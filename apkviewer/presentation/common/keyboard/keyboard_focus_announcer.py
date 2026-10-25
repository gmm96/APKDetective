"""
Tells the widgets when the keyboard (Tab / Shift+Tab) has just moved the focus to one of them.

Tk moves the focus on its own, and a widget that gets it through <FocusIn> can't tell a key press
from a click. What a widget wants to do about it is different too: a page scrolls to show the field,
a table selects its first row. So, after Tk has done its traversal, this sends the virtual event
<<KeyboardFocusIn>> to the widget that got the focus, and each widget reacts to it on its own. A click
never sends it.
"""

import tkinter as tk


class KeyboardFocusAnnouncer:
    EVENT: str = "<<KeyboardFocusIn>>"

    def __init__(self, root: tk.Misc) -> None:
        # add="+": Tk's own handlers of these events (the ones that move the focus) must run first.
        root.bind_all("<<NextWindow>>", self._on_traversal, add="+")
        root.bind_all("<<PrevWindow>>", self._on_traversal, add="+")

    @classmethod
    def announce(cls, widget: tk.Misc) -> None:
        """For the code that moves the focus by itself with the keyboard (the arrows of a button block)."""
        widget.event_generate(cls.EVENT)

    def _on_traversal(self, event: tk.Event) -> None:
        try:
            focused = event.widget.focus_get()
        except (KeyError, tk.TclError):  # the focus is in a window Tk has no widget for (a popup menu)
            return
        if focused is not None:
            self.announce(focused)
