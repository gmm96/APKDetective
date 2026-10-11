"""
"Permissions" tab: three plain tables (no tree), each with its own filter:

  * Permissions: requested permissions that Android defines.
  * AppOps: the requested ones with the "appop" protection (special access
    the user grants from Settings: overlays, install packages, all files...).
  * Custom permissions: anything Android doesn't define, whether the app only
    requests it (another app or a library defines it) or declares it itself.

The tables share the tab's height in proportion to their rows. Dangerous
permissions are written in the error color.
"""

import tkinter as tk
from tkinter import ttk

from apkviewer.domain.entities.permission import Permission
from apkviewer.domain.entities.permissions_info import PermissionsInfo
from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.tree.tree_column import TreeColumn
from apkviewer.presentation.common.warning_banner import WarningBanner
from apkviewer.presentation.permissions_tab.permission_rows import PermissionRowBuilder
from apkviewer.presentation.permissions_tab.permission_table_group import PermissionTableGroup

# Columns share the width in proportion to their weights (the permission name and the
# summary get twice as much as the others). If the window is too narrow for the minimum
# widths, the table scrolls horizontally instead.
_NAME = TreeColumn("#0", "Permission", min_width=280, weight=2)
_TYPE = TreeColumn("type", "Type", min_width=150, weight=1)
_ORIGIN = TreeColumn("origin", "Origin", min_width=150, weight=1)
_MAX_SDK = TreeColumn("max_sdk", "Max SDK", min_width=70, weight=1)
_SUMMARY = TreeColumn("summary", "Summary", min_width=220, weight=2)

_STANDARD_COLUMNS: tuple[TreeColumn, ...] = (_NAME, _TYPE, _MAX_SDK, _SUMMARY)
_CUSTOM_COLUMNS: tuple[TreeColumn, ...] = (_NAME, _TYPE, _ORIGIN, _MAX_SDK, _SUMMARY)


class PermissionsPanel(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Notebook,
        palette: ThemePalette,
        row_builder: PermissionRowBuilder | None = None,
    ) -> None:
        super().__init__(parent)
        self._row_builder: PermissionRowBuilder = row_builder or PermissionRowBuilder()

        self._container: ttk.Frame = ttk.Frame(self)
        self._container.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self._container.columnconfigure(0, weight=1)
        self._banner: WarningBanner = WarningBanner(self, palette, before=self._container)

        self._permissions: PermissionTableGroup = PermissionTableGroup(
            self._container, 0, "Permissions", _STANDARD_COLUMNS, "permissions",
            "No Android permissions requested.", palette,
        )
        self._app_ops: PermissionTableGroup = PermissionTableGroup(
            self._container, 1, "AppOps (special access)", _STANDARD_COLUMNS, "app ops",
            "No special-access permissions requested.", palette,
        )
        self._custom: PermissionTableGroup = PermissionTableGroup(
            self._container, 2, "Custom permissions", _CUSTOM_COLUMNS, "custom permissions",
            "No custom permissions requested or declared.", palette,
        )
        self._groups: tuple[PermissionTableGroup, ...] = (self._permissions, self._app_ops, self._custom)

    def apply_palette(self, palette: ThemePalette) -> None:
        self._banner.apply_palette(palette)
        for group in self._groups:
            group.apply_palette(palette)

    def show_warnings(self, messages: list[str]) -> None:
        self._banner.show(messages)

    def clear(self) -> None:
        self._banner.show(())
        for group in self._groups:
            group.clear()

    def render(self, info: PermissionsInfo) -> None:
        self._show(self._permissions, info.permissions, with_origin=False)
        self._show(self._app_ops, info.app_ops, with_origin=False)
        self._show(self._custom, info.custom_permissions, with_origin=True)

    def _show(self, group: PermissionTableGroup, permissions: tuple[Permission, ...], with_origin: bool) -> None:
        group.show(self._row_builder.build(permissions, with_origin))
