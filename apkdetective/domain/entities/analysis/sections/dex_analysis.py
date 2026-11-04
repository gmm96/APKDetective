"""
What the analysis of the code of an APK finds: everything that comes from its DEX files, and nothing else.
"""

from dataclasses import dataclass

from apkdetective.domain.entities.analysis.analysis_warning import AnalysisWarning
from apkdetective.domain.entities.analysis.sections.dex_metrics import DexMetrics
from apkdetective.domain.entities.analysis.sections.embedded_content import EmbeddedContent


@dataclass(frozen=True)
class DexAnalysis:
    metrics: DexMetrics
    embedded_content: EmbeddedContent
    class_names: tuple[str, ...]  # what the detection of trackers looks at
    warnings: tuple[AnalysisWarning, ...]

    @staticmethod
    def empty() -> "DexAnalysis":
        return DexAnalysis(DexMetrics(), EmbeddedContent(()), (), ())
