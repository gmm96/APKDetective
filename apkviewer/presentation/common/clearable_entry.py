import tkinter as tk
from collections.abc import Callable
from typing import Any

import ttkbootstrap as ttkb

from apkviewer.presentation.common.clear_icon_overlay import ClearIconOverlay
from apkviewer.presentation.common.icon_entry import IconEntry


class ClearableEntry(IconEntry):
    """Text field with a clear icon at its right end, visible only while the field has text."""

    def __init__(
        self,
        parent: tk.Misc,
        icon_color: str,
        on_clear: Callable[[], None] | None = None,
        background: str | None = None,
        **options: Any,
    ) -> None:
        self._variable: ttkb.StringVar = ttkb.StringVar(master=parent)
        super().__init__(parent, textvariable=self._variable, **options)

        self.overlay: ClearIconOverlay = ClearIconOverlay(
            target=self,
            variable=self._variable,
            icon_color=icon_color,
            on_clear=on_clear,
            background=background,
        )

    def update_colors(
        self,
        icon_color: str | None = None,
        background: str | None = None,
        foreground: str | None = None,
    ) -> None:
        """`foreground`: the color of the text typed in the field."""
        self.configure_entry_style()
        if foreground is not None:
            self.configure(foreground=foreground)
        self.overlay.update_colors(icon_color=icon_color, background=background)
