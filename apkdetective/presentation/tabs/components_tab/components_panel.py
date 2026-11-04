"""
"Components" tab: one table with every declared component. Above it, a row
of pills restricts the table to one kind (see CategoryPillBar) and the
table's own header line carries the filter, the counter and the expand /
collapse buttons, exactly as in the Files tab. Each component expands to
show its properties and intent filters.
"""

import tkinter as tk

import ttkbootstrap as ttkb
import ttkbootstrap.constants as ttkb_constants

from apkdetective.domain.entities.manifest.components.declared_components import DeclaredComponents
from apkdetective.presentation.common.feedback.warning_banner import WarningBanner
from apkdetective.presentation.common.tree.category_pill_bar import CategoryPillBar
from apkdetective.presentation.common.tree.record_table_panel import RecordTablePanel
from apkdetective.presentation.tabs.components_tab.component_tree_builder import ComponentTreeBuilder
from apkdetective.presentation.viewmodels.appearance.theme_palette import ThemePalette
from apkdetective.presentation.viewmodels.tree.tree_column import TreeColumn


class ComponentsPanel(ttkb.Frame):
    _COLUMNS: tuple[TreeColumn, ...] = (
        TreeColumn(
            "#0",
            "Name",
            width=460,
            min_width=220,
            stretch=True,
            tooltip="Class name of the component. A relative name in the manifest is completed with the package name."
        ),
        TreeColumn(
            "type",
            "Type",
            width=110,
            min_width=80,
            tooltip="Kind of component: activity, activity alias, service, receiver or provider."
        ),
        TreeColumn(
            "exported",
            "Exported",
            width=120,
            min_width=90,
            tooltip="Whether other apps can use the component. \"implicit\": android:exported is not declared, "
                    "so Android's default rules apply. \"unknown\": it could not be determined."
        ),
        TreeColumn(
            "permission",
            "Permission",
            width=260,
            min_width=100,
            stretch=True,
            tooltip="Permission that another app must hold to use the component, if the manifest requires one."
        ),
    )

    def __init__(
        self,
        parent: ttkb.Notebook,
        palette: ThemePalette,
        tree_builder: ComponentTreeBuilder | None = None,
    ) -> None:
        super().__init__(parent)
        self._tree_builder: ComponentTreeBuilder = tree_builder or ComponentTreeBuilder()

        self._table: RecordTablePanel = RecordTablePanel(
            self,
            palette,
            self._COLUMNS,
            item_noun="components",
            empty_text="No components declared.",
            toolbar_row=True,
            expand_buttons=True,
            bootstyle=ttkb_constants.PRIMARY
        )
        self._table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._banner: WarningBanner = WarningBanner(self, palette, self._table)

        toolbar = self._table.toolbar  # the table's first line; its buttons are already at the right
        assert toolbar is not None
        self._pills: CategoryPillBar = CategoryPillBar(
            toolbar,
            dict(ComponentTreeBuilder.GROUPS),
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

    def render(self, components: DeclaredComponents) -> None:
        root = self._tree_builder.build_components(components)
        self._table.show(root)
        self._pills.reset(row.category for row in root.children)
