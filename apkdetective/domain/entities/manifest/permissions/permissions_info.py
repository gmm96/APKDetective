"""
The permissions of an APK, split the way the UI shows them: framework
permissions, "app op" permissions (special access the user grants from
Settings) and custom permissions (anything Android itself doesn't define).
"""

from dataclasses import dataclass

from apkdetective.domain.entities.manifest.permissions.permission import Permission


@dataclass(frozen=True)
class PermissionsInfo:
    permissions: tuple[Permission, ...] = ()         # requested, defined by Android, not app-op
    app_ops: tuple[Permission, ...] = ()             # requested, special access ("appop" level)
    custom_permissions: tuple[Permission, ...] = ()  # not defined by Android: requested or declared here
