"""
A tooltip for the column headings of a table: it appears when the pointer rests on the heading of a column
that has a description (TreeColumn.tooltip), and not over the rows or the other headings.

It is a ttkbootstrap ToolTip (so it looks like the other tooltips of the app) whose triggers are replaced:
the base one reacts to the pointer entering the widget, and here it has to react to it being on a heading.
"""

import tkinter as tk
from collections.abc import Sequence
from tkinter import ttk

import ttkbootstrap as ttkb

from apkviewer.presentation.viewmodels.tree.tree_column import TreeColumn


class HeadingToolTip(ttkb.ToolTip):
    DELAY_MS: int = 500  # headings are crossed all the time on the way to something else

    def __init__(self, tree: ttk.Treeview, columns: Sequence[TreeColumn]) -> None:
        self._tree: ttk.Treeview = tree
        # identify_column() numbers the columns as they are displayed: the tree column "#0" and then the others.
        self._column_ids: list[str] = ["#0"] + [column.id for column in columns if column.id != "#0"]
        self._descriptions: dict[str, str] = {column.id: column.tooltip for column in columns if column.tooltip}
        self._shown_for: str | None = None  # the column the tooltip is waiting for, or showing
        super().__init__(tree, text="", delay=self.DELAY_MS)

    def enter(self, event: tk.Event | None = None) -> None:
        """Entering the table is not enough to show anything: see move_tip."""

    def leave(self, event: tk.Event | None = None) -> None:
        self._shown_for = None
        super().leave(event)

    def move_tip(self, *args: tk.Event) -> None:
        column_id = self._heading_column(args[0]) if args else None
        if column_id != self._shown_for:
            self.leave()  # moved to another heading, or out of the headings: the previous one goes away
            if column_id is not None:
                self._shown_for = column_id
                self.configure(text=self._descriptions[column_id])
                self.schedule()
        else:
            super().move_tip(*args)  # same heading: the tooltip, if it is already shown, follows the pointer

    def _heading_column(self, event: tk.Event) -> str | None:
        """The column whose heading is under the pointer, if it has a description."""
        if self._tree.identify_region(event.x, event.y) != "heading":
            return None
        position = int(self._tree.identify_column(event.x).lstrip("#") or 0)
        column_id = self._column_ids[position] if position < len(self._column_ids) else None
        return column_id if column_id in self._descriptions else None
