"""
Right-click "Copy" context menu shared by every read-only Text widget in
the app (manifest viewer, list fields, etc.). Also makes the copy shortcut
(Ctrl+C, Ctrl+Insert, Command+C: Tk's <<Copy>>) behave consistently with it,
since these widgets are read-only (state="disabled") and don't reliably get
Tk's default copy binding.
"""

import tkinter as tk
from collections.abc import Callable

from apkdetective.presentation.viewmodels.appearance.theme_palette import ThemePalette
from apkdetective.presentation.appearance.tk_widget_styler import TkWidgetStyler
from apkdetective.presentation.common.menus.popup_menu_controller import PopupMenuController
from apkdetective.presentation.config.layout_config import LayoutConfig


class TextContextMenu:
    """
    Attach to any Text widget with `attach(widget)`. Right-click (or the
    copy shortcut) copies the current selection; with no selection, the
    currently marked line; with neither, the whole text of the widget.
    """

    def __init__(self, root: tk.Misc, palette: ThemePalette) -> None:
        self._menu = tk.Menu(root, tearoff=0)
        self._menu.add_command(label="Copy Text", command=self._copy_from_active)
        self._popup: PopupMenuController = PopupMenuController(root, self._menu)
        self._active_widget: tk.Text | None = None
        self._full_texts: dict[tk.Text, Callable[[], str]] = {}
        self.apply_palette(palette)

    def apply_palette(self, palette: ThemePalette) -> None:
        TkWidgetStyler.style_menu(self._menu, palette)

    def attach(self, widget: tk.Text, get_full_text: Callable[[], str] | None = None) -> None:
        """
        `get_full_text`: what is copied when nothing is selected or marked, for a widget whose
        content is not exactly what the user means to copy (a list box padded with blank lines).
        By default it is the content of the widget.
        """
        self._full_texts[widget] = get_full_text or (lambda: widget.get("1.0", "end-1c"))
        widget.bind("<Button-3>", self._show)
        widget.bind("<<Copy>>", self._on_copy)

    def _show(self, event: tk.Event) -> None:
        if isinstance(event.widget, tk.Text):
            self._active_widget = event.widget
            self._popup.post(event.x_root, event.y_root)

    def _on_copy(self, event: tk.Event) -> str:
        if isinstance(event.widget, tk.Text):
            self._copy_from(event.widget)
        return "break"

    def _copy_from_active(self) -> None:
        if self._active_widget is not None:
            self._copy_from(self._active_widget)

    def _copy_from(self, widget: tk.Text) -> None:
        try:
            if widget.tag_ranges(tk.SEL):
                text_to_copy = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            else:
                marked = widget.tag_ranges(LayoutConfig.MARKED_LINE_TAG)
                text_to_copy = widget.get(marked[0], marked[1]) if marked else self._full_texts[widget]()
            text_to_copy = self._strip_trailing_padding(text_to_copy)
            if text_to_copy:
                widget.clipboard_clear()
                widget.clipboard_append(text_to_copy)
        except Exception:
            pass

    @staticmethod
    def _strip_trailing_padding(text: str) -> str:
        """
        Drop trailing spaces from each copied line. ManifestPanel pads
        every line to a uniform width (to keep its horizontal scrollbar
        stable - see ManifestPanel._pad_lines_to_equal_width); this makes
        sure that invisible padding never ends up on the clipboard.
        """
        return "\n".join(line.rstrip(" ") for line in text.split("\n"))
