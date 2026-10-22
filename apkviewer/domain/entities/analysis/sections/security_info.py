"""
Signing certificates and signature schemes of an APK.
"""

from dataclasses import dataclass

from apkviewer.domain.entities.analysis.sections.certificate import Certificate


@dataclass(frozen=True)
class SecurityInfo:
    certificates: tuple[Certificate, ...]
    # APK signature schemes present, e.g. ("v1 (JAR)", "v2", "v3"). v4 lives in a separate
    # .idsig file, so it can't be detected from the APK alone.
    signature_schemes: tuple[str, ...] = ()
