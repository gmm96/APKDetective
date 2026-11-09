"""
The analysis of the code, with every DEX file analyzed in a process of its own, while this process goes on with the
rest of the APK.

Analyzing a DEX file (its code, its strings, its classes) is what takes longest in the analysis, and the files do not
depend on each other: with a process per file (as many at a time as there are cores) they all take what the biggest
one takes, while this process is busy with the rest of the APK. Only adding the results up is left for this process.

Python runs one thread of code at a time per process, so the only way to use more cores is more processes. They are
started with "spawn", the same way on every system: forking a program that has a window and threads can leave the
child with a lock that nobody will ever release. If the processes cannot be started, one dies, or they stop
answering, the analysis is done here, in this process, with the same result.
"""

import gc
import multiprocessing
import os
import time
from collections.abc import Sequence

from apkdetective.domain.entities.analysis.cancellation_token import CancellationToken
from apkdetective.domain.entities.analysis.sections.dex_analysis import DexAnalysis
from apkdetective.infrastructure.androguard.dex.dex_analysis_job import DexAnalysisJob
from apkdetective.infrastructure.androguard.dex.dex_analyzer import DexAnalyzer
from apkdetective.domain.entities.analysis.sections.dex_file_analysis import DexFileAnalysis
from apkdetective.infrastructure.androguard.dex.dex_file_analyzer import DexFileAnalyzer


class ParallelDexAnalysisJob(DexAnalysisJob):
    POLL_SECONDS: float = 0.1
    STALL_TIMEOUT_SECONDS: float = 60.0  # no file analyzed for this long: the workers are not coming (one takes seconds)

    def __init__(self, dex_files: Sequence[bytes], analyzer: DexAnalyzer, in_process: DexAnalysisJob) -> None:
        self._dex_files: Sequence[bytes] = dex_files
        self._analyzer: DexAnalyzer = analyzer
        self._in_process: DexAnalysisJob = in_process
        context = multiprocessing.get_context("spawn")
        self._pool = context.Pool(processes=min(len(dex_files), os.cpu_count() or 1), initializer=self._prepare_worker)
        self._analyses = [
            self._pool.apply_async(self._analyze_in_worker, (number, data))
            for number, data in enumerate(dex_files, start=1)
        ]

    def result(self, cancellation: CancellationToken) -> DexAnalysis:
        try:
            analyses = self._wait_for_analyses(cancellation)
        finally:
            self.discard()  # the workers are not needed any more, whatever happened
        if analyses is None:
            return self._in_process.result(cancellation)
        return self._analyzer.analyze(self._dex_files, cancellation, file_analyses=analyses)

    def discard(self) -> None:
        try:
            self._pool.terminate()
            self._pool.join()
        except ValueError:  # already discarded
            pass

    def _wait_for_analyses(self, cancellation: CancellationToken) -> list[DexFileAnalysis] | None:
        """The analysis of every file, in the order of the files, or None if they can't be had (then it is done here)."""
        finished = 0
        last_progress = time.monotonic()
        while finished < len(self._analyses):
            cancellation.raise_if_cancelled()
            now = time.monotonic()
            done = sum(analysis.ready() for analysis in self._analyses)
            if done != finished:
                finished, last_progress = done, now
            elif now - last_progress > self.STALL_TIMEOUT_SECONDS:
                return None
            if finished < len(self._analyses):
                time.sleep(self.POLL_SECONDS)
        try:
            return [analysis.get() for analysis in self._analyses]
        except Exception:  # pylint: disable=broad-except
            return None  # a worker raised: the same analysis, here, says what is wrong with the file

    @staticmethod
    def _prepare_worker() -> None:
        gc.disable()  # a worker lives for a few seconds and its objects are not cycles

    @staticmethod
    def _analyze_in_worker(number: int, data: bytes) -> DexFileAnalysis:
        """What a worker process runs: the analysis of one DEX file."""
        return DexFileAnalyzer().analyze(number, data)
