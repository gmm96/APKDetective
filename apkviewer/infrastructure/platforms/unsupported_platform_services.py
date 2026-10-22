"""
Fallback services for platforms with no native integration at all.
"""

from apkviewer.ports.system.clipboard_file_copier_port import ClipboardFileCopierPort
from apkviewer.ports.system.os_file_opener_port import OsFileOpenerPort
from apkviewer.ports.system.platform_services_port import PlatformServicesPort
from apkviewer.ports.system.system_color_scheme_detector_port import SystemColorSchemeDetectorPort
from apkviewer.ports.system.url_opener_port import UrlOpenerPort
from apkviewer.infrastructure.appearance.unsupported_color_scheme_detector import UnsupportedColorSchemeDetector
from apkviewer.infrastructure.clipboard.unsupported_clipboard_file_copier import UnsupportedClipboardFileCopier
from apkviewer.infrastructure.os_integration.unsupported_file_opener import UnsupportedFileOpener
from apkviewer.infrastructure.url.webbrowser_url_opener import WebBrowserUrlOpener


class UnsupportedPlatformServices(PlatformServicesPort):
    def create_os_file_opener(self) -> OsFileOpenerPort:
        return UnsupportedFileOpener()

    def create_clipboard_file_copier(self) -> ClipboardFileCopierPort:
        return UnsupportedClipboardFileCopier()

    def create_url_opener(self) -> UrlOpenerPort:
        return WebBrowserUrlOpener()

    def create_system_color_scheme_detector(self) -> SystemColorSchemeDetectorPort:
        return UnsupportedColorSchemeDetector()
