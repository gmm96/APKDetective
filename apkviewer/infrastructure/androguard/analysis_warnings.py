"""
Collects the warnings raised by the extractors while one APK is analyzed.
"""

from apkviewer.domain.entities.analysis.analysis_section_enum import AnalysisSectionEnum
from apkviewer.domain.entities.analysis.analysis_warning import AnalysisWarning


class AnalysisWarningCollector:
    def __init__(self) -> None:
        self._warnings: list[AnalysisWarning] = []

    def add(self, message: str, *sections: AnalysisSectionEnum) -> None:
        """Record that `message` concerns each of those sections of the analysis."""
        for section in sections:
            warning = AnalysisWarning(section, message)
            if warning not in self._warnings:
                self._warnings.append(warning)

    def as_tuple(self) -> tuple[AnalysisWarning, ...]:
        return tuple(self._warnings)
