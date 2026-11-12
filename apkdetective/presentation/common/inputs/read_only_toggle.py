"""
A toggle button that only shows a yes/no value: it can't be toggled, pressed, focused or highlighted. It is what the
flags and the lists of architectures and densities of a form are made of.
"""

import tkinter as tk

import ttkbootstrap as ttkb

from apkdetective.presentation.viewmodels.appearance.theme_palette import ThemePalette


class ReadOnlyToggle(ttkb.Checkbutton):
    # ttk styles derived from "Toolbutton" (they keep its layout and padding) under names that no ttkbootstrap
    # color nor the filter pills ("primary.Outline.Toolbutton") use, so neither is touched.
    _ON_STYLE: str = "ReadOnlyOn.Toolbutton"
    _OFF_STYLE: str = "ReadOnlyOff.Toolbutton"

    def __init__(self, parent: tk.Misc, text: str, value: bool) -> None:
        """`value`: on (accent border) or off (quiet); see `configure_styles`."""
        super().__init__(parent, text=text, takefocus=False, style=self._ON_STYLE if value else self._OFF_STYLE)
        # The class bindings are what make a Checkbutton react to the mouse and the keyboard.
        self.bindtags(tuple(tag for tag in self.bindtags() if tag != self.winfo_class()))

    @classmethod
    def configure_styles(cls, palette: ThemePalette) -> None:
        """
        Set the colors of the on and off styles: an outlined button whose border carries the theme's accent while
        its text stays the normal text color, or, when off, border and text both quiet. ttkbootstrap's own
        toolbutton styles tie the border and the text to one color, hence these two of their own.

        ttk keeps the settings of a style per theme, so this has to be called again whenever the theme changes.
        """
        style = ttkb.Style()
        style.configure(
            cls._ON_STYLE,
            foreground=palette.foreground,
            background=palette.background,
            bordercolor=palette.primary,
            darkcolor=palette.background,   # as the border of the outline toolbuttons: no bevel
            lightcolor=palette.background,
            focuscolor=palette.foreground,
        )
