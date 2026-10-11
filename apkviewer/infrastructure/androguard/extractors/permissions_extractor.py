"""
Extracts the permissions an APK requests (<uses-permission>) and declares
(<permission>), and sorts them into the three groups the UI shows.

Android decides the protection level, label and description of its own
permissions (see AospPermissionCatalog). For the permissions the app
declares itself, those come from the manifest, with resource references
resolved through the app's resource table.
"""

from dataclasses import replace
from typing import Any

from androguard.core.apk import APK

from apkviewer.domain.entities.analysis_section import AnalysisSection
from apkviewer.domain.entities.permission import Permission
from apkviewer.domain.entities.permission_origin import PermissionOrigin
from apkviewer.domain.entities.permissions_info import PermissionsInfo
from apkviewer.domain.entities.protection_level import ProtectionLevel
from apkviewer.infrastructure.androguard.analysis_warnings import AnalysisWarningCollector
from apkviewer.infrastructure.androguard.aosp_permission_catalog import AospPermissionCatalog
from apkviewer.infrastructure.androguard.config.android import ANDROID_NS
from apkviewer.infrastructure.androguard.resource_reference_resolver import ResourceReferenceResolver


class PermissionsExtractor:
    def __init__(self, catalog: AospPermissionCatalog | None = None) -> None:
        self._catalog: AospPermissionCatalog = catalog or AospPermissionCatalog()

    def extract(self, apk: APK, warnings: AnalysisWarningCollector | None = None) -> PermissionsInfo:
        root = self._manifest_root(apk)
        if root is None:
            if warnings is not None:
                warnings.add(
                    "The manifest is missing or corrupted: no permissions could be listed.",
                    AnalysisSection.PERMISSIONS,
                )
            return PermissionsInfo()

        requested = self._requested(root)
        declared = self._declared(root, ResourceReferenceResolver(apk))
        # The database of the app's own targetSdk still lists permissions that later Android
        # versions dropped, so it is consulted when the newest database doesn't know a name.
        target_entries: dict[str, Any] = getattr(apk, "permission_module", None) or {}

        framework: list[Permission] = []
        app_ops: list[Permission] = []
        custom: dict[str, Permission] = {}
        for name, max_sdk in requested.items():
            if name in declared:
                custom[name] = replace(
                    declared[name], max_sdk=max_sdk, origin=PermissionOrigin.DECLARED_AND_REQUESTED
                )
                continue
            entry = self._catalog.lookup(name) or target_entries.get(name)
            if entry is None:
                custom[name] = Permission(name, max_sdk=max_sdk)
                continue
            permission = Permission(
                name=name,
                protection=ProtectionLevel.parse(entry.get("protectionLevel")),
                label=self._clean(entry.get("label")) or self._clean(entry.get("description")),
                max_sdk=max_sdk,
            )
            (app_ops if permission.is_app_op else framework).append(permission)
        for name, permission in declared.items():
            custom.setdefault(name, permission)

        return PermissionsInfo(
            permissions=tuple(sorted(framework, key=self._by_name)),
            app_ops=tuple(sorted(app_ops, key=self._by_name)),
            custom_permissions=tuple(sorted(custom.values(), key=self._by_name)),
        )

    # --- Manifest ---------------------------------------------------------------------------

    @staticmethod
    def _manifest_root(apk: APK) -> Any:
        try:
            return apk.get_android_manifest_xml()
        except Exception:  # pylint: disable=broad-except
            return None

    @staticmethod
    def _requested(root: Any) -> dict[str, str | None]:
        """name -> maxSdkVersion, from every <uses-permission*> (also the -sdk-23 variants)."""
        requested: dict[str, str | None] = {}
        for node in root:
            tag = node.tag
            if not isinstance(tag, str) or not tag.startswith("uses-permission"):
                continue
            name = node.get(f"{ANDROID_NS}name")
            if name and name not in requested:
                requested[name] = node.get(f"{ANDROID_NS}maxSdkVersion") or None
        return requested

    def _declared(self, root: Any, resolver: ResourceReferenceResolver) -> dict[str, Permission]:
        """The permissions the app defines with <permission>."""
        declared: dict[str, Permission] = {}
        for node in root.iter("permission"):
            name = node.get(f"{ANDROID_NS}name")
            if not name:
                continue
            declared[name] = Permission(
                name=name,
                protection=ProtectionLevel.parse(node.get(f"{ANDROID_NS}protectionLevel")),
                label=self._text(node.get(f"{ANDROID_NS}label"), resolver)
                or self._text(node.get(f"{ANDROID_NS}description"), resolver),
                origin=PermissionOrigin.DECLARED,
            )
        return declared

    # --- Helpers ---------------------------------------------------------------------------------

    @staticmethod
    def _by_name(permission: Permission) -> str:
        return permission.name.lower()

    @classmethod
    def _text(cls, value: str | None, resolver: ResourceReferenceResolver) -> str | None:
        if not value:
            return None
        text = resolver.literal(value)
        return cls._clean(text if text is not None else value)

    @staticmethod
    def _clean(text: Any) -> str | None:
        if not isinstance(text, str):
            return None
        return " ".join(text.split()) or None
