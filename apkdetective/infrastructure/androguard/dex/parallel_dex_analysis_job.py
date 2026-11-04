"""
The analysis of the code, done in another process while this one goes on with the rest of the APK.

ProcessPoolExecutor is used to manage a pool of workers efficiently.
This infrastructure adapter is agnostic of how DexAnalysis metrics are combined.
"""

import gc
import multiprocessing
import os
from collections.abc import Sequence
from concurrent.futures import Future, ProcessPoolExecutor

from apkdetective.domain.entities.analysis.cancellation_token import CancellationToken
from apkdetective.infrastructure.androguard.dex.dex_analysis import DexAnalysis
from apkdetective.infrastructure.androguard.dex.dex_analysis_job import DexAnalysisJob
from apkdetective.infrastructure.androguard.dex.dex_analyzer import DexAnalyzer


class ParallelDexAnalysisJob(DexAnalysisJob):
    """
    Infrastructure adapter responsible ONLY for parallel execution orchestration.
    """
    def __init__(self, dex_files: Sequence[bytes], in_process: DexAnalysisJob) -> None:
        self._in_process: DexAnalysisJob = in_process
        self._executor: ProcessPoolExecutor = ProcessPoolExecutor(
            max_workers=os.cpu_count() or 4,
            mp_context=multiprocessing.get_context("spawn")
        )
        self._futures: list[Future] = [
            self._executor.submit(self._analyze_single_dex, dex)
            for dex in dex_files
        ]

    def result(self, cancellation: CancellationToken) -> DexAnalysis:
        try:
            results: list[DexAnalysis] = []
            for future in self._futures:
                cancellation.raise_if_cancelled()
                results.append(future.result())
            return DexAnalysis.aggregate(results)
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
    def _analyze_single_dex(dex_bytes: bytes) -> DexAnalysis:
        """
        Worker function: Runs in a separate process for a single DEX file.
        """
        gc.disable()
        analyzer = DexAnalyzer()
        return analyzer.analyze([dex_bytes])
