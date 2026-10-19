"""
"Manifest" tab: read-only text view with XML syntax highlighting.
"""

import tkinter as tk
from typing import Optional

import ttkbootstrap as ttkb

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.config.theme import FONT_MONO
from apkviewer.presentation.common.auto_scrolled_text import AutoScrolledText
from apkviewer.presentation.common.text_context_menu import TextContextMenu

from .xml_syntax_highlighter import XmlSyntaxHighlighter


class ManifestPanel(ttkb.Frame):
    def __init__(
        self,
        parent: ttkb.Notebook,
        context_menu: TextContextMenu,
        palette: ThemePalette,
        highlighter: Optional[XmlSyntaxHighlighter] = None
    ) -> None:
        super().__init__(parent)
        self._highlighter: XmlSyntaxHighlighter = highlighter or XmlSyntaxHighlighter()

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # ttkbootstrap styles the inner Text (colors, selection) and follows the theme by itself.
        scrolled_text = AutoScrolledText(self, wrap=tk.NONE, font=FONT_MONO)
        scrolled_text.grid(row=0, column=0, sticky="nsew")
        self.text: tk.Text = scrolled_text.text

        context_menu.attach(self.text)
        self.apply_palette(palette)

    def apply_palette(self, palette: ThemePalette) -> None:
        self._highlighter.configure_tags(self.text, palette)

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete(1.0, tk.END)

    def render(self, manifest_xml: str):
        self.clear()
        padded_xml = self._pad_lines_to_equal_width(manifest_xml)
        self.text.insert(tk.END, padded_xml)
        self._highlighter.highlight(self.text, padded_xml)
        self.text.configure(state="disabled")

    @staticmethod
    def _pad_lines_to_equal_width(content: str) -> str:
        """
        Right-pad every line with spaces so they all share the width of the
        longest one.

        Tk's Text widget (wrap="none") only reserves horizontal scroll room
        for the lines currently in the vertical viewport - it recomputes
        that room dynamically as you scroll, so without this, the
        horizontal scrollbar keeps resizing itself depending on which part
        of the document happens to be visible. Padding every line to a
        uniform width means whatever is on screen always reports the true,
        whole-document width, so the scrollbar is identical for line 1 and
        line 1000. The added spaces are invisible (monospace font) and are
        stripped again on copy - see TextContextMenu.
        """
        lines = content.split("\n")
        max_len = max((len(line) for line in lines), default=0)
        return "\n".join(line.ljust(max_len) for line in lines)
