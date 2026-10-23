"""
Measures the label texts of a form so every section can align its values on
the same column. Each text is measured once, with one font object, and the
result is kept: loading another APK shows the same labels again, and resizing
the window never measures anything.
"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


class LabelWidthMeter:
    def __init__(self, master: tk.Misc, extra_px: int = 0) -> None:
        """`extra_px`: margin added to the widest text."""
        font_spec = ttk.Style(master).lookup("TLabel", "font") or "TkDefaultFont"
        self._font: tkfont.Font = tkfont.Font(root=master, font=font_spec)
        self._extra_px: int = extra_px
        self._widest_px: int = 0
        self._measured: dict[str, int] = {}

    @property
    def width_px(self) -> int:
        """The widest registered text plus the margin; 0 while there is none."""
        return self._widest_px + self._extra_px if self._widest_px else 0

    def register(self, text: str) -> None:
        width = self._measured.get(text)
        if width is None:
            width = self._measured[text] = self._font.measure(text)
        self._widest_px = max(self._widest_px, width)

    def reset(self) -> None:
        """Forgets the registered texts (not their measures: the font does not change)."""
        self._widest_px = 0
