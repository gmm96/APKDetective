"""
Fallback for platforms where the system color scheme cannot be queried.
"""

from apkdetective.domain.entities.appearance.color_scheme_enum import ColorSchemeEnum
from apkdetective.ports.system.system_color_scheme_detector_port import SystemColorSchemeDetectorPort


class UnsupportedColorSchemeDetector(SystemColorSchemeDetectorPort):
    def detect(self) -> ColorSchemeEnum:
        return ColorSchemeEnum.LIGHT
