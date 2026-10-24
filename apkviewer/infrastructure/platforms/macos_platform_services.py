"""
macOS implementations of the OS-dependent services.
"""

from apkviewer.ports.system.clipboard_file_copier_port import ClipboardFileCopierPort
from apkviewer.ports.system.os_file_opener_port import OsFileOpenerPort
from apkviewer.ports.system.platform_services_port import PlatformServicesPort
from apkviewer.ports.system.system_color_scheme_detector_port import SystemColorSchemeDetectorPort
from apkviewer.ports.system.url_opener_port import UrlOpenerPort
from apkviewer.infrastructure.appearance.macos_color_scheme_detector import MacColorSchemeDetector
from apkviewer.infrastructure.clipboard.macos_clipboard_file_copier import MacClipboardFileCopier
from apkviewer.infrastructure.os_integration.macos_file_opener import MacFileOpener
from apkviewer.infrastructure.url.webbrowser_url_opener import WebBrowserUrlOpener


class MacPlatformServices(PlatformServicesPort):
    def create_os_file_opener(self) -> OsFileOpenerPort:
        return MacFileOpener()

    def create_clipboard_file_copier(self) -> ClipboardFileCopierPort:
        return MacClipboardFileCopier()

    def create_url_opener(self) -> UrlOpenerPort:
        return WebBrowserUrlOpener()

    def create_system_color_scheme_detector(self) -> SystemColorSchemeDetectorPort:
        return MacColorSchemeDetector()
