"""
Builds the neutral placeholder image shown while there is no APK icon (before
loading one, and while it is being analyzed): a question mark, tinted to fit
the active theme.
"""

import tkinter as tk

import ttkbootstrap as ttkb

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.config.layout import ICON_SIZE


class PlaceholderIconFactory:
    _ICON_NAME: str = "question-square-fill"

    def __init__(self, size: tuple[int, int] = ICON_SIZE) -> None:
        self._size: tuple[int, int] = size

    def create(self, palette: ThemePalette) -> tk.PhotoImage:
        # Bootstrap icons are square: draw it as large as fits and center it in the requested box.
        side = min(self._size)
        glyph = ttkb.Icon(self._ICON_NAME, side, palette.muted_text)
        image = tk.PhotoImage(width=self._size[0], height=self._size[1])
        image.tk.call(image.name, "copy", glyph, "-to", (self._size[0] - side) // 2, (self._size[1] - side) // 2)
        return image
