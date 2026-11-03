"""
The analysis of the code of an APK: it reads the strings and the classes of its DEX files, counts what they
contain and looks for URLs. It needs nothing but the bytes of those files, which is why it can run in another
process while the rest of the APK (all of it behind the resource table) is analyzed in this one.
"""

from collections.abc import Sequence

from apkdetective.domain.entities.analysis.analysis_section_enum import AnalysisSectionEnum
from apkdetective.domain.entities.analysis.cancellation_token import CancellationToken
from apkdetective.domain.entities.analysis.sections.dex_metrics import DexMetrics
from apkdetective.domain.entities.analysis.sections.embedded_content import EmbeddedContent
from apkdetective.infrastructure.androguard.analysis_warnings import AnalysisWarningCollector
from apkdetective.infrastructure.androguard.dex.dex_analysis import DexAnalysis
from apkdetective.infrastructure.androguard.dex.dex_contents import DexContents
from apkdetective.infrastructure.androguard.dex.dex_reader import DexReader
from apkdetective.infrastructure.androguard.extractors.dex_metrics_extractor import DexMetricsExtractor
from apkdetective.infrastructure.androguard.extractors.embedded_content_extractor import EmbeddedContentExtractor


class DexAnalyzer:
    def __init__(
        self,
        reader: DexReader | None = None,
        metrics_extractor: DexMetricsExtractor | None = None,
        embedded_content_extractor: EmbeddedContentExtractor | None = None,
    ) -> None:
        self._reader = reader or DexReader()
        self._metrics = metrics_extractor or DexMetricsExtractor()
        self._embedded_content = embedded_content_extractor or EmbeddedContentExtractor()

    def analyze(self, dex_files: Sequence[bytes], cancellation: CancellationToken | None = None) -> DexAnalysis:
        """Each part guarded as in the rest of the analysis: one that fails leaves a warning, not a hole."""
        warnings = AnalysisWarningCollector()
        section = AnalysisSectionEnum
        contents = warnings.attempt(
            "The code (DEX) of the app",
            (section.EMBEDDED_CONTENT, section.THIRD_PARTY),
            lambda: self._reader.read(dex_files, warnings, cancellation),
            DexContents(),
        )
        metrics = warnings.attempt(
            "The DEX metrics",
            (section.DEX_METRICS,),
            lambda: self._metrics.extract(dex_files, contents, warnings, cancellation),
            DexMetrics(),
        )
        embedded_content = warnings.attempt(
            "The embedded content",
            (section.EMBEDDED_CONTENT,),
            lambda: self._embedded_content.extract(contents),
            EmbeddedContent(()),
        )
        return DexAnalysis(metrics, embedded_content, contents.class_names, warnings.as_tuple())
