"""
"Info" tab: app identity, versions, SDK range, configuration and the
content embedded in the code.
"""

import ttkbootstrap as ttkb

from apkviewer.application.analysis.dex_metrics_formatter import DexMetricsFormatter
from apkviewer.domain.entities.analysis.sections.application_info import ApplicationInfo
from apkviewer.domain.entities.analysis.sections.configuration_info import ConfigurationInfo
from apkviewer.domain.entities.analysis.sections.dex_metrics import DexMetrics
from apkviewer.domain.entities.analysis.sections.embedded_content import EmbeddedContent
from apkviewer.ports.formatting.date_formatter_port import DateFormatterPort
from apkviewer.ports.formatting.size_formatter_port import SizeFormatterPort
from apkviewer.presentation.viewmodels.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.forms.form_panel import FormPanel
from apkviewer.presentation.common.menus.text_context_menu import TextContextMenu
from apkviewer.presentation.common.forms.text_line_marker import TextLineMarker
from apkviewer.presentation.formatting.english_long_date_formatter import EnglishLongDateFormatter
from apkviewer.presentation.formatting.human_readable_size_formatter import HumanReadableSizeFormatter


class InfoPanel(FormPanel):
    def __init__(
        self,
        parent: ttkb.Notebook,
        context_menu: TextContextMenu,
        palette: ThemePalette,
        line_marker: TextLineMarker | None = None,
        size_formatter: SizeFormatterPort | None = None,
        date_formatter: DateFormatterPort | None = None,
    ) -> None:
        super().__init__(parent, context_menu, palette, line_marker)
        self._size_formatter: SizeFormatterPort = size_formatter or HumanReadableSizeFormatter()
        self._date_formatter: DateFormatterPort = date_formatter or EnglishLongDateFormatter()
        self._dex_metrics_formatter: DexMetricsFormatter = DexMetricsFormatter(self._size_formatter)

    def render(
        self,
        application: ApplicationInfo,
        configuration: ConfigurationInfo,
        embedded_content: EmbeddedContent,
        dex_metrics: DexMetrics,
    ) -> None:
        self.clear()
        app_section = self.add_section("Application", responsive=True, max_columns=2)
        app_section.add_entry("App Name", application.app_name)
        app_section.add_entry("Package Name", application.package_name)
        app_section.add_entry("Version Name", application.version_name)
        app_section.add_entry("Version Code", application.version_code)
        app_section.add_entry("Min SDK", application.min_sdk)
        app_section.add_entry("Target SDK", application.target_sdk)
        if application.max_sdk:
            app_section.add_entry("Max SDK", application.max_sdk)

        file_section = self.add_section("File", responsive=True, max_columns=2)
        file_section.add_entry("File Name", application.file_name or "Unknown")
        file_section.add_entry("File Path", application.file_path or "Unknown")
        file_section.add_entry("File Size", self._format_size(application.file_size))
        file_section.add_entry("Last Modified", self._format_date(application))

        flags_section = self.add_section("Flags", responsive=True, max_columns=2)
        flags_section.add_entry("Debuggable", application.debuggable)
        flags_section.add_entry("Allow Backup", application.allow_backup)
        flags_section.add_entry("Test Only", application.test_only)
        flags_section.add_entry("Hardware Accelerated", application.hardware_accelerated)
        flags_section.add_entry("Extract Native Libs", application.extract_native_libs)
        flags_section.add_entry("Cleartext Traffic Permitted", application.cleartext_traffic_permitted)
        flags_section.add_entry("Trusts User Certificates", application.trust_user_certificates)
        flags_section.add_entry("Certificate Pinning Enforced", application.certificate_pinning_enforced)

        section = self.add_section("Configuration")
        section.add_list("Architectures", configuration.architectures or ("None / Unknown (Java only)",))
        section.add_list("Hardware Requirements", [feature.as_text() for feature in configuration.hardware_requirements])
        section.add_list("Supported Locales", configuration.locales)
        section.add_list("Screen Densities", configuration.screen_densities)

        section = self.add_section("DEX Metrics", responsive=True, max_columns=2)
        for label, value in self._dex_metrics_formatter.fields(dex_metrics):
            section.add_entry(label, value)

        section = self.add_section("Embedded Content")
        section.add_list("Discovered URLs", embedded_content.urls)

    def _format_size(self, size: int | None) -> str:
        return "Unknown" if size is None else self._size_formatter.format(size, True)

    def _format_date(self, application: ApplicationInfo) -> str:
        modified = application.last_modified
        return "Unknown" if modified is None else self._date_formatter.format(modified)
