"""
A permission an APK requests or declares.
"""

from dataclasses import dataclass

from apkdetective.domain.entities.manifest.permissions.permission_origin_enum import PermissionOriginEnum
from apkdetective.domain.entities.manifest.permissions.permission_type_enum import PermissionTypeEnum
from apkdetective.domain.entities.manifest.permissions.protection_level import ProtectionLevel


@dataclass(frozen=True)
class Permission:
    name: str
    type: PermissionTypeEnum = PermissionTypeEnum.CUSTOM
    protection: str | None = None  # normalized ('dangerous', 'signature|appop'...); None when nothing defines it
    label: str | None = None       # short summary of what it allows
    max_sdk: str | None = None     # maxSdkVersion of the <uses-permission>
    origin: PermissionOriginEnum = PermissionOriginEnum.REQUESTED

    @property
    def is_dangerous(self) -> bool:
        return ProtectionLevel.is_dangerous(self.protection)

    @property
    def is_app_op(self) -> bool:
        return ProtectionLevel.is_app_op(self.protection)

    @property
    def level_text(self) -> str:
        return ProtectionLevel.describe(self.protection)
