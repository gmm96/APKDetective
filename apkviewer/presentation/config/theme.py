"""
Fonts shared across widgets and the numbers the palette is derived with.
Colors live in ThemePalette (see apkviewer.presentation.appearance.theme_palette_builder).
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



# --- Readability ---
# What ThemePaletteBuilder derives the palette's text, icon and band colors with.
MIN_TEXT_CONTRAST: float = 4.5      # WCAG AA for normal text
MIN_COMMENT_CONTRAST: float = 4.0   # XML comments are meant to be dimmer than the code (they are italic too)
MARKED_LINE_TINT: float = 0.25      # share of the theme's primary color laid over the input background
FOLDER_ROW_TINT: float = 0.12       # same, for the folder rows (a quieter band: there are many of them)
DISABLED_TEXT_AMOUNT: float = 0.6   # share of the text color kept when dimming disabled text
MUTED_TEXT_AMOUNT: float = 0.7      # share of the text color kept in muted text (captions, notes)


# --- Colors ---
# Baselines per color scheme: ThemePaletteBuilder nudges each one on the themes where it does not
# reach the minimum contrast, so these only set the hue and the general feel.
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
