"""
The analysis of the code, done in another process while this one goes on with the rest of the APK.

Python runs one thread of code at a time per process, so the only way to use a second core is a second process.
It is started with "spawn", the same way on every system: forking a program that has a window and threads can
leave the child with a lock that nobody will ever release. If the child cannot be started, dies, or does not
answer, the analysis is done here, in this process, with the same result.
"""

import os
from concurrent.futures import ProcessPoolExecutor, Future

import gc
import multiprocessing
import threading
import time
from collections.abc import Sequence
from multiprocessing.connection import Connection
from typing import Any

from apkdetective.domain.entities.analysis.analysis_warning import AnalysisWarning
from apkdetective.domain.entities.analysis.cancellation_token import CancellationToken
from apkdetective.infrastructure.androguard.dex.dex_analysis import DexAnalysis
from apkdetective.infrastructure.androguard.dex.dex_analysis_job import DexAnalysisJob
from apkdetective.domain.entities.analysis.sections.dex_metrics import DexMetrics
from apkdetective.infrastructure.androguard.dex.dex_analyzer import DexAnalyzer
from apkdetective.domain.entities.analysis.sections.embedded_content import EmbeddedContent

_READY = "ready"
_DONE = "done"
_FAILED = "failed"


def run_in_child(incoming: Connection, outgoing: Connection) -> None:
    """What the child process runs: it takes the DEX files, analyzes them and sends the result back."""
    gc.disable()  # it lives for a few seconds and its objects are not cycles
    try:
        outgoing.send((_READY, None))
        dex_files = incoming.recv()
        outgoing.send((_DONE, DexAnalyzer().analyze(dex_files)))
    except BaseException as exc:  # pylint: disable=broad-except
        try:
            outgoing.send((_FAILED, f"{type(exc).__name__}: {exc}"))
        except (OSError, ValueError):
            pass
    finally:
        outgoing.close()


class ChildProcessDexAnalysisJob(DexAnalysisJob):
    POLL_SECONDS: float = 0.1
    STARTUP_TIMEOUT_SECONDS: float = 30.0  # a child that has not even said it is ready by then is not coming

    def __init__(self, dex_files: Sequence[bytes], in_process: DexAnalysisJob) -> None:
        self._in_process: DexAnalysisJob = in_process
        context = multiprocessing.get_context("spawn")
        child_incoming, self._to_child = context.Pipe(duplex=False)
        self._from_child, child_outgoing = context.Pipe(duplex=False)
        self._process = context.Process(target=run_in_child, args=(child_incoming, child_outgoing), daemon=True)
        self._started_at = time.monotonic()
        self._ready = False
        self._process.start()
        child_incoming.close()
        child_outgoing.close()
        # Sent from a thread: the child takes a moment to start, and the DEX files are tens of megabytes.
        threading.Thread(target=self._send, args=(dex_files,), daemon=True).start()

    def result(self, cancellation: CancellationToken) -> DexAnalysis:
        try:
            message = self._wait_for_answer(cancellation)
        finally:
            self.discard()  # whatever the answer, the child is not needed any more
        if message is not None and message[0] == _DONE:
            return message[1]
        return self._in_process.result(cancellation)

    def discard(self) -> None:
        if self._process.is_alive():
            self._process.terminate()
        self._process.join(timeout=2)
        self._from_child.close()
        self._to_child.close()

    def _send(self, dex_files: Sequence[bytes]) -> None:
        try:
            self._to_child.send(dex_files)
        except (OSError, ValueError):  # the child died or was discarded: result() will notice
            pass

    def _wait_for_answer(self, cancellation: CancellationToken) -> tuple[str, Any] | None:
        """The final message of the child, or None if it can't be had (then the analysis is done here)."""
        while True:
            cancellation.raise_if_cancelled()
            if not self._ready and time.monotonic() - self._started_at > self.STARTUP_TIMEOUT_SECONDS:
                return None
            try:
                if not self._from_child.poll(self.POLL_SECONDS):
                    continue
                message = self._from_child.recv()
            except (EOFError, OSError, ValueError):  # the child is gone
                return None
            if message[0] == _READY:
                self._ready = True
            else:
                return message



def _analyze_single_dex(dex_bytes: bytes) -> DexAnalysis:
    """Worker function: Runs in a separate process for a single DEX file."""
    gc.disable()
    analyzer = DexAnalyzer()
    return analyzer.analyze([dex_bytes])


class ParallelDexAnalysisJob(DexAnalysisJob):
    def __init__(self, dex_files: Sequence[bytes], in_process: DexAnalysisJob) -> None:
        self._in_process: DexAnalysisJob = in_process
        self._executor: ProcessPoolExecutor = ProcessPoolExecutor(
            max_workers=os.cpu_count() or 4,
            mp_context=multiprocessing.get_context("spawn")
        )
        # Submit each DEX file as a separate independent task to the pool
        self._futures: list[Future] = [
            self._executor.submit(_analyze_single_dex, dex)
            for dex in dex_files
        ]

    def result(self, cancellation: CancellationToken) -> DexAnalysis:
        try:
            results: list[DexAnalysis] = []
            for future in self._futures:
                cancellation.raise_if_cancelled()
                # Blocks until this specific file is analyzed
                results.append(future.result())
            return self._aggregate(results)
        except Exception:
            # Fallback to single-process analysis if the pool fails or crashes
            return self._in_process.result(cancellation)
        finally:
            self.discard()

    def discard(self) -> None:
        for future in self._futures:
            future.cancel()
        self._executor.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _aggregate(analyses: list[DexAnalysis]) -> DexAnalysis:
        """Combines the individual analysis of each DEX file into the final result."""
        if not analyses:
            return DexAnalysis.empty()

        all_class_names: list[str] = []
        all_urls: list[str] = []
        all_warnings: list[AnalysisWarning] = []
        for a in analyses:
            all_class_names.extend(a.class_names)
            all_urls.extend(a.embedded_content.urls)
            all_warnings.extend(a.warnings)

        max_comp_analysis = max(analyses, key=lambda a: a.metrics.max_complexity, default=analyses[0])
        longest_analysis = max(analyses, key=lambda a: a.metrics.max_instructions, default=analyses[0])

        total_metrics = DexMetrics(
            dex_files=sum(a.metrics.dex_files for a in analyses),
            dex_size=sum(a.metrics.dex_size for a in analyses),
            packages=len({name.rpartition("/")[0] for name in all_class_names}),
            classes=sum(a.metrics.classes for a in analyses),
            methods=sum(a.metrics.methods for a in analyses),
            methods_with_code=sum(a.metrics.methods_with_code for a in analyses),
            native_methods=sum(a.metrics.native_methods for a in analyses),
            method_references=sum(a.metrics.method_references for a in analyses),
            fields=sum(a.metrics.fields for a in analyses),
            strings=sum(a.metrics.strings for a in analyses),
            string_characters=sum(a.metrics.string_characters for a in analyses),
            instructions=sum(a.metrics.instructions for a in analyses),
            code_size=sum(a.metrics.code_size for a in analyses),
            cyclomatic_complexity=sum(a.metrics.cyclomatic_complexity for a in analyses),
            max_complexity=max_comp_analysis.metrics.max_complexity,
            most_complex_method=max_comp_analysis.metrics.most_complex_method,
            max_instructions=longest_analysis.metrics.max_instructions,
            longest_method=longest_analysis.metrics.longest_method,
        )

        return DexAnalysis(
            metrics=total_metrics,
            embedded_content=EmbeddedContent(urls=tuple(sorted(set(all_urls)))),
            class_names=tuple(all_class_names),
            warnings=tuple(all_warnings)
        )
