"""
Extracts the core application identity, SDK versions, and physical file metrics.
"""

import os
from datetime import datetime
from typing import Any

from androguard.core.apk import APK
from androguard.core.axml import AXMLPrinter

from apkviewer.domain.entities.analysis.sections.application_info import ApplicationInfo
from apkviewer.domain.entities.analysis.analysis_section_enum import AnalysisSectionEnum
from apkviewer.infrastructure.androguard.analysis_warnings import AnalysisWarningCollector
from apkviewer.infrastructure.androguard.config.android import ANDROID_NS


class ApplicationInfoExtractor:
    def extract(
        self,
        apk: APK,
        warnings: AnalysisWarningCollector | None = None
    ) -> ApplicationInfo:
        path = apk.get_filename()
        target_sdk_int = apk.get_effective_target_sdk_version()
        min_sdk = apk.get_min_sdk_version()
        min_sdk = "1" if min_sdk is None else str(min_sdk)
        app_info: ApplicationInfo = ApplicationInfo(
            app_name=apk.get_app_name() or "",
            package_name=apk.get_package() or "",
            version_name=apk.get_androidversion_name(),
            version_code=apk.get_androidversion_code(),
            min_sdk=min_sdk,
            target_sdk=str(target_sdk_int),
            max_sdk=apk.get_max_sdk_version() or None,
            file_name=os.path.basename(path) if path else None,
            file_path=os.path.realpath(path) if path else None,
            file_size=self._file_size(path),
            last_modified=self._last_modified(path),
        )
        try:
            xml_root = apk.get_android_manifest_xml()
            app_node = xml_root.find("application") if xml_root is not None else None
            if app_node is None:
                self._warn(warnings, "The manifest is missing or corrupted: no components could be listed.")
                return app_info

            app_info.debuggable = self._parse_flag(app_node, "debuggable", False)
            app_info.allow_backup = self._parse_flag(app_node, "allowBackup", True)
            app_info.test_only = self._parse_flag(app_node, "testOnly", False)
            app_info.hardware_accelerated = self._parse_flag(app_node, "hardwareAccelerated", True)
            app_info.extract_native_libs = self._parse_flag(app_node, "extractNativeLibs", True)
            app_info.cleartext_traffic_permitted = self._parse_flag(app_node, "usesCleartextTraffic", target_sdk_int <= 27)

            network_config_ref = app_node.get(f"{ANDROID_NS}networkSecurityConfig")
            if network_config_ref is None:
                app_info.trust_user_certificates = target_sdk_int <= 23
                app_info.certificate_pinning_enforced = False
            else:
                config_root = self._load_network_security_config(apk, network_config_ref)
                if config_root is None:
                    self._warn(warnings, "The network security configuration file could not be resolved or parsed.")
                else:
                    app_info.trust_user_certificates = self._trust_user_certificates(config_root, target_sdk_int, app_info.debuggable)
                    app_info.certificate_pinning_enforced = self._has_active_certificate_pinning(config_root)

        except Exception as exc:
            self._warn(
                warnings,
                f"The manifest could not be read completely ({type(exc).__name__}): "
                "some flags are missing or invalid.",
            )

        return app_info

    @staticmethod
    def _load_network_security_config(
        apk: APK,
        resource_ref: str
    ) -> AXMLPrinter | None:
        resource_path = apk.get_res_value(resource_ref)
        if not resource_path or resource_path == resource_ref or resource_path.startswith("@"):
            return None
        xml_data = apk.get_file(resource_path)
        return AXMLPrinter(xml_data).get_xml_obj()

    @staticmethod
    def _trust_user_certificates(
        config_root: Any,
        target_sdk_int: int,
        debuggable: bool
    ) -> bool:
        trust_anchor_nodes = (
            config_root.findall(".//base-config/trust-anchors")
            + config_root.findall(".//domain-config/trust-anchors")
        )
        if debuggable:
            trust_anchor_nodes.extend(config_root.findall("./debug-overrides/trust-anchors"))

        if any(
                certificate.get("src", "").lower() == "user"
                for trust_anchors in trust_anchor_nodes
                for certificate in trust_anchors.findall("certificates")
        ):
            return True

        base_config = config_root.find("base-config")
        if base_config is not None and base_config.find("trust-anchors") is not None:
            return False

        return target_sdk_int <= 23

    @staticmethod
    def _has_active_certificate_pinning(
        config_root: Any
    ) -> bool:
        today = datetime.now().date()
        for pin_set in config_root.iter("pin-set"):
            if not pin_set.findall("pin"):
                continue
            expiration = pin_set.get("expiration")
            if expiration:
                try:
                    expiration_date = datetime.strptime(expiration, "%Y-%m-%d").date()
                except ValueError:
                    continue
                if expiration_date <= today:
                    continue
            return True
        return False

    @staticmethod
    def _file_size(path: str | None) -> int | None:
        if not path:
            return None
        try:
            return os.path.getsize(path)
        except OSError:
            return None

    @staticmethod
    def _last_modified(path: str | None) -> datetime | None:
        if not path:
            return None
        try:
            return datetime.fromtimestamp(os.path.getmtime(path))
        except OSError:
            return None

    @staticmethod
    def _warn(warnings: AnalysisWarningCollector | None, message: str) -> None:
        if warnings is not None:
            warnings.add(message, AnalysisSectionEnum.COMPONENTS)

    @staticmethod
    def _parse_flag(node: Any, attr: str, default: bool) -> bool:
        value = node.get(f"{ANDROID_NS}{attr}") if node is not None else None
        if node is None or value is None:
            return default
        return value.lower() == "true"
