"""
Collects the warnings raised by the extractors while one APK is analyzed.
"""

from collections.abc import Callable
from typing import TypeVar

from apkdetective.domain.entities.analysis.analysis_cancelled_error import AnalysisCancelledError
from apkdetective.domain.entities.analysis.analysis_section_enum import AnalysisSectionEnum
from apkdetective.domain.entities.analysis.analysis_warning import AnalysisWarning

T = TypeVar("T")


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

    def extend(self, warnings: tuple[AnalysisWarning, ...]) -> None:
        for warning in warnings:
            if warning not in self._warnings:
                self._warnings.append(warning)

    def attempt(self, what: str, sections: tuple[AnalysisSectionEnum, ...], read: Callable[[], T], default: T) -> T:
        """
        Runs one step of the analysis. If it fails, the rest of the analysis can go on: the failure is
        recorded as a warning for the sections that depended on it and `default` takes the place of its result.
        """
        try:
            return read()
        except AnalysisCancelledError:  # not a failure of this step: the whole analysis must stop
            raise
        except Exception as exc:  # pylint: disable=broad-except
            self.add(f"{what} could not be read ({type(exc).__name__}: {exc}).", *sections)
            return default
