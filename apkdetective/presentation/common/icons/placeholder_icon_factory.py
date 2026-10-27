"""
Builds the neutral placeholder image shown while there is no APK icon (before
loading one, and while it is being analyzed): a question mark, tinted to fit
the active theme.
"""

import tkinter as tk

import ttkbootstrap as ttkb

from apkdetective.presentation.viewmodels.appearance.theme_palette import ThemePalette


class PlaceholderIconFactory:
    _ICON_NAME: str = "question-square-fill"
    # Launcher icons keep a transparent margin around their artwork (about 79% of the box is visible in
    # the ones seen so far), while this glyph fills almost all of its own box: it is drawn smaller so that
    # swapping the placeholder for the real icon does not look like a jump in size.
    _SIZE_FRACTION: float = 0.85

    def __init__(self, size: tuple[int, int]) -> None:
        self._size: tuple[int, int] = size

    def create(self, palette: ThemePalette) -> tk.PhotoImage:
        image = tk.PhotoImage(width=self._size[0], height=self._size[1])
        glyph = self._render_glyph(image, round(min(self._size) * self._SIZE_FRACTION), palette.muted_text)

        # The glyph is not centered inside its own box (the font leaves uneven margins): center what is visible.
        left, top, right, bottom = self._visible_bounds(glyph)
        visible_width, visible_height = right - left + 1, bottom - top + 1
        image.tk.call(
            image.name, "copy", glyph.name,
            "-from", left, top, right + 1, bottom + 1,
            "-to", (self._size[0] - visible_width) // 2, (self._size[1] - visible_height) // 2,
        )
        return image

    def _render_glyph(self, image: tk.PhotoImage, pixels: int, color: str) -> tk.PhotoImage:
        """
        The glyph as an image about `pixels` wide. ttkbootstrap sizes icons in logical units that grow with the
        display's dpi, while the app icon is always a fixed number of pixels: the size is converted so that
        both stay comparable on any screen, and the copy takes the image's real size so nothing gets cut.
        """
        tcl = image.tk.call
        scale = float(tcl("winfo", "fpixels", ".", "1i")) / 96
        name = ttkb.Icon(self._ICON_NAME, max(1, round(pixels / scale)), color)

        glyph = tk.PhotoImage(width=int(tcl("image", "width", name)), height=int(tcl("image", "height", name)))
        tcl(glyph.name, "copy", name, "-to", 0, 0)
        return glyph

    @staticmethod
    def _visible_bounds(image: tk.PhotoImage) -> tuple[int, int, int, int]:
        """(left, top, right, bottom) of the non-transparent pixels, both ends included."""
        width, height = image.width(), image.height()

        def row_is_visible(y: int) -> bool:
            return any(not image.transparency_get(x, y) for x in range(width))

        def column_is_visible(x: int) -> bool:
            return any(not image.transparency_get(x, y) for y in range(height))

        top = next((y for y in range(height) if row_is_visible(y)), 0)
        bottom = next((y for y in range(height - 1, -1, -1) if row_is_visible(y)), height - 1)
        left = next((x for x in range(width) if column_is_visible(x)), 0)
        right = next((x for x in range(width - 1, -1, -1) if column_is_visible(x)), width - 1)
        return left, top, right, bottom
