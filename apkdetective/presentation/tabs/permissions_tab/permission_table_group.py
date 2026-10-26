"""
A titled frame (showing the row count) with one filterable permission table.
The tab's grid gives each group a share of the height in proportion to its rows.
"""

from collections.abc import Sequence

import ttkbootstrap as ttkb

from apkdetective.presentation.viewmodels.appearance.theme_palette import ThemePalette
from apkdetective.presentation.viewmodels.tree.record_node import RecordNode
from apkdetective.presentation.common.tree.record_table_panel import RecordTablePanel
from apkdetective.presentation.viewmodels.tree.tree_column import TreeColumn
from apkdetective.presentation.tabs.permissions_tab.permission_rows import DANGEROUS_STYLE


class PermissionTableGroup:
    _MIN_HEIGHT_WITH_ROWS: int = 170
    _MIN_HEIGHT_EMPTY: int = 95
    _MIN_WEIGHT: int = 4   # a table with rows never gets less than the share of this many rows
    _MAX_WEIGHT: int = 30  # nor more than the share of this many

    def __init__(
        self,
        container: ttkb.Frame,
        row: int,
        title: str,
        columns: Sequence[TreeColumn],
        noun: str,
        empty_text: str,
        palette: ThemePalette,
        bootstyle: str | None = None
    ) -> None:
        self._container: ttkb.Frame = container
        self._row: int = row
        self._title: str = title
        self._frame: ttkb.LabelFrame = ttkb.LabelFrame(container, text=title)
        self._frame.grid(row=row, column=0, sticky="nsew", padx=10, pady=(0, 6))
        self._frame.rowconfigure(0, weight=1)
        self._frame.columnconfigure(0, weight=1)
        self._table: RecordTablePanel = RecordTablePanel(
            self._frame,
            palette,
            columns,
            item_noun=noun,
            empty_text=empty_text,
            row_styles={DANGEROUS_STYLE: lambda current: current.danger_text},
            bootstyle=bootstyle
        )
        self._table.tree.configure(height=3)  # the real height comes from the grid weights
        self._table.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.clear()

    def apply_palette(self, palette: ThemePalette) -> None:
        self._table.apply_palette(palette)

    def show(self, root: RecordNode) -> None:
        count = len(root.children)
        self._table.show(root)
        self._frame.configure(text=f"{self._title} ({count})")
        self._container.rowconfigure(
            self._row,
            weight=min(max(count, self._MIN_WEIGHT), self._MAX_WEIGHT) if count else 0,
            minsize=self._MIN_HEIGHT_WITH_ROWS if count else self._MIN_HEIGHT_EMPTY,
        )

    def clear(self) -> None:
        self._table.clear()
        self._frame.configure(text=self._title)
        self._container.rowconfigure(self._row, weight=0, minsize=self._MIN_HEIGHT_EMPTY)
