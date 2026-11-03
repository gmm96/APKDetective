"""
Starts the analysis of the code, in another process if that is going to be faster.
"""

import os
from collections.abc import Sequence

from apkdetective.infrastructure.androguard.dex.parallel_dex_analysis_job import ParallelDexAnalysisJob
from apkdetective.infrastructure.androguard.dex.dex_analysis_job import DexAnalysisJob
from apkdetective.infrastructure.androguard.dex.dex_analyzer import DexAnalyzer
from apkdetective.infrastructure.androguard.dex.sequential_dex_analysis_job import SequentialDexAnalysisJob


class DexAnalysisStarter:
    MIN_CPUS: int = 2  # with a single core a second process only adds work

    def __init__(self, analyzer: DexAnalyzer | None = None, use_child_process: bool = True) -> None:
        self._analyzer: DexAnalyzer = analyzer or DexAnalyzer()
        self._use_child_process: bool = use_child_process

    def start(self, dex_files: Sequence[bytes]) -> DexAnalysisJob:
        in_process = SequentialDexAnalysisJob(dex_files, self._analyzer)
        if not dex_files or not self._use_child_process or (os.cpu_count() or 1) < self.MIN_CPUS:
            return in_process
        try:
            return ParallelDexAnalysisJob(dex_files, in_process)
        except (OSError, ValueError, RuntimeError):  # the child could not be started
            return in_process
