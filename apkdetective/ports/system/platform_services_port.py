"""
Port (abstract factory) that groups every dependency whose implementation
depends on the operating system. The composition root asks it for what it
needs, so the rest of the code never checks the platform itself.
"""

from abc import ABC, abstractmethod

from .clipboard_file_copier_port import ClipboardFileCopierPort
from .os_file_opener_port import OsFileOpenerPort
from .system_color_scheme_detector_port import SystemColorSchemeDetectorPort
from .url_opener_port import UrlOpenerPort


class PlatformServicesPort(ABC):
    @abstractmethod
    def create_os_file_opener(self) -> OsFileOpenerPort:
        raise NotImplementedError

    @abstractmethod
    def create_clipboard_file_copier(self) -> ClipboardFileCopierPort:
        raise NotImplementedError

    @abstractmethod
    def create_url_opener(self) -> UrlOpenerPort:
        raise NotImplementedError

    @abstractmethod
    def create_system_color_scheme_detector(self) -> SystemColorSchemeDetectorPort:
        raise NotImplementedError
