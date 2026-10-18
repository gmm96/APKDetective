"""
Applies a palette to the classic Tk widgets that ttk theming does not
reach (Text and Menu).
"""

import tkinter as tk

from .theme_palette import ThemePalette


class TkWidgetStyler:
    @staticmethod
    def style_text(widget: tk.Text, palette: ThemePalette) -> None:
        widget.configure(
            background=palette.background,
            foreground=palette.foreground,
            insertbackground=palette.input_foreground,
            selectbackground=palette.select_background,
            selectforeground=palette.select_foreground,
            inactiveselectbackground=palette.input_background,
            highlightbackground=palette.background,
            highlightcolor=palette.foreground,
        )

    @staticmethod
    def style_menu(menu: tk.Menu, palette: ThemePalette) -> None:
        menu.configure(
            background=palette.background,
            foreground=palette.foreground,
            activebackground=palette.input_background,
            activeforeground=palette.select_foreground,
            disabledforeground=palette.background,
            selectcolor=palette.select_foreground,
        )
