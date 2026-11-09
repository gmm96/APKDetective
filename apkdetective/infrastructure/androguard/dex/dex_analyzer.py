"""
The analysis of the code of an APK: the analysis of each of its DEX files, added up. The files do not depend on each
other, so each one can be analyzed in another process while the rest of the APK is analyzed in this one: what is left
for this process is adding the results up.
"""

from collections.abc import Sequence
from functools import partial

from apkdetective.domain.entities.analysis.analysis_section_enum import AnalysisSectionEnum
from apkdetective.domain.entities.analysis.cancellation_token import CancellationToken
from apkdetective.domain.entities.analysis.sections.dex_analysis import DexAnalysis
from apkdetective.domain.entities.analysis.sections.dex_file_analysis import DexFileAnalysis
from apkdetective.domain.entities.analysis.sections.dex_file_contents import DexFileContents
from apkdetective.domain.entities.analysis.sections.dex_file_scan import DexFileScan
from apkdetective.domain.entities.analysis.sections.dex_metrics import DexMetrics
from apkdetective.domain.entities.analysis.sections.embedded_content import EmbeddedContent
from apkdetective.infrastructure.androguard.analysis_warnings import AnalysisWarningCollector
from apkdetective.infrastructure.androguard.dex.dex_file_analyzer import DexFileAnalyzer
from apkdetective.infrastructure.androguard.dex.dex_reader import DexReader
from apkdetective.infrastructure.androguard.extractors.dex_metrics_extractor import DexMetricsExtractor
from apkdetective.infrastructure.androguard.extractors.embedded_content_extractor import EmbeddedContentExtractor


class DexAnalyzer:
    def __init__(
        self,
        reader: DexReader | None = None,
        metrics_extractor: DexMetricsExtractor | None = None,
        embedded_content_extractor: EmbeddedContentExtractor | None = None,
        file_analyzer: DexFileAnalyzer | None = None,
    ) -> None:
        self._metrics = metrics_extractor or DexMetricsExtractor()
        self._embedded_content = embedded_content_extractor or EmbeddedContentExtractor()
        self._file_analyzer = file_analyzer or DexFileAnalyzer(reader, self._metrics, self._embedded_content)

    def analyze(
        self,
        dex_files: Sequence[bytes],
        cancellation: CancellationToken | None = None,
        file_analyses: Sequence[DexFileAnalysis] | None = None,
    ) -> DexAnalysis:
        """
        Each part guarded as in the rest of the analysis: one that fails leaves a warning, not a hole.
        `file_analyses`: the analysis of every DEX file, if it was already done (in other processes, one per file).
        """
        warnings = AnalysisWarningCollector()
        section = AnalysisSectionEnum
        analyses = file_analyses if file_analyses is not None else self._analyze_files(dex_files, cancellation, warnings)
        class_names = tuple(name for analysis in analyses for name in analysis.contents.class_names)
        for analysis in analyses:
            if analysis.contents.problem:
                warnings.add(
                    f"DEX file #{analysis.contents.number} {analysis.contents.problem}: "
                    "embedded URLs and trackers may be incomplete.",
                    section.EMBEDDED_CONTENT, section.THIRD_PARTY,
                )
        metrics = warnings.attempt(
            "The DEX metrics",
            (section.DEX_METRICS,),
            lambda: self._metrics.combine(
                [analysis.scan for analysis in analyses],
                dex_files,
                class_names,
                sum(analysis.contents.string_characters for analysis in analyses),
                warnings,
            ),
            DexMetrics(),
        )
        embedded_content = warnings.attempt(
            "The embedded content",
            (section.EMBEDDED_CONTENT,),
            lambda: self._embedded_content.combine(analysis.contents.urls for analysis in analyses),
            EmbeddedContent(()),
        )
        return DexAnalysis(metrics, embedded_content, class_names, warnings.as_tuple())

    def _analyze_files(
        self,
        dex_files: Sequence[bytes],
        cancellation: CancellationToken | None,
        warnings: AnalysisWarningCollector,
    ) -> list[DexFileAnalysis]:
        """The analysis of each file, here, one after the other; a file that fails leaves a warning and no data."""
        section = AnalysisSectionEnum
        analyses: list[DexFileAnalysis] = []
        for number, data in enumerate(dex_files, start=1):
            if cancellation is not None:
                cancellation.raise_if_cancelled()
            analyses.append(warnings.attempt(
                f"DEX file #{number}",
                (section.EMBEDDED_CONTENT, section.THIRD_PARTY, section.DEX_METRICS),
                partial(self._file_analyzer.analyze, number, data, cancellation),
                DexFileAnalysis(DexFileScan(number), DexFileContents(number)),
            ))
        return analyses
