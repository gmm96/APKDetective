"""
Fallback services for platforms with no native integration at all.
"""

from apkdetective.ports.system.clipboard_file_copier_port import ClipboardFileCopierPort
from apkdetective.ports.system.os_file_opener_port import OsFileOpenerPort
from apkdetective.ports.system.platform_services_port import PlatformServicesPort
from apkdetective.ports.system.system_color_scheme_detector_port import SystemColorSchemeDetectorPort
from apkdetective.ports.system.url_opener_port import UrlOpenerPort
from apkdetective.infrastructure.appearance.unsupported_color_scheme_detector import UnsupportedColorSchemeDetector
from apkdetective.infrastructure.clipboard.unsupported_clipboard_file_copier import UnsupportedClipboardFileCopier
from apkdetective.infrastructure.os_integration.unsupported_file_opener import UnsupportedFileOpener
from apkdetective.infrastructure.url.webbrowser_url_opener import WebBrowserUrlOpener


class UnsupportedPlatformServices(PlatformServicesPort):
    def create_os_file_opener(self) -> OsFileOpenerPort:
        return UnsupportedFileOpener()

    def create_clipboard_file_copier(self) -> ClipboardFileCopierPort:
        return UnsupportedClipboardFileCopier()

    def create_url_opener(self) -> UrlOpenerPort:
        return WebBrowserUrlOpener()

    def create_system_color_scheme_detector(self) -> SystemColorSchemeDetectorPort:
        return UnsupportedColorSchemeDetector()
