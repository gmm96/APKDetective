import tkinter as tk
from collections.abc import Callable

from apkviewer.presentation.common.action_icon_overlay import ActionIconOverlay


class ClearIconOverlay(ActionIconOverlay):
    """Clear icon shown over a text field while the variable bound to it has text."""

    _ICON: str = "x-circle"

    def __init__(
        self,
        target: tk.Widget,
        variable: tk.StringVar,
        icon_color: str,
        on_clear: Callable[[], None] | None = None,
        background: str | None = None,
    ) -> None:
        self._variable: tk.StringVar = variable
        self._on_clear: Callable[[], None] | None = on_clear
        super().__init__(target, self._ICON, icon_color, background)
        variable.trace_add("write", lambda *_args: self.refresh())
        self.refresh()

    def update_colors(self, icon_color: str | None = None, background: str | None = None) -> None:
        self._icon.configure(icon_color=icon_color, background=background)

    # --- Visibility ----------------------------------------------------------------------------

    def refresh(self) -> None:
        if self._variable.get():
            self._icon.show()
        else:
            self._icon.hide()

    # --- Clear Action ----------------------------------------------------------------------------

    def clear(self, _event: tk.Event | None = None) -> str:
        self._variable.set("")
        self._target.focus_set()
        if self._on_clear is not None:
            self._on_clear()
        return "break"

    def _activate(self, event: tk.Event | None = None) -> str:
        return self.clear(event)
