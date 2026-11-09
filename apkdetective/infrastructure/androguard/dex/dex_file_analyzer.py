"""
Everything the analysis takes from one DEX file: its metrics, its class names, the length of its strings and the URLs
written in them. It needs nothing but the bytes of the file, which is why it can run in another process (one per file)
while the rest of the APK, all of it behind the resource table, is analyzed in this one.
"""

from apkdetective.domain.entities.analysis.cancellation_token import CancellationToken
from apkdetective.domain.entities.analysis.sections.dex_file_analysis import DexFileAnalysis
from apkdetective.domain.entities.analysis.sections.dex_file_contents import DexFileContents
from apkdetective.infrastructure.androguard.dex.dex_reader import DexReader
from apkdetective.infrastructure.androguard.extractors.dex_metrics_extractor import DexMetricsExtractor
from apkdetective.infrastructure.androguard.extractors.embedded_content_extractor import EmbeddedContentExtractor


class DexFileAnalyzer:
    def __init__(
        self,
        reader: DexReader | None = None,
        metrics_extractor: DexMetricsExtractor | None = None,
        embedded_content_extractor: EmbeddedContentExtractor | None = None,
    ) -> None:
        self._reader = reader or DexReader()
        self._metrics = metrics_extractor or DexMetricsExtractor()
        self._embedded_content = embedded_content_extractor or EmbeddedContentExtractor()

    def analyze(self, number: int, data: bytes, cancellation: CancellationToken | None = None) -> DexFileAnalysis:
        """`number`: the position of the file among the DEX files of the APK, from 1."""
        scan = self._metrics.scan_file(number, data, cancellation)
        strings, class_names, problem = self._reader.read(data)
        contents = DexFileContents(
            number,
            class_names=tuple(class_names),
            string_characters=sum(map(len, strings)),
            urls=self._embedded_content.find_urls(strings),
            problem=problem,
        )
        return DexFileAnalysis(scan, contents)
