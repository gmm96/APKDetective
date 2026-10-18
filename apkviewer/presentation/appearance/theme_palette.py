"""
Every color the application needs that the ttk theme cannot provide by
itself (classic Tk widgets, text tags, tinted icons, status messages).
"""

from dataclasses import dataclass

from apkviewer.presentation.viewmodels.theme_custom_colors import ThemeCustomColors


@dataclass(frozen=True)
class ThemePalette(ThemeCustomColors):
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
