"""
"Code" tab: what the APK says about the code it ships: the third-party libraries and trackers bundled in it, a size
report of its compiled code (the DEX files) and the content embedded in that code.
"""

import ttkbootstrap as ttkb

from apkdetective.application.analysis.dex_metrics_formatter import DexMetricsFormatter
from apkdetective.domain.entities.analysis.sections.dex_metrics import DexMetrics
from apkdetective.domain.entities.analysis.sections.embedded_content import EmbeddedContent
from apkdetective.domain.entities.analysis.sections.third_party_info import ThirdPartyInfo
from apkdetective.ports.formatting.size_formatter_port import SizeFormatterPort
from apkdetective.presentation.common.forms.form_panel import FormPanel
from apkdetective.presentation.common.forms.form_section import FormSection
from apkdetective.presentation.common.forms.text_line_marker import TextLineMarker
from apkdetective.presentation.common.menus.text_context_menu import TextContextMenu
from apkdetective.presentation.formatting.human_readable_size_formatter import HumanReadableSizeFormatter
from apkdetective.presentation.viewmodels.appearance.theme_palette import ThemePalette


class CodePanel(FormPanel):
    def __init__(
        self,
        parent: ttkb.Notebook,
        context_menu: TextContextMenu,
        palette: ThemePalette,
        line_marker: TextLineMarker | None = None,
        size_formatter: SizeFormatterPort | None = None,
    ) -> None:
        super().__init__(parent, context_menu, palette, line_marker)
        self._dex_metrics_formatter: DexMetricsFormatter = DexMetricsFormatter(
            size_formatter or HumanReadableSizeFormatter()
        )

    def render(
        self,
        third_party: ThirdPartyInfo,
        dex_metrics: DexMetrics,
        embedded_content: EmbeddedContent,
    ) -> None:
        self.clear()
        section: FormSection = self.add_section("DEX Metrics", responsive=True, max_columns=2)
        for label, value in self._dex_metrics_formatter.fields(dex_metrics):
            section.add_entry(label, value)

        section = self.add_section("Third-party Code")
        section.add_list("Libraries", third_party.libraries)
        section.add_list("Trackers", third_party.trackers)

        section = self.add_section("Embedded Content")
        section.add_list("Discovered URLs", embedded_content.urls)
