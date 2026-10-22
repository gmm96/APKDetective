"""
Linux implementations of the OS-dependent services.
"""

from apkviewer.ports.system.clipboard_file_copier_port import ClipboardFileCopierPort
from apkviewer.ports.system.os_file_opener_port import OsFileOpenerPort
from apkviewer.ports.system.platform_services_port import PlatformServicesPort
from apkviewer.ports.system.system_color_scheme_detector_port import SystemColorSchemeDetectorPort
from apkviewer.ports.system.url_opener_port import UrlOpenerPort
from apkviewer.infrastructure.appearance.linux_color_scheme_detector import LinuxColorSchemeDetector
from apkviewer.infrastructure.clipboard.linux_clipboard_file_copier import LinuxClipboardFileCopier
from apkviewer.infrastructure.os_integration.linux_file_opener import LinuxFileOpener
from apkviewer.infrastructure.url.webbrowser_url_opener import WebBrowserUrlOpener


class LinuxPlatformServices(PlatformServicesPort):
    def create_os_file_opener(self) -> OsFileOpenerPort:
        return LinuxFileOpener()

    def create_clipboard_file_copier(self) -> ClipboardFileCopierPort:
        return LinuxClipboardFileCopier()

    def create_url_opener(self) -> UrlOpenerPort:
        return WebBrowserUrlOpener()

    def create_system_color_scheme_detector(self) -> SystemColorSchemeDetectorPort:
        return LinuxColorSchemeDetector()
