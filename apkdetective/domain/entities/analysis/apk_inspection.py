"""
What an ApkInspector learns by looking inside an APK: everything except
the archive's file tree, which is obtained through a separate port.
"""

from dataclasses import dataclass

from apkdetective.domain.entities.analysis.analysis_warning import AnalysisWarning
from apkdetective.domain.entities.analysis.sections.application_info import ApplicationInfo
from apkdetective.domain.entities.analysis.sections.configuration_info import ConfigurationInfo
from apkdetective.domain.entities.manifest.components.declared_components import DeclaredComponents
from apkdetective.domain.entities.analysis.sections.dex_metrics import DexMetrics
from apkdetective.domain.entities.analysis.sections.embedded_content import EmbeddedContent
from apkdetective.domain.entities.manifest.permissions.permissions_info import PermissionsInfo
from apkdetective.domain.entities.analysis.sections.security_info import SecurityInfo
from apkdetective.domain.entities.analysis.sections.third_party_info import ThirdPartyInfo


@dataclass(frozen=True)
class ApkInspection:
    application: ApplicationInfo
    configuration: ConfigurationInfo
    dex_metrics: DexMetrics
    embedded_content: EmbeddedContent
    security: SecurityInfo
    permissions: PermissionsInfo
    third_party: ThirdPartyInfo
    components: DeclaredComponents
    icon_png: bytes | None
    manifest_xml: str
    warnings: tuple[AnalysisWarning, ...] = ()
