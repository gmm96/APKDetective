"""
Something the analysis could not read, so that "nothing found" can be told
apart from "could not look".
"""

from dataclasses import dataclass

from apkdetective.domain.entities.analysis.analysis_section_enum import AnalysisSectionEnum


@dataclass(frozen=True)
class AnalysisWarning:
    section: AnalysisSectionEnum
    message: str
