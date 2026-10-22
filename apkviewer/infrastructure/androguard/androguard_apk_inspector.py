"""
Androguard-backed implementation of the ApkInspector port. It loads the
APK once, reads its DEX files once, runs every extractor and maps their
results into a single ApkInspection entity.

Each extractor runs guarded: if one of them fails, the rest of the
analysis still completes and a warning says what is missing, instead of
the whole APK being rejected or the section silently coming up empty.
"""

from collections.abc import Callable
from typing import TypeVar

from loguru import logger

from apkviewer.domain.entities.analysis.analysis_section_enum import AnalysisSectionEnum
from apkviewer.domain.entities.analysis.apk_inspection import ApkInspection
from apkviewer.domain.entities.analysis.sections.application_info import ApplicationInfo
from apkviewer.domain.entities.analysis.sections.configuration_info import ConfigurationInfo
from apkviewer.domain.entities.manifest.components.declared_components import DeclaredComponents
from apkviewer.domain.entities.analysis.sections.dex_metrics import DexMetrics
from apkviewer.domain.entities.analysis.sections.embedded_content import EmbeddedContent
from apkviewer.domain.entities.manifest.permissions.permissions_info import PermissionsInfo
from apkviewer.domain.entities.analysis.sections.security_info import SecurityInfo
from apkviewer.domain.entities.analysis.sections.third_party_info import ThirdPartyInfo
from apkviewer.ports.apk.apk_inspector_port import ApkInspectorPort
from apkviewer.infrastructure.androguard.analysis_warnings import AnalysisWarningCollector
from apkviewer.infrastructure.androguard.apk_loader import ApkLoader
from apkviewer.infrastructure.androguard.dex.dex_contents import DexContents
from apkviewer.infrastructure.androguard.dex.dex_reader import DexReader
from apkviewer.infrastructure.androguard.extractors.app_info_extractor import ApplicationInfoExtractor
from apkviewer.infrastructure.androguard.extractors.components_extractor import ComponentsExtractor
from apkviewer.infrastructure.androguard.extractors.configuration_extractor import ConfigurationExtractor
from apkviewer.infrastructure.androguard.extractors.dex_metrics_extractor import DexMetricsExtractor
from apkviewer.infrastructure.androguard.extractors.embedded_content_extractor import EmbeddedContentExtractor
from apkviewer.infrastructure.androguard.extractors.permissions_extractor import PermissionsExtractor
from apkviewer.infrastructure.androguard.extractors.security_info_extractor import SecurityInfoExtractor
from apkviewer.infrastructure.androguard.extractors.tracker_detector import TrackerDetector
from apkviewer.infrastructure.androguard.extractors.icon_extractor import IconExtractor
from apkviewer.infrastructure.androguard.manifest.manifest_formatter import ManifestFormatter

logger.disable("androguard")  # it logs thousands of DEBUG lines per APK

T = TypeVar("T")


class AndroguardApkInspector(ApkInspectorPort):
    def __init__(
        self,
        apk_loader: ApkLoader | None = None,
        dex_reader: DexReader | None = None,
        dex_metrics_extractor: DexMetricsExtractor | None = None,
        icon_extractor: IconExtractor | None = None,
        manifest_formatter: ManifestFormatter | None = None,
        application_extractor: ApplicationInfoExtractor | None = None,
        configuration_extractor: ConfigurationExtractor | None = None,
        embedded_content_extractor: EmbeddedContentExtractor | None = None,
        security_extractor: SecurityInfoExtractor | None = None,
        permissions_extractor: PermissionsExtractor | None = None,
        tracker_detector: TrackerDetector | None = None,
        components_extractor: ComponentsExtractor | None = None,
    ) -> None:
        self._apk_loader = apk_loader or ApkLoader()
        self._dex_reader = dex_reader or DexReader()
        self._dex_metrics = dex_metrics_extractor or DexMetricsExtractor()
        self._icon_extractor = icon_extractor or IconExtractor()
        self._manifest_formatter = manifest_formatter or ManifestFormatter()
        self._application = application_extractor or ApplicationInfoExtractor()
        self._configuration = configuration_extractor or ConfigurationExtractor()
        self._embedded_content = embedded_content_extractor or EmbeddedContentExtractor()
        self._security = security_extractor or SecurityInfoExtractor()
        self._permissions = permissions_extractor or PermissionsExtractor()
        self._trackers = tracker_detector or TrackerDetector()
        self._components = components_extractor or ComponentsExtractor()

    def inspect(self, apk_path: str) -> ApkInspection:
        warnings = AnalysisWarningCollector()
        apk = self._apk_loader.load(apk_path)  # an APK that can't even be opened is a real error
        guard = self._guarded
        section = AnalysisSectionEnum

        # The DEX files are read from the APK once and shared by everything that looks at the code.
        dex_files = guard(
            warnings,
            "The code (DEX) of the app",
            (section.EMBEDDED_CONTENT, section.THIRD_PARTY,
             section.DEX_METRICS),
            lambda: tuple(apk.get_all_dex()), (),
        )
        dex = guard(
            warnings,
            "The code (DEX) of the app",
            (section.EMBEDDED_CONTENT, section.THIRD_PARTY),
            lambda: self._dex_reader.read(dex_files, warnings),
            DexContents(),
        )
        return ApkInspection(
            application=guard(
                warnings,
                "The application data",
                (section.APPLICATION,),
                lambda: self._application.extract(apk),
                ApplicationInfo("", "", None, None, None, None, None, None, None, None, None),
            ),
            configuration=guard(
                warnings,
                "The configuration",
                (section.CONFIGURATION,),
                lambda: self._configuration.extract(apk, warnings),
                ConfigurationInfo((), (), (), ()),
            ),
            dex_metrics=guard(
                warnings,
                "The DEX metrics",
                (section.DEX_METRICS,),
                lambda: self._dex_metrics.extract(dex_files, dex, warnings),
                DexMetrics(),
            ),
            embedded_content=guard(
                warnings,
                "The embedded content",
                (section.EMBEDDED_CONTENT,),
                lambda: self._embedded_content.extract(dex),
                EmbeddedContent(()),
            ),
            security=guard(
                warnings,
                "The signatures",
                (section.SIGNATURES,),
                lambda: self._security.extract(apk, warnings),
                SecurityInfo(()),
            ),
            permissions=guard(
                warnings,
                "The permissions",
                (section.PERMISSIONS,),
                lambda: self._permissions.extract(apk, warnings),
                PermissionsInfo(),
            ),
            third_party=guard(
                warnings,
                "The third-party code",
                (section.THIRD_PARTY,),
                lambda: self._trackers.extract(apk, dex),
                ThirdPartyInfo((), ()),
            ),
            components=guard(
                warnings,
                "The components",
                (section.COMPONENTS,),
                lambda: self._components.extract(apk, warnings),
                DeclaredComponents(),
            ),
            icon_png=guard(
                warnings,
                "The icon",
                (section.ICON,),
                lambda: self._icon_extractor.extract(apk, warnings),
                None,
            ),
            manifest_xml=guard(
                warnings,
                "The manifest",
                (section.MANIFEST,),
                lambda: self._manifest_formatter.format(apk),
                "",
            ),
            warnings=warnings.as_tuple(),
        )

    @staticmethod
    def _guarded(
        warnings: AnalysisWarningCollector,
        what: str,
        sections: tuple[AnalysisSectionEnum, ...],
        read: Callable[[], T],
        default: T,
    ) -> T:
        try:
            return read()
        except Exception as exc:  # pylint: disable=broad-except
            warnings.add(f"{what} could not be read ({type(exc).__name__}: {exc}).", *sections)
            return default
