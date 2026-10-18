"""
Read-only text field with a copy icon at its right end. The icon only
shows while the pointer is over the field.
"""

import tkinter as tk

import ttkbootstrap.constants as ttkb_constants

from apkviewer.presentation.common.copy_icon_overlay import CopyIconOverlay
from apkviewer.presentation.common.icon_entry import IconEntry


class CopyableEntry(IconEntry):
    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        icon_style: str = ttkb_constants.INFO,
        active_icon_style: str = ttkb_constants.SUCCESS,
        background: str | None = None,
        font: tuple | None = None,
    ) -> None:
        options = {} if font is None else {"font": font}
        super().__init__(parent, **options)
        self.insert(0, text)
        self.configure(state="readonly")
        self.overlay: CopyIconOverlay = CopyIconOverlay(
            target=self,
            get_text=lambda: text,
            icon_style=icon_style,
            active_icon_style=active_icon_style,
            background=background,
        )

    @property
    def entry(self) -> "CopyableEntry":
        """Kept for compatibility: the field used to be a frame wrapping an inner entry."""
        return self

    def update_colors(
        self,
        icon_style: str | None = None,
        active_icon_style: str | None = None,
        background: str | None = None,
    ) -> None:
        """Propagates theme color updates to the entry style and the overlay."""
        self.configure_entry_style()
        self.overlay.update_colors(
            icon_style=icon_style,
            active_icon_style=active_icon_style,
            background=background,
        )
