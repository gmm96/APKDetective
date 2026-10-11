"""
The parts an APK analysis is made of, so a warning can say WHAT could not be
read. Which tab shows each part is a decision of the presentation layer.
"""

from enum import Enum


class AnalysisSection(Enum):
    APPLICATION = "application"
    CONFIGURATION = "configuration"
    EMBEDDED_CONTENT = "embedded content"
    SIGNATURES = "signatures"
    PERMISSIONS = "permissions"
    THIRD_PARTY = "third-party code"
    COMPONENTS = "components"
    MANIFEST = "manifest"
    ICON = "icon"
