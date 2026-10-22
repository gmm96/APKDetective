"""
Fallback for platforms where the system color scheme cannot be queried.
"""

from apkviewer.domain.entities.appearance.color_scheme_enum import ColorSchemeEnum
from apkviewer.ports.system.system_color_scheme_detector_port import SystemColorSchemeDetectorPort


class UnsupportedColorSchemeDetector(SystemColorSchemeDetectorPort):
    def detect(self) -> ColorSchemeEnum:
        return ColorSchemeEnum.LIGHT
