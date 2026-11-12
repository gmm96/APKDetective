"""
UI font constants shared across widgets.
"""


class FontConfig:
    FONT_SIZE: int = 11
    FONT_SIZE_SMALL: int = FONT_SIZE - 1
    FONT_TITLE: tuple[str, int, str] = ("Helvetica", 24, "bold")
    FONT_SUBTITLE: tuple[str, int] = ("Helvetica", 16)
    FONT_MONO: tuple[str, int] = ("Consolas", FONT_SIZE)
    FONT_MONO_SMALL: tuple[str, int] = ("Consolas", FONT_SIZE_SMALL)
    FONT_MONO_SMALL_ITALIC: tuple[str, int, str] = FONT_MONO_SMALL + ("italic",)
