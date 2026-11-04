"""
Starts the analysis of the code, with a process for each DEX file if that is going to be faster.
"""

import os
from collections.abc import Sequence

from apkdetective.infrastructure.androguard.dex.dex_analysis_job import DexAnalysisJob
from apkdetective.infrastructure.androguard.dex.dex_analyzer import DexAnalyzer
from apkdetective.infrastructure.androguard.dex.sequential_dex_analysis_job import SequentialDexAnalysisJob
from apkdetective.infrastructure.androguard.dex.parallel_dex_analysis_job import ParallelDexAnalysisJob


class DexAnalysisStarter:
    MIN_CPUS: int = 2  # with a single core a second process only adds work

    def __init__(self, analyzer: DexAnalyzer | None = None, parallel: bool = True) -> None:
        self._analyzer: DexAnalyzer = analyzer or DexAnalyzer()
        self._parallel: bool = parallel

    def start(self, dex_files: Sequence[bytes]) -> DexAnalysisJob:
        sequential_job: DexAnalysisJob = SequentialDexAnalysisJob(dex_files, self._analyzer)
        if not dex_files or not self._parallel or (os.cpu_count() or 1) < self.MIN_CPUS:
            return sequential_job
        try:
            return ParallelDexAnalysisJob(dex_files, self._analyzer, sequential_job)
        except (OSError, ValueError, RuntimeError):  # the processes could not be started
            return sequential_job
