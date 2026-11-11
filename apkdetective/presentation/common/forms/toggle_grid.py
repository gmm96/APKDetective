"""
A block of read-only toggles of the same width, laid out in as many columns as fit. It is what a form row
uses to show a fixed set of options of which only some are on (e.g. the architectures of an APK).

Like FormSection, it only lays out again when the number of columns changes, so resizing the window costs
nothing while the toggles keep the same shape.
"""

import tkinter as tk
from collections.abc import Callable, Sequence

import ttkbootstrap as ttkb


class ToggleGrid(ttkb.Frame):
    GAP_PX: int = 6

    def __init__(
        self,
        parent: tk.Misc,
        toggles: Sequence[tuple[str, bool]],
        toggle_factory: Callable[[tk.Misc, str, bool], tk.Widget],
    ) -> None:
        """
        `toggles`: (text, is on) of each toggle, in display order.
        `toggle_factory`: builds one read-only toggle as a child of the widget it is given.
        """
        super().__init__(parent)
        self._toggles: tuple[tk.Widget, ...] = tuple(toggle_factory(self, text, on) for text, on in toggles)
        self._width: int = 0
        self._columns: int = 0  # 0: not laid out yet
        self.bind("<Configure>", self._on_resize, add="+")

    def _on_resize(self, event: tk.Event) -> None:
        # Only a change of WIDTH matters: laying the toggles out changes the height, which would
        # otherwise trigger this handler again.
        if event.width != self._width:
            self._width = event.width
            self._apply_layout()

    def _apply_layout(self) -> None:
        if not self._toggles or self._width <= 1:
            return  # no size yet: the first <Configure> lays it out
        columns = self._columns_for(self._width)
        if columns == self._columns:
            return
        self._columns = columns
        for column in range(len(self._toggles)):
            self.columnconfigure(column, weight=0, uniform="")  # clear the previous layout
        for column in range(columns):
            self.columnconfigure(column, weight=1, uniform="toggles")
        for index, toggle in enumerate(self._toggles):
            row, column = divmod(index, columns)
            toggle.grid(
                row=row,
                column=column,
                sticky="ew",
                padx=(0 if column == 0 else self.GAP_PX, 0),
                pady=(0 if row == 0 else self.GAP_PX, 0),
            )

    def _columns_for(self, width: int) -> int:
        """As many columns as fit with every toggle as wide as the widest one (at least one)."""
        toggle_width = max(toggle.winfo_reqwidth() for toggle in self._toggles)
        fitting = (width + self.GAP_PX) // (toggle_width + self.GAP_PX)
        return max(1, min(len(self._toggles), fitting))
