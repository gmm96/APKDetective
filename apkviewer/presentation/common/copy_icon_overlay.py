import tkinter as tk
from collections.abc import Callable

import ttkbootstrap.constants as ttkb_constants

from apkviewer.presentation.common.action_icon_overlay import ActionIconOverlay


class CopyIconOverlay(ActionIconOverlay):
    """Copy icon shown over any widget while the pointer is over it."""

    _FEEDBACK_MS: int = 1500
    _ICON_IDLE: str = "copy"
    _ICON_COPIED: str = "check-circle-fill"

    def __init__(
        self,
        target: tk.Widget,
        get_text: Callable[[], str],
        icon_style: str = ttkb_constants.INFO,
        active_icon_style: str = ttkb_constants.SUCCESS,
        background: str | None = None,
        top_offset: int | None = None,
        right_offset: int | None = None,
    ) -> None:
        self._get_text: Callable[[], str] = get_text
        self._icon_style: str = icon_style
        self._active_icon_style: str = active_icon_style
        self._restore_job: str | None = None
        super().__init__(target, self._ICON_IDLE, icon_style, background, top_offset, right_offset)

        for widget in (target, self._icon.widget):
            widget.bind("<Enter>", self._schedule_refresh, add="+")
            widget.bind("<Leave>", self._schedule_refresh, add="+")
        self.refresh()

    def update_colors(
        self,
        icon_style: str | None = None,
        active_icon_style: str | None = None,
        background: str | None = None,
    ) -> None:
        if icon_style is not None:
            self._icon_style = icon_style
        if active_icon_style is not None:
            self._active_icon_style = active_icon_style

        copied = self._restore_job is not None
        self._icon.configure(
            icon_name=self._ICON_COPIED if copied else self._ICON_IDLE,
            icon_style=self._active_icon_style if copied else self._icon_style,
            background=background,
        )

    # --- Visibility ----------------------------------------------------------------------------

    def refresh(self) -> None:
        if not (self._target.winfo_exists() and self._icon.widget.winfo_exists()):
            return
        if self._pointer_inside():
            self._icon.show()
        else:
            self._icon.hide()

    def _schedule_refresh(self, _event: tk.Event) -> None:
        self._target.after_idle(self.refresh)

    def _pointer_inside(self) -> bool:
        x, y = self._target.winfo_pointerxy()
        left, top = self._target.winfo_rootx(), self._target.winfo_rooty()
        return (
            left <= x < left + self._target.winfo_width()
            and top <= y < top + self._target.winfo_height()
        )

    # --- Copy Action -----------------------------------------------------------------------------

    def copy(self, _event: tk.Event | None = None) -> str:
        self._target.clipboard_clear()
        self._target.clipboard_append(self._get_text())

        if self._restore_job is not None:
            self._target.after_cancel(self._restore_job)
        self._restore_job = self._target.after(self._FEEDBACK_MS, self._restore_icon)

        self.update_colors()
        return "break"

    def _activate(self, event: tk.Event | None = None) -> str:
        return self.copy(event)

    def _restore_icon(self) -> None:
        self._restore_job = None
        if self._icon.widget.winfo_exists():
            self.update_colors()
