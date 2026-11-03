"""
Androguard-backed implementation of the ApkInspector port. It loads the
APK once, reads its DEX files once, runs every extractor and maps their
results into a single ApkInspection entity.

Each extractor runs guarded: if one of them fails, the rest of the
analysis still completes and a warning says what is missing, instead of
the whole APK being rejected or the section silently coming up empty.

The analysis of the code (DEX) needs nothing but the bytes of the DEX files, so it runs at the same time as
everything that depends on the resource table, in another process when the computer has a core to spare.

The analysis can be cancelled: the token is checked before every step and, inside the DEX
files, every few classes. A step that is running (such as loading the APK) is not interrupted;
the analysis stops as soon as it ends.
"""

from collections.abc import Callable
from functools import partial
from typing import TypeVar

from loguru import logger

from apkdetective.domain.entities.analysis.analysis_section_enum import AnalysisSectionEnum
from apkdetective.domain.entities.analysis.apk_inspection import ApkInspection
from apkdetective.domain.entities.analysis.cancellation_token import CancellationToken
from apkdetective.domain.entities.analysis.sections.application_info import ApplicationInfo
from apkdetective.domain.entities.analysis.sections.configuration_info import ConfigurationInfo
from apkdetective.domain.entities.manifest.components.declared_components import DeclaredComponents
from apkdetective.domain.entities.manifest.permissions.permissions_info import PermissionsInfo
from apkdetective.domain.entities.analysis.sections.security_info import SecurityInfo
from apkdetective.domain.entities.analysis.sections.third_party_info import ThirdPartyInfo
from apkdetective.ports.apk.apk_inspector_port import ApkInspectorPort
from apkdetective.infrastructure.androguard.analysis_warnings import AnalysisWarningCollector
from apkdetective.infrastructure.androguard.apk_loader import ApkLoader
from apkdetective.infrastructure.androguard.dex.dex_contents import DexContents
from apkdetective.infrastructure.androguard.dex.dex_analysis import DexAnalysis
from apkdetective.infrastructure.androguard.dex.dex_analysis_starter import DexAnalysisStarter
from apkdetective.infrastructure.androguard.extractors.app_info_extractor import ApplicationInfoExtractor
from apkdetective.infrastructure.androguard.extractors.components_extractor import ComponentsExtractor
from apkdetective.infrastructure.androguard.extractors.configuration_extractor import ConfigurationExtractor
from apkdetective.infrastructure.androguard.extractors.permissions_extractor import PermissionsExtractor
from apkdetective.infrastructure.androguard.extractors.security_info_extractor import SecurityInfoExtractor
from apkdetective.infrastructure.androguard.paused_garbage_collector import PausedGarbageCollector
from apkdetective.infrastructure.androguard.extractors.tracker_detector import TrackerDetector
from apkdetective.infrastructure.androguard.extractors.icon_extractor import IconExtractor
from apkdetective.infrastructure.androguard.manifest.manifest_formatter import ManifestFormatter

logger.disable("androguard")  # it logs thousands of DEBUG lines per APK

T = TypeVar("T")


