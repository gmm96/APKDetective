"""
"Components" tab: one table with every declared component. Above it, a row
of pills restricts the table to one kind (a kind with no components is
dimmed instead of opening an empty view) and the table's own header line
carries the filter, the counter and the expand / collapse buttons, exactly
as in the Files tab. Each component expands to show its properties and
intent filters.

For the keyboard the pills are one block: Tab stops on one of them and the
arrow keys move between them.
"""

import tkinter as tk

import ttkbootstrap as ttkb
import ttkbootstrap.constants as ttkb_constants

from apkviewer.domain.entities.manifest.components.declared_components import DeclaredComponents
from apkviewer.presentation.appearance.toolbutton_focus_ring import ToolbuttonFocusRing
from apkviewer.presentation.common.keyboard.button_group_navigator import ButtonGroupNavigator
from apkviewer.presentation.viewmodels.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.tree.record_table_panel import RecordTablePanel
from apkviewer.presentation.viewmodels.tree.tree_column import TreeColumn
from apkviewer.presentation.common.feedback.warning_banner import WarningBanner
from apkviewer.presentation.tabs.components_tab.component_tree_builder import ComponentTreeBuilder


class ComponentsPanel(ttkb.Frame):
    _COLUMNS: tuple[TreeColumn, ...] = (
        TreeColumn("#0", "Name", width=460, min_width=220, stretch=True),
        TreeColumn("type", "Type", width=110, min_width=80),
        TreeColumn("exported", "Exported", width=120, min_width=90),
        TreeColumn("permission", "Permission", width=260, min_width=100, stretch=True),
    )
    _ALL: str = "all"
    _PILL_STYLE: str = f"{ttkb_constants.PRIMARY} {ttkb_constants.TOOLBUTTON} {ttkb_constants.OUTLINE}"

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

        self._selected: tk.StringVar = tk.StringVar(value=self._ALL)
        self._pill_labels: dict[str, str] = {self._ALL: "All", **dict(ComponentTreeBuilder.GROUPS)}
        self._pills: dict[str, ttkb.Radiobutton] = {}
        toolbar = self._table.toolbar  # the table's first line; its buttons are already at the right
        assert toolbar is not None
        for key, label in self._pill_labels.items():
            pill = ttkb.Radiobutton(
                toolbar,
                text=label,
                value=key,
                variable=self._selected,
                style=self._PILL_STYLE,
                command=self._on_pill_selected,
            )
            pill.pack(side=tk.LEFT, padx=(0, 4))
            self._pills[key] = pill
        self._pill_block: ButtonGroupNavigator = ButtonGroupNavigator(list(self._pills.values()))
        self._style_pills()
        self._update_pills({})

    def apply_palette(self, palette: ThemePalette) -> None:
        self._table.apply_palette(palette)
        self._banner.apply_palette(palette)
        self._style_pills()

    def show_warnings(self, messages: list[str]) -> None:
        self._banner.show(messages)

    def clear(self) -> None:
        self._banner.show(())
        self._selected.set(self._ALL)
        self._table.set_category(None, refresh=False)
        self._table.clear()
        self._update_pills({})

    def render(self, components: DeclaredComponents) -> None:
        root = self._tree_builder.build_components(components)
        counts: dict[str, int] = {}
        for row in root.children:
            if row.category is not None:
                counts[row.category] = counts.get(row.category, 0) + 1

        self._selected.set(self._ALL)
        self._table.set_category(None, refresh=False)
        self._table.show(root)
        self._update_pills(counts)

    # --- Pills -------------------------------------------------------------------

    def _style_pills(self) -> None:
        # The style of a toolbutton has no focus ring; it is added again after every theme change.
        ToolbuttonFocusRing.apply(str(self._pills[self._ALL].cget("style")))

    def _on_pill_selected(self) -> None:
        key = self._selected.get()
        self._table.set_category(None if key == self._ALL else key)

    def _update_pills(self, counts: dict[str, int]) -> None:
        total = sum(counts.values())
        for key, pill in self._pills.items():
            count = total if key == self._ALL else counts.get(key, 0)
            pill.configure(
                text=f"{self._pill_labels[key]} ({count})",
                bootstyle=self._PILL_STYLE,
                state=tk.NORMAL if count else tk.DISABLED,
            )
