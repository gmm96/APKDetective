"""
Turns the DEX metrics into the (label, value) pairs the app shows and exports, so the
Info tab and the text report always say the same thing.
"""

from apkviewer.domain.entities.analysis.sections.dex_metrics import DexMetrics
from apkviewer.ports.formatting.size_formatter_port import SizeFormatterPort


class DexMetricsFormatter:
    _NONE: str = "—"

    def __init__(self, size_formatter: SizeFormatterPort | None = None) -> None:
        self._size_formatter: SizeFormatterPort | None = size_formatter

    def fields(self, metrics: DexMetrics) -> list[tuple[str, str]]:
        return [
            ("DEX Files", self._number(metrics.dex_files)),
            ("DEX Size", self._size(metrics.dex_size)),
            ("Packages", self._number(metrics.packages)),
            ("Classes", self._number(metrics.classes)),
            ("Methods", self._number(metrics.methods)),
            ("Method References", self._number(metrics.method_references)),
            ("Native Methods", self._number(metrics.native_methods)),
            ("Fields", self._number(metrics.fields)),
            ("Strings", self._number(metrics.strings)),
            ("String Characters", self._number(metrics.string_characters)),
            ("Instructions", self._number(metrics.instructions)),
            ("Bytecode Size", self._size(metrics.code_size)),
            ("Cyclomatic Complexity", self._number(metrics.cyclomatic_complexity)),
            ("Average Complexity", f"{metrics.average_complexity:.2f}"),
            ("Most Complex Method", self._method(metrics.most_complex_method, f"complexity {metrics.max_complexity:,}")),
            ("Longest Method", self._method(metrics.longest_method, f"{metrics.max_instructions:,} instructions")),
        ]

    @staticmethod
    def _number(value: int) -> str:
        return f"{value:,}"

    def _size(self, size: int) -> str:
        return self._size_formatter.format(size, True) if self._size_formatter else f"{size:,} B"

    def _method(self, name: str | None, detail: str) -> str:
        return f"{name} ({detail})" if name else self._NONE
