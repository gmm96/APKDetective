"""
Wraps a ttkb.Scrollbar so it hides itself (via grid_remove) whenever the
whole content is already visible, and re-grids it otherwise. Bind its
`scroll_command` method to a widget's xscrollcommand/yscrollcommand.

Whether the bar is shown is read from the grid manager (`winfo_manager`),
never from `winfo_ismapped`. A bar that is gridded but not mapped yet (its
tab is hidden, the geometry pass is still pending...) reports "not mapped",
and trusting that turned an "everything fits" notification into a no-op and
left the bar stuck on screen. It also means that the bar is only touched when
its visibility really changes, instead of being re-gridded on every report.
"""

from typing import Any

import ttkbootstrap as ttkb


class AutoHideScrollbar:
    # Tk may report 0.9999999 instead of 1 once a fraction has been rounded.
    _EPSILON: float = 1e-6

    def __init__(self, scrollbar: ttkb.Scrollbar, grid_kwargs: dict[str, Any] | None = None) -> None:
        """
        `grid_kwargs`: the options the bar is gridded with when it has to be shown. Empty (or
        None) restores the ones it already had, which only works for a bar gridded before.
        """
        self._scrollbar: ttkb.Scrollbar = scrollbar
        self._grid_kwargs: dict[str, Any] = grid_kwargs or {}

    def scroll_command(self, first: float | str, last: float | str) -> None:
        if float(first) <= self._EPSILON and float(last) >= 1.0 - self._EPSILON:
            self._hide()
        else:
            self._show()
        self._scrollbar.set(first, last)

    def _is_shown(self) -> bool:
        return self._scrollbar.winfo_manager() == "grid"

    def _show(self) -> None:
        if not self._is_shown():
            self._scrollbar.grid(**self._grid_kwargs)

    def _hide(self) -> None:
        if self._is_shown():
            self._scrollbar.grid_remove()