class AndroguardApkInspector(ApkInspectorPort):
    def __init__(
        self,
        apk_loader: ApkLoader | None = None,
        dex_analysis_starter: DexAnalysisStarter | None = None,
        icon_extractor: IconExtractor | None = None,
        manifest_formatter: ManifestFormatter | None = None,
        application_extractor: ApplicationInfoExtractor | None = None,
        configuration_extractor: ConfigurationExtractor | None = None,
        security_extractor: SecurityInfoExtractor | None = None,
        permissions_extractor: PermissionsExtractor | None = None,
        tracker_detector: TrackerDetector | None = None,
        components_extractor: ComponentsExtractor | None = None,
    ) -> None:
        self._apk_loader = apk_loader or ApkLoader()
        self._dex_analysis_starter = dex_analysis_starter or DexAnalysisStarter()
        self._icon_extractor = icon_extractor or IconExtractor()
        self._manifest_formatter = manifest_formatter or ManifestFormatter()
        self._application = application_extractor or ApplicationInfoExtractor()
        self._configuration = configuration_extractor or ConfigurationExtractor()
        self._security = security_extractor or SecurityInfoExtractor()
        self._permissions = permissions_extractor or PermissionsExtractor()
        self._trackers = tracker_detector or TrackerDetector()
        self._components = components_extractor or ComponentsExtractor()

    def inspect(self, apk_path: str, cancellation: CancellationToken) -> ApkInspection:
        with PausedGarbageCollector():
            return self._inspect(apk_path, cancellation)

    def _inspect(self, apk_path: str, cancellation: CancellationToken) -> ApkInspection:
        warnings = AnalysisWarningCollector()
        cancellation.raise_if_cancelled()
        apk = self._apk_loader.load(apk_path)  # an APK that can't even be opened is a real error
        guard = partial(self._guarded, warnings, cancellation)
        section = AnalysisSectionEnum

        # The DEX files are read from the APK once. Everything that looks at the code needs nothing else, so its
        # analysis is started now (in another process when there is a core to spare) while this one goes on
        # with everything that depends on the resource table.
        dex_files = guard(
            "The code (DEX) of the app",
            (section.EMBEDDED_CONTENT, section.THIRD_PARTY, section.DEX_METRICS),
            lambda: tuple(apk.get_all_dex()), (),
        )
        dex_job = self._dex_analysis_starter.start(dex_files)
        try:
            application = guard(
                "The application data",
                (section.APPLICATION,),
                lambda: self._application.extract(apk),
                ApplicationInfo("", "", None, None, None, None, None, None, None, None, None),
            )
            configuration = guard(
                "The configuration",
                (section.CONFIGURATION,),
                lambda: self._configuration.extract(apk, warnings),
                ConfigurationInfo((), (), (), ()),
            )
            security = guard(
                "The signatures",
                (section.SIGNATURES,),
                lambda: self._security.extract(apk, warnings),
                SecurityInfo(()),
            )
            permissions = guard(
                "The permissions",
                (section.PERMISSIONS,),
                lambda: self._permissions.extract(apk, warnings),
                PermissionsInfo(),
            )
            components = guard(
                "The components",
                (section.COMPONENTS,),
                lambda: self._components.extract(apk, warnings),
                DeclaredComponents(),
            )
            icon_png = guard(
                "The icon",
                (section.ICON,),
                lambda: self._icon_extractor.extract(apk, warnings),
                None,
            )
            manifest_xml = guard(
                "The manifest",
                (section.MANIFEST,),
                lambda: self._manifest_formatter.format(apk),
                "",
            )
            dex = guard(
                "The code (DEX) of the app",
                (section.EMBEDDED_CONTENT, section.THIRD_PARTY, section.DEX_METRICS),
                lambda: dex_job.result(cancellation),
                DexAnalysis.empty(),
            )
            warnings.extend(dex.warnings)
            third_party = guard(
                "The third-party code",
                (section.THIRD_PARTY,),
                lambda: self._trackers.extract(apk, DexContents(class_names=dex.class_names)),
                ThirdPartyInfo((), ()),
            )
        finally:
            dex_job.discard()  # whatever is still running for a result nobody is going to read stops
        return ApkInspection(
            application=application,
            configuration=configuration,
            dex_metrics=dex.metrics,
            embedded_content=dex.embedded_content,
            security=security,
            permissions=permissions,
            third_party=third_party,
            components=components,
            icon_png=icon_png,
            manifest_xml=manifest_xml,
            warnings=warnings.as_tuple(),
        )

    @staticmethod
    def _guarded(
        warnings: AnalysisWarningCollector,
        cancellation: CancellationToken,
        what: str,
        sections: tuple[AnalysisSectionEnum, ...],
        read: Callable[[], T],
        default: T,
    ) -> T:
        cancellation.raise_if_cancelled()
        return warnings.attempt(what, sections, read, default)
