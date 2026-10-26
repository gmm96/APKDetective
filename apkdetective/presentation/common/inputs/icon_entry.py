"""
Base class of the text fields that reserve room at their right end for an icon.
"""

import tkinter as tk
from typing import Any

import ttkbootstrap as ttkb

from apkdetective.presentation.config.layout import FIELD_PADX, FIELD_PADY


class IconEntry(ttkb.Entry):
    ENTRY_STYLE: str = "IconEntry.TEntry"
    ENTRY_ICON_AREA: int = 30  # pixels kept free at the right end of the field's text area

    def __init__(self, parent: tk.Misc, **options: Any) -> None:
        self.configure_entry_style()
        super().__init__(parent, style=self.ENTRY_STYLE, **options)

    @classmethod
    def configure_entry_style(cls) -> None:
        """ttk keeps style settings per theme, so this must be called on initialization and theme changes."""
        ttkb.Style().configure(
            cls.ENTRY_STYLE,
            padding=(FIELD_PADX, FIELD_PADY, cls.ENTRY_ICON_AREA, FIELD_PADY),
        )
