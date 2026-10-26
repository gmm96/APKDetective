"""
macOS implementation of SystemColorSchemeDetector: the global
AppleInterfaceStyle default only exists (as "Dark") in dark mode.
"""

import subprocess

from apkdetective.domain.entities.appearance.color_scheme_enum import ColorSchemeEnum
from apkdetective.ports.system.system_color_scheme_detector_port import SystemColorSchemeDetectorPort


class MacColorSchemeDetector(SystemColorSchemeDetectorPort):
    def detect(self) -> ColorSchemeEnum:
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, timeout=2, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return ColorSchemeEnum.LIGHT
        is_dark = result.returncode == 0 and "dark" in result.stdout.lower()
        return ColorSchemeEnum.DARK if is_dark else ColorSchemeEnum.LIGHT
