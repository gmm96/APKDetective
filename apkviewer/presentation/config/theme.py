"""
Fonts shared across widgets. Colors live in the palettes
(see apkviewer.presentation.appearance.palettes).
"""

from apkviewer.presentation.viewmodels.theme_custom_colors import ThemeCustomColors
from apkviewer.domain.entities.color_scheme import ColorScheme


# --- Fonts ---
FONT_TITLE: tuple[str, int, str] = ("Helvetica", 20, "bold")
FONT_SUBTITLE: tuple[str, int] = ("Helvetica", 12)
FONT_MONO: tuple[str, int] = ("Consolas", 10)
FONT_MONO_SMALL: tuple[str, int] = ("Consolas", 9)
FONT_MONO_SMALL_ITALIC: tuple[str, int, str] = FONT_MONO_SMALL + ("italic",)


# --- Theme ---
THEMES: list[str] = [
    "bootstrap",
    "pydata",
    "nord",
    "solarized",
    "catppuccin",
    "gruvbox",
    "dracula",
    "tokyo-night",
    "one",
    "everforest",
    "vapor",
    "minty",
    "pulse",
    "united",
    "sandstone",
]



# --- Colors ---
LIGHT_CUSTOM_COLORS = ThemeCustomColors(
    xml_tag="#0033B3",
    xml_attr="#871094",
    xml_value="#067D17",
    xml_comment="#8C8C8C",
)
DARK_CUSTOM_COLORS = ThemeCustomColors(
    xml_tag="#6fa8ff",
    xml_attr="#c792ea",
    xml_value="#a5d6a7",
    xml_comment="#8a8a8a",
)
CUSTOM_COLORS: dict[ColorScheme, ThemeCustomColors] = {
    ColorScheme.LIGHT: LIGHT_CUSTOM_COLORS,
    ColorScheme.DARK: DARK_CUSTOM_COLORS,
}
