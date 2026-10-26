"""
Tells when the whole application has lost the keyboard focus (click on
another window, Alt+Tab, ...), which is what makes any open popup menu
have to go away.
"""

import tkinter as tk
from collections.abc import Callable, Iterable


class AppFocusWatcher:
    # Delay before checking whether the whole app lost focus: focus briefly
    # moves between the window and its own popups, so checking immediately
    # would produce false positives.
    _CHECK_DELAY_MS: int = 100

    def __init__(
        self,
        widget: tk.Misc,
        on_lost: Callable[[], None],
        widget_classes: Iterable[str] = (),
    ) -> None:
        """
        `on_lost`: called whenever the application is found to have no focus; it must be idempotent.
        `widget_classes`: widget classes whose own <FocusOut> must be watched too. While a menu of
        the window's menu bar is open the focus is on that menu, a window of its own that does
        not report to the toplevel, so leaving the application is only seen there.
        """
        self._toplevel: tk.Misc = widget.winfo_toplevel()
        self._on_lost: Callable[[], None] = on_lost
        self._toplevel.bind("<FocusOut>", self._on_focus_out, add="+")
        for widget_class in widget_classes:
            self._toplevel.bind_class(widget_class, "<FocusOut>", self._on_focus_out, add="+")

    def _on_focus_out(self, _event: tk.Event) -> None:
        self._toplevel.after(self._CHECK_DELAY_MS, self._check)

    def _check(self) -> None:
        if not self._app_has_focus():
            self._on_lost()

    def _app_has_focus(self) -> bool:
        # Ask Tk directly: `Misc.focus_displayof()` tries to resolve the
        # returned name to a widget and raises KeyError for internal windows
        # (e.g. '#!menu'), which would abort this very check.
        return bool(self._toplevel.tk.call("focus", "-displayof", str(self._toplevel)))
