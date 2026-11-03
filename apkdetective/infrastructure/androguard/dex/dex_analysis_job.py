"""
An analysis of the code that has been started and whose result is asked for later.
"""

from abc import ABC, abstractmethod

from apkdetective.domain.entities.analysis.cancellation_token import CancellationToken
from apkdetective.infrastructure.androguard.dex.dex_analysis import DexAnalysis


class DexAnalysisJob(ABC):
    @abstractmethod
    def result(self, cancellation: CancellationToken) -> DexAnalysis:
        """Waits for the analysis. Raises AnalysisCancelledError as soon as `cancellation` is cancelled."""
        raise NotImplementedError

    @abstractmethod
    def discard(self) -> None:
        """The result is not wanted (any more): whatever is still running for it stops."""
        raise NotImplementedError
