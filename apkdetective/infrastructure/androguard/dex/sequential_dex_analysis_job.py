"""
The analysis of the code, done in this process when the result is asked for.
"""

from collections.abc import Sequence

from apkdetective.domain.entities.analysis.cancellation_token import CancellationToken
from apkdetective.domain.entities.analysis.sections.dex_analysis import DexAnalysis
from apkdetective.infrastructure.androguard.dex.dex_analysis_job import DexAnalysisJob
from apkdetective.infrastructure.androguard.dex.dex_analyzer import DexAnalyzer


class SequentialDexAnalysisJob(DexAnalysisJob):
    def __init__(self, dex_files: Sequence[bytes], analyzer: DexAnalyzer) -> None:
        self._dex_files: Sequence[bytes] = dex_files
        self._analyzer: DexAnalyzer = analyzer

    def result(self, cancellation: CancellationToken) -> DexAnalysis:
        return self._analyzer.analyze(self._dex_files, cancellation)

    def discard(self) -> None:
        """Nothing runs before the result is asked for."""
