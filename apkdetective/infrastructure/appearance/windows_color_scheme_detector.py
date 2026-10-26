"""
Windows implementation of SystemColorSchemeDetector: reads the "apps use
light theme" flag from the registry.
"""

import importlib

from apkdetective.domain.entities.appearance.color_scheme_enum import ColorSchemeEnum
from apkdetective.ports.system.system_color_scheme_detector_port import SystemColorSchemeDetectorPort


class WindowsColorSchemeDetector(SystemColorSchemeDetectorPort):
    _KEY: str = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    _VALUE: str = "AppsUseLightTheme"

    def detect(self) -> ColorSchemeEnum:
        try:
            winreg = importlib.import_module("winreg")
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._KEY) as key:
                uses_light, _ = winreg.QueryValueEx(key, self._VALUE)
        except (ImportError, OSError):
            return ColorSchemeEnum.LIGHT
        return ColorSchemeEnum.LIGHT if uses_light else ColorSchemeEnum.DARK
