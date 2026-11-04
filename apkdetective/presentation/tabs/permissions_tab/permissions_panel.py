"""
"Permissions" tab: one table with every permission of the APK, built like the
Components tab but without nesting (its rows have no detail, so there are no
expand / collapse buttons). Above it, a row of pills restricts the table to one
type, and the table's own header line carries the filter and the counter:

  * Permissions: requested permissions that Android defines.
  * AppOps: the requested ones with the "appop" protection (special access
    the user grants from Settings: overlays, install packages, all files...).
  * Custom: anything Android doesn't define, whether the app only requests it
    (another app or a library defines it) or declares it itself.

Dangerous permissions are written in the error color.
"""

import tkinter as tk

import ttkbootstrap as ttkb
import ttkbootstrap.constants as ttkb_constants

from apkdetective.domain.entities.manifest.permissions.permission_type_enum import PermissionTypeEnum
from apkdetective.domain.entities.manifest.permissions.permissions_info import PermissionsInfo
from apkdetective.presentation.common.feedback.warning_banner import WarningBanner
from apkdetective.presentation.common.tree.category_pill_bar import CategoryPillBar
from apkdetective.presentation.common.tree.record_table_panel import RecordTablePanel
from apkdetective.presentation.tabs.permissions_tab.permission_row_builder import PermissionRowBuilder
from apkdetective.presentation.viewmodels.appearance.theme_palette import ThemePalette
from apkdetective.presentation.viewmodels.tree.tree_column import TreeColumn


class PermissionsPanel(ttkb.Frame):
    # Columns share the width in proportion to their weights (the permission name and the
    # summary get twice as much as the others). If the window is too narrow for the minimum
    # widths, the table scrolls horizontally instead.
    _NAME = TreeColumn(
        "#0",
        "Permission",
        min_width=280,
        weight=4,
        tooltip="Name of the permission."
    )
    _TYPE = TreeColumn(
        "type",
        "Type",
        min_width=100,
        weight=1,
        tooltip="Type of the permission: permission, appops or custom."
    )
    _LEVEL = TreeColumn(
        "level",
        "Level",
        min_width=150,
        weight=2,
        tooltip="Protection level of the permission. The dangerous ones are highlighted."
    )
    _ORIGIN = TreeColumn(
        "origin",
        "Origin",
        min_width=100,
        weight=2,
        tooltip="Whether the app declares the permission itself, requests it, or both."
    )
    _MAX_SDK = TreeColumn(
        "max_sdk",
        "Max SDK",
        min_width=75,
        weight=1,
        tooltip="Last Android API level on which the app requests the permission (android:maxSdkVersion)."
    )
    _SUMMARY = TreeColumn(
        "summary",
        "Summary",
        min_width=220,
        weight=3,
        tooltip="What the permission is for, in plain words."
    )

    _COLUMNS: tuple[TreeColumn, ...] = (_NAME, _TYPE, _LEVEL, _ORIGIN, _MAX_SDK, _SUMMARY)

    # Pill label of each permission type (the category of a row is the value of its type).
    _PILL_LABELS: dict[str, str] = {
        PermissionTypeEnum.PERMISSION.value: "Permissions",
        PermissionTypeEnum.APPOPS.value: "AppOps",
        PermissionTypeEnum.CUSTOM.value: "Custom",
    }

    def __init__(
        self,
        parent: ttkb.Notebook,
        palette: ThemePalette,
        row_builder: PermissionRowBuilder | None = None,
    ) -> None:
        super().__init__(parent)
        self._row_builder: PermissionRowBuilder = row_builder or PermissionRowBuilder()

        self._table: RecordTablePanel = RecordTablePanel(
            self,
            palette,
            self._COLUMNS,
            item_noun="permissions",
            empty_text="No permissions requested or declared.",
            row_styles={PermissionRowBuilder.DANGEROUS_STYLE: lambda current: current.danger_text},
            toolbar_row=True,
            bootstyle=ttkb_constants.PRIMARY
        )
        self._table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._banner: WarningBanner = WarningBanner(self, palette, self._table)

        toolbar = self._table.toolbar  # the table's first line, where the pills go
        assert toolbar is not None
        self._pills: CategoryPillBar = CategoryPillBar(
            toolbar,
            self._PILL_LABELS,
            on_select=self._table.set_category,
        )

    def apply_palette(self, palette: ThemePalette) -> None:
        self._table.apply_palette(palette)
        self._banner.apply_palette(palette)
        self._pills.restyle()

    def show_warnings(self, messages: list[str]) -> None:
        self._banner.show(messages)

    def clear(self) -> None:
        self._banner.show(())
        self._table.clear()
        self._pills.reset(())

    def render(self, info: PermissionsInfo) -> None:
        root = self._row_builder.build(info)
        self._table.show(root)
        self._pills.reset(row.category for row in root.children)
