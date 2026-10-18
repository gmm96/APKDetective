import tkinter as tk
from collections.abc import Callable
from typing import Any

import ttkbootstrap as ttkb
import ttkbootstrap.constants as ttkb_constants

from apkviewer.presentation.common.clear_icon_overlay import ClearIconOverlay
from apkviewer.presentation.common.icon_entry import IconEntry


class ClearableEntry(IconEntry):
    """Text field with a clear icon at its right end, visible only while the field has text."""

    def __init__(
        self,
        parent: tk.Misc,
        on_clear: Callable[[], None] | None = None,
        icon_style: str = ttkb_constants.SECONDARY,
        background: str | None = None,
        **options: Any,
    ) -> None:
        self._variable: ttkb.StringVar = ttkb.StringVar(master=parent)
        super().__init__(parent, textvariable=self._variable, **options)

        self.overlay: ClearIconOverlay = ClearIconOverlay(
            target=self,
            variable=self._variable,
            on_clear=on_clear,
            icon_style=icon_style,
            background=background,
        )

    def update_colors(self, icon_style: str | None = None, background: str | None = None) -> None:
        self.configure_entry_style()
        self.overlay.update_colors(icon_style=icon_style, background=background)
