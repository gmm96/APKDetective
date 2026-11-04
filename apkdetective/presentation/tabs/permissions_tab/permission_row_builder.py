"""
Maps the permissions into RecordNode rows for the permissions table. Pure
functions of the entities: no Tk involved.
"""

from dataclasses import replace

from apkdetective.domain.entities.manifest.permissions.permission import Permission
from apkdetective.domain.entities.manifest.permissions.permissions_info import PermissionsInfo
from apkdetective.presentation.viewmodels.tree.record_node import RecordNode



class PermissionRowBuilder:
    DANGEROUS_STYLE: str = "dangerous"

    def build(self, info: PermissionsInfo) -> RecordNode:
        """One flat row per permission of any type; its category is its type."""
        permissions = (*info.permissions, *info.app_ops, *info.custom_permissions)
        rows = tuple(self._row(index, permission) for index, permission in enumerate(permissions))
        return replace(RecordNode.create_root(), children=rows)

    def _row(self, index: int, permission: Permission) -> RecordNode:
        kind = permission.type.value
        return RecordNode(
            iid=f"{kind}:{index}",
            cells=(
                permission.name,
                kind.capitalize(),  # the type of permission (permission, appop or custom)
                permission.level_text,  # the protection level
                permission.origin.value,
                permission.max_sdk or "",
                self._summary(permission),
            ),
            category=kind,
            style=self.DANGEROUS_STYLE if permission.is_dangerous else None,
        )

    @staticmethod
    def _summary(permission: Permission) -> str:
        label = permission.label or ""
        return label[:1].upper() + label[1:]  # capitalize the first letter only
