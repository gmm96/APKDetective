"""
A row of pills (mutually exclusive toolbuttons) that restricts a table to one
category of its rows. The first pill, "All", removes the restriction. Each
pill shows how many rows its category has and a category with no rows is
dimmed instead of opening an empty view.

It knows nothing about the table: it reports the choice through a callback
and is placed in the toolbar row a RecordTablePanel offers.

For the keyboard the pills are one block: Tab stops on one of them and the
arrow keys move between them.
"""

import tkinter as tk
from collections import Counter
from collections.abc import Callable, Iterable, Mapping

import ttkbootstrap as ttkb
import ttkbootstrap.constants as ttkb_constants

from apkdetective.presentation.appearance.toolbutton_focus_ring import ToolbuttonFocusRing
from apkdetective.presentation.common.keyboard.button_group_navigator import ButtonGroupNavigator


class CategoryPillBar:
    _ALL: str = "all"
    _STYLE: str = f"{ttkb_constants.PRIMARY} {ttkb_constants.TOOLBUTTON} {ttkb_constants.OUTLINE}"

    def __init__(
        self,
        parent: tk.Misc,
        categories: Mapping[str, str],
        on_select: Callable[[str | None], None],
    ) -> None:
        """
        `categories`: category key -> label of its pill ("All" is added in front).
        `on_select`: called with the chosen category, or None for "All".
        """
        self._on_select: Callable[[str | None], None] = on_select
        self._selected: tk.StringVar = tk.StringVar(master=parent, value=self._ALL)
        self._labels: dict[str, str] = {self._ALL: "All", **categories}
        self._pills: dict[str, ttkb.Radiobutton] = {}
        for key, label in self._labels.items():
            pill = ttkb.Radiobutton(
                parent,
                text=label,
                value=key,
                variable=self._selected,
                style=self._STYLE,
                command=self._on_pill_selected,
            )
            pill.pack(side=tk.LEFT, padx=(0, 4))
            self._pills[key] = pill
        self._block: ButtonGroupNavigator = ButtonGroupNavigator(list(self._pills.values()))
        self.restyle()
        self.reset(())

    # --- Public API ------------------------------------------------------------

    def reset(self, row_categories: Iterable[str | None]) -> None:
        """
        New data: go back to "All" and count the rows of each category (one entry per row;
        rows without category only count for "All"). The callback is not called.
        """
        counts = Counter(category for category in row_categories if category is not None)
        total = sum(counts.values())
        self._selected.set(self._ALL)
        for key, pill in self._pills.items():
            count = total if key == self._ALL else counts[key]
            pill.configure(
                text=f"{self._labels[key]} ({count})",
                bootstyle=self._STYLE,
                state=tk.NORMAL if count else tk.DISABLED,
            )

    def restyle(self) -> None:
        """The style of a toolbutton has no focus ring: add it again after every theme change."""
        ToolbuttonFocusRing.apply(str(self._pills[self._ALL].cget("style")))

    # --- Internals ---------------------------------------------------------------

    def _on_pill_selected(self) -> None:
        key = self._selected.get()
        self._on_select(None if key == self._ALL else key)
