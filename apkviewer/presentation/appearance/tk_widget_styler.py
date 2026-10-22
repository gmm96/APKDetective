"""
Applies a palette to the classic Tk widgets that ttk theming does not
reach (Menu). ttkbootstrap already styles Text widgets on its own.
"""

import tkinter as tk

from apkviewer.presentation.viewmodels.appearance.theme_palette import ThemePalette


class TkWidgetStyler:
    @staticmethod
    def style_menu(menu: tk.Menu, palette: ThemePalette) -> None:
        menu.configure(
            background=palette.background,
            foreground=palette.foreground,
            activebackground=palette.select_background,
            activeforeground=palette.select_foreground,
            disabledforeground=palette.disabled_text,
            selectcolor=palette.foreground,
        )
