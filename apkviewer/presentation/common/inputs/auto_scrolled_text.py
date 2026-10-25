import tkinter as tk
from tkinter import ttk

import ttkbootstrap as ttkb

from apkviewer.presentation.common.scrolling.auto_hide_scrollbar import AutoHideScrollbar
from apkviewer.presentation.common.scrolling.wheel_lines import WheelLines
from apkviewer.presentation.config.layout import FIELD_PADX, FIELD_PADY


class AutoScrolledText(ttkb.ScrolledText):
    """
    A ScrolledText widget whose scrollbars are only shown while the content overflows.

    ttkbootstrap reserves a fixed lane for each bar (a minsize on the row or column that holds
    it), so showing or hiding a bar never changes the size of the text. That is what stops the
    visibility from feeding back into the layout (a bar appears -> less room -> another bar
    appears...): those lanes must stay. The grid options of the bars are not repeated here
    either; hiding a bar remembers them and showing it again restores them.

    The mouse wheel scrolls the text while it overflows vertically; otherwise it is left to the
    page behind it (same rule as the tables of BaseTreePanel).

    It takes the focus with Tab like an Entry does, and shows it with the same ring. Tk would not
    do it: a Text that is read-only (state disabled) is skipped by the keyboard traversal. The
    frame around the Text is not a stop: it has focus bindings (those of the icons overlaid on
    it), and Tk takes any widget that has them for one unless it is told otherwise.
    """

    def __init__(self, *args, **kwargs) -> None:
        # Ensure horizontal scrollbar is requested by default
        kwargs.setdefault("hbar", True)
        super().__init__(*args, **kwargs)

        self.text.configure(padx=FIELD_PADX, pady=FIELD_PADY, takefocus=True)
        ttk.Frame.configure(self, takefocus=False)  # not self.configure: that one is delegated to the Text

        # ttkbootstrap grids the bars as soon as it creates them: start with both hidden and
        # let the first scroll report of the text decide which ones the content really needs.
        self.hide_scrollbars()
        if self.hbar is not None:
            self.text.configure(xscrollcommand=AutoHideScrollbar(self.hbar).scroll_command)
        if self.vbar is not None:
            self.text.configure(yscrollcommand=AutoHideScrollbar(self.vbar).scroll_command)
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.text.bind(sequence, self._on_mousewheel)

    def _on_mousewheel(self, event: tk.Event) -> str | None:
        first, last = self.text.yview()
        if first <= 0.0 and last >= 1.0:
            return None  # nothing to scroll here: let the page behind it scroll
        lines = WheelLines.of(event)
        units = round(lines)
        if units == 0 and lines != 0:
            units = 1 if lines > 0 else -1
        if units:
            self.text.yview_scroll(units, "units")
        return "break"  # handled: the enclosing scrollable page must not scroll too
