"""
Build configuration of an APK: ABIs, hardware requirements, locales and
screen densities. Empty tuples mean "nothing found".
"""

from dataclasses import dataclass

from apkdetective.domain.entities.analysis.sections.hardware_feature import HardwareFeature


@dataclass(frozen=True)
class ConfigurationInfo:
    architectures: tuple[str, ...]
    hardware_requirements: tuple[HardwareFeature, ...]
    locales: tuple[str, ...]
    screen_densities: tuple[str, ...]
