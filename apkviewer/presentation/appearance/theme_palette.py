"""
Every color the application needs that the ttk theme cannot provide by
itself (classic Tk widgets, text tags, tinted icons, status messages).

The first group comes straight from the ttkbootstrap theme. The second one is
derived from it (see ThemePaletteBuilder) so it stays readable on any theme:
the theme's accents are meant for fills and buttons, and several of them are
too faint to be used as text or as a thin icon.
"""

from dataclasses import dataclass

from apkviewer.presentation.viewmodels.color_pair import ColorPair
from apkviewer.presentation.viewmodels.theme_custom_colors import ThemeCustomColors


@dataclass(frozen=True)
class ThemePalette(ThemeCustomColors):
    # --- From the ttkbootstrap theme ---
    primary: str
    secondary: str
    success: str
    info: str
    warning: str
    danger: str
    light: str
    dark: str
    background: str
    foreground: str
    select_background: str
    select_foreground: str
    border: str
    input_background: str
    input_foreground: str
    active: str

    # --- Derived from it ---
    muted_text: str      # quiet text: captions, notes, the clear icon (neutral: not every theme's secondary is)
    info_text: str       # info as text (status bar)
    primary_icon: str    # the theme's primary as an icon color (copy icon); only nudged if it is too faint
    success_text: str    # success as text or icon (status bar, "copied" icon)
    danger_text: str     # danger as text (errors, dangerous permissions)
    disabled_text: str   # disabled menu entries
    marked_line: ColorPair   # the line marked with a click inside a list field
    folder_row: ColorPair    # the folder rows of the Files tree
    chip_success: ColorPair
    chip_danger: ColorPair
    chip_neutral: ColorPair
    chip_muted: ColorPair
