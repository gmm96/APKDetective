"""
What the analysis of the code of an APK finds: everything that comes from its DEX files, and nothing else.
"""

from dataclasses import dataclass
from typing import Iterable

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

    @classmethod
    def aggregate(cls, analyses: Iterable["DexAnalysis"]) -> "DexAnalysis":
        """
        Combines multiple DexAnalysis entities into a single one.
        This is pure domain logic, entirely decoupled from how the analyses were executed.
        """
        analyses_list = list(analyses)
        if not analyses_list:
            return cls.empty()

        all_class_names: list[str] = []
        all_urls: list[str] = []
        all_warnings: list[AnalysisWarning] = []

        for analysis in analyses_list:
            all_class_names.extend(analysis.class_names)
            all_urls.extend(analysis.embedded_content.urls)
            all_warnings.extend(analysis.warnings)

        max_comp_analysis = max(analyses_list, key=lambda a: a.metrics.max_complexity, default=analyses_list[0])
        longest_analysis = max(analyses_list, key=lambda a: a.metrics.max_instructions, default=analyses_list[0])

        total_metrics = DexMetrics(
            dex_files=sum(a.metrics.dex_files for a in analyses_list),
            dex_size=sum(a.metrics.dex_size for a in analyses_list),
            packages=len({name.rpartition("/")[0] for name in all_class_names}),
            classes=sum(a.metrics.classes for a in analyses_list),
            methods=sum(a.metrics.methods for a in analyses_list),
            methods_with_code=sum(a.metrics.methods_with_code for a in analyses_list),
            native_methods=sum(a.metrics.native_methods for a in analyses_list),
            method_references=sum(a.metrics.method_references for a in analyses_list),
            fields=sum(a.metrics.fields for a in analyses_list),
            strings=sum(a.metrics.strings for a in analyses_list),
            string_characters=sum(a.metrics.string_characters for a in analyses_list),
            instructions=sum(a.metrics.instructions for a in analyses_list),
            code_size=sum(a.metrics.code_size for a in analyses_list),
            cyclomatic_complexity=sum(a.metrics.cyclomatic_complexity for a in analyses_list),
            max_complexity=max_comp_analysis.metrics.max_complexity,
            most_complex_method=max_comp_analysis.metrics.most_complex_method,
            max_instructions=longest_analysis.metrics.max_instructions,
            longest_method=longest_analysis.metrics.longest_method,
        )

        return cls(
            metrics=total_metrics,
            embedded_content=EmbeddedContent(urls=tuple(sorted(set(all_urls)))),
            class_names=tuple(all_class_names),
            warnings=tuple(all_warnings)
        )
