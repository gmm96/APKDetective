"""
UI font constants shared across widgets.
"""


class FontConfig:
    FONT_TITLE: tuple[str, int, str] = ("Helvetica", 20, "bold")
    FONT_SUBTITLE: tuple[str, int] = ("Helvetica", 12)
    FONT_MONO: tuple[str, int] = ("Consolas", 10)
    FONT_MONO_SMALL: tuple[str, int] = ("Consolas", 9)
    FONT_MONO_SMALL_ITALIC: tuple[str, int, str] = FONT_MONO_SMALL + ("italic",)
