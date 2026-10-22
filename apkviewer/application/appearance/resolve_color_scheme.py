"""
Use case: turn the user's color preference into the scheme to render.
The operating system is only queried when the preference is AUTO.
"""

from apkviewer.domain.entities.appearance.color_mode_enum import ColorModeEnum
from apkviewer.domain.entities.appearance.color_scheme_enum import ColorSchemeEnum
from apkviewer.ports.system.system_color_scheme_detector_port import SystemColorSchemeDetectorPort


class ResolveColorScheme:
    def __init__(self, detector: SystemColorSchemeDetectorPort) -> None:
        self._detector: SystemColorSchemeDetectorPort = detector

    def execute(self, mode: ColorModeEnum) -> ColorSchemeEnum:
        if mode is ColorModeEnum.LIGHT:
            return ColorSchemeEnum.LIGHT
        if mode is ColorModeEnum.DARK:
            return ColorSchemeEnum.DARK
        return self._detector.detect()
