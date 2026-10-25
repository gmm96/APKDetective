"""
Makes Enter press a radiobutton or a checkbutton, as it presses a button.

Plain Tk activates a focused button only with the space bar; ttkbootstrap adds Enter, but just to buttons
(TButton). So in the app the filter pills, which are radiobuttons, ignored Enter while "Collapse all" or
"Load APK" did not. This gives them the same key, doing exactly what the space bar does.
"""

import tkinter as tk


class EnterKeyActivation:
    _WIDGET_CLASSES: tuple[str, ...] = ("TRadiobutton", "TCheckbutton")
    _KEYS: tuple[str, ...] = ("<Key-Return>", "<KP_Enter>")  # KP_Enter: Enter of the numeric keypad

    def __init__(self, root: tk.Misc) -> None:
        for widget_class in self._WIDGET_CLASSES:
            for key in self._KEYS:
                # The very command Tk binds to the space bar of these widgets (it also shows them pressed).
                root.bind_class(widget_class, key, "ttk::button::activate %W")
