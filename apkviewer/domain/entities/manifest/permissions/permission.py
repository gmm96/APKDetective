"""
A permission an APK requests or declares.
"""

from dataclasses import dataclass

from apkviewer.domain.entities.manifest.permissions.permission_origin_enum import PermissionOriginEnum
from apkviewer.domain.entities.manifest.permissions.protection_level import ProtectionLevel


@dataclass(frozen=True)
class Permission:
    name: str
    protection: str | None = None  # normalized ('dangerous', 'signature|appop'...); None when nothing defines it
    label: str | None = None       # short summary of what it allows
    max_sdk: str | None = None     # maxSdkVersion of the <uses-permission>
    origin: PermissionOriginEnum = PermissionOriginEnum.REQUESTED

    @property
    def is_dangerous(self) -> bool:
        return ProtectionLevel.includes(self.protection, "dangerous")

    @property
    def is_app_op(self) -> bool:
        return ProtectionLevel.includes(self.protection, "appop")

    @property
    def type_text(self) -> str:
        return ProtectionLevel.describe(self.protection)
