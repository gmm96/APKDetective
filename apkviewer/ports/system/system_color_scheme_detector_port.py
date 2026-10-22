"""
Port for asking the operating system which color scheme (light or dark)
the user has selected.
"""

from abc import ABC, abstractmethod

from apkviewer.domain.entities.appearance.color_scheme_enum import ColorSchemeEnum


class SystemColorSchemeDetectorPort(ABC):
    @abstractmethod
    def detect(self) -> ColorSchemeEnum:
        """Return the OS scheme; LIGHT whenever it cannot be determined."""
        raise NotImplementedError
