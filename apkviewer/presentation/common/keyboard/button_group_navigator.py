"""
Makes a block of buttons (the filter pills, "Collapse all" / "Expand all"...) work like one control for the keyboard:
Tab enters the block on one of its buttons and the next Tab leaves it, and the Left / Right arrows move the focus
between its buttons. This is the usual "roving focus" of toolbars and radio groups.

Which button Tab stops at is decided each time, not stored: the one that has the focus, else the selected one
(a pill), else the last one that had it, else the first. Disabled buttons are skipped by the arrows and never
stop Tab, and neither does any button while the block is not on screen (a tab that is not the selected one).
"""

import tkinter as tk
from collections.abc import Sequence
from functools import partial
from tkinter import ttk

from apkviewer.presentation.common.keyboard.keyboard_focus_announcer import KeyboardFocusAnnouncer


class ButtonGroupNavigator:
    def __init__(self, buttons: Sequence[ttk.Widget]) -> None:
        self._buttons: tuple[ttk.Widget, ...] = tuple(buttons)
        self._last_focused: tk.Misc | None = None
        # A takefocus that is a command is asked, with the window path, every time Tab looks for a stop.
        is_tab_stop = self._buttons[0].register(self._is_tab_stop)
        for button in self._buttons:
            button["takefocus"] = is_tab_stop
            button.bind("<FocusIn>", self._remember, add="+")
            button.bind("<Left>", partial(self._move, -1), add="+")
            button.bind("<Right>", partial(self._move, 1), add="+")

    # --- Tab ---------------------------------------------------------------------

    def _is_tab_stop(self, path: str) -> int:
        stop = self._tab_stop()
        return int(stop is not None and str(stop) == path)

    def _tab_stop(self) -> ttk.Widget | None:
        available = [button for button in self._buttons if self._is_available(button)]
        focused = self._buttons[0].tk.call("focus")
        candidates = (
            [button for button in available if str(button) == focused],
            [button for button in available if button.instate(["selected"])],
            [button for button in available if button is self._last_focused],
            available,
        )
        return next((found[0] for found in candidates if found), None)

    def _remember(self, event: tk.Event) -> None:
        self._last_focused = event.widget

    # --- Arrows ------------------------------------------------------------------

    def _move(self, step: int, event: tk.Event) -> str:
        index = self._buttons.index(event.widget) + step
        while 0 <= index < len(self._buttons):
            target = self._buttons[index]
            if self._is_available(target):
                target.focus_set()
                KeyboardFocusAnnouncer.announce(target)
                break
            index += step
        return "break"  # also at the ends: the arrow keys are not for anything else here

    @staticmethod
    def _is_available(button: ttk.Widget) -> bool:
        # A takefocus that is a command replaces Tk's own checks, so being on screen has to be checked here.
        return bool(button.winfo_viewable()) and button.instate(["!disabled"])
