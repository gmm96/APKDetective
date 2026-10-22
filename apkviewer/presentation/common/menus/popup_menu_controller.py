"""
Gives a hand-posted tk.Menu the behaviour users expect from any popup menu:

  * it disappears when the user clicks anywhere else in the application;
  * it disappears when the application loses focus (click on another
    window, Alt+Tab, ...);
  * it disappears with Escape;
  * only one popup of the whole application is open at a time.

The menu is shown with `menu.post()` + `focus_set()` (never `tk_popup`, which
relies on a pointer grab that not every platform/window manager honours), so
all the popups share exactly the same, testable mechanism.
"""

import tkinter as tk
from collections.abc import Iterable

from apkviewer.presentation.common.menus.app_focus_watcher import AppFocusWatcher


class PopupMenuController:
    _open_controller: "PopupMenuController | None" = None

    def __init__(
        self,
        widget: tk.Misc,
        menu: tk.Menu,
        ignored_widgets: Iterable[tk.Misc] = ()
    ) -> None:
        """
        `ignored_widgets`: widgets whose own click handling opens/closes this
        menu (e.g. the toolbar button that owns it); clicking them must not
        be treated as "clicked elsewhere".
        """
        self._toplevel: tk.Misc = widget.winfo_toplevel()
        self._menu: tk.Menu = menu
        self._ignored_paths: set[str] = {str(w) for w in ignored_widgets}

        self._toplevel.bind("<Button-1>", self._on_app_click, add="+")
        AppFocusWatcher(self._toplevel, self._close_if_open)
        self._menu.bind("<FocusOut>", lambda _event: self.unpost(), add="+")
        self._menu.bind("<Escape>", lambda _event: self.unpost(), add="+")

    @property
    def is_open(self) -> bool:
        return bool(self._menu.winfo_ismapped())

    @classmethod
    def is_any_open(cls) -> bool:
        """Whether some popup of the application (this one or another) is currently posted."""
        return cls._open_controller is not None

    def post(self, x_root: int, y_root: int) -> None:
        self.close_open_popup()
        PopupMenuController._open_controller = self
        self._menu.post(x_root, y_root)
        # Forcing focus onto the menu is what makes <FocusOut> fire when the
        # user goes somewhere else.
        self._menu.focus_set()

    def unpost(self) -> None:
        self._menu.unpost()
        if PopupMenuController._open_controller is self:
            PopupMenuController._open_controller = None

    @classmethod
    def close_open_popup(cls) -> None:
        if cls._open_controller is not None:
            cls._open_controller.unpost()

    # --- Dismiss handlers ----------------------------------------------------

    def _on_app_click(self, event: tk.Event) -> None:
        if self.is_open and str(event.widget) not in self._ignored_paths:
            self.unpost()

    def _close_if_open(self) -> None:
        if self.is_open:
            self.unpost()
