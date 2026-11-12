"""
"Info" tab: app identity, versions, SDK range, file data, flags and configuration.
"""

from collections.abc import Sequence

import ttkbootstrap as ttkb

from apkdetective.domain.entities.analysis.sections.android_abi_enum import AndroidAbiEnum
from apkdetective.domain.entities.analysis.sections.application_info import ApplicationInfo
from apkdetective.domain.entities.analysis.sections.configuration_info import ConfigurationInfo
from apkdetective.ports.formatting.date_formatter_port import DateFormatterPort
from apkdetective.ports.formatting.size_formatter_port import SizeFormatterPort
from apkdetective.presentation.viewmodels.appearance.theme_palette import ThemePalette
from apkdetective.presentation.common.forms.form_panel import FormPanel
from apkdetective.presentation.common.menus.text_context_menu import TextContextMenu
from apkdetective.presentation.common.forms.text_line_marker import TextLineMarker
from apkdetective.presentation.formatting.english_long_date_formatter import EnglishLongDateFormatter
from apkdetective.presentation.formatting.human_readable_size_formatter import HumanReadableSizeFormatter
from apkdetective.presentation.viewmodels.forms.toggle_spec import ToggleSpec


class InfoPanel(FormPanel):
    # A flag's value is a toggle plus "true" / "false", far narrower than the text fields the sections assume
    # (FormSection.DEFAULT_MIN_FIELD_WIDTH_PX); with that default the flags would stay in one column in windows
    # that have room for two.
    _FLAG_MIN_FIELD_WIDTH_PX: int = 100

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

    def render(
        self,
        application: ApplicationInfo,
        configuration: ConfigurationInfo,
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

        flags_section = self.add_section(
            "Flags",
            responsive=True,
            max_columns=2,
            min_field_width=InfoPanel._FLAG_MIN_FIELD_WIDTH_PX,
        )
        flags_section.add_flag("Debuggable", application.debuggable or False)
        flags_section.add_flag("Allow Backup", application.allow_backup or False)
        flags_section.add_flag("Test Only", application.test_only or False)
        flags_section.add_flag("Hardware Accelerated", application.hardware_accelerated or False)
        flags_section.add_flag("Extract Native Libs", application.extract_native_libs or False)
        flags_section.add_flag("Cleartext Traffic Permitted", application.cleartext_traffic_permitted or False)
        flags_section.add_flag("Trusts User Certificates", application.trust_user_certificates or False)
        flags_section.add_flag("Certificate Pinning Enforced", application.certificate_pinning_enforced or False)

        section = self.add_section("Configuration")
        section.add_toggles(
            "Architectures",
            [ToggleSpec(name) for name in self._architecture_names(configuration.architectures)],
        )
        section.add_list("Hardware Requirements", [feature.as_text() for feature in configuration.hardware_requirements])
        section.add_list("Supported Locales", configuration.locales)
        section.add_toggles(
            "Screen Densities",
            [ToggleSpec(density.name, density.description) for density in configuration.screen_densities],
        )

    @staticmethod
    def _architecture_names(supported: Sequence[str]) -> list[str]:
        """
        The architectures the APK supports, the known ones in the order of AndroidAbiEnum and then any other.
        An APK without native code runs on every architecture.
        """
        known = [abi.value for abi in AndroidAbiEnum]
        if not supported:
            return known
        return sorted(supported, key=lambda name: known.index(name) if name in known else len(known))

    def _format_size(self, size: int | None) -> str:
        return "Unknown" if size is None else self._size_formatter.format(size, True)

    def _format_date(self, application: ApplicationInfo) -> str:
        modified = application.last_modified
        return "Unknown" if modified is None else self._date_formatter.format(modified)
