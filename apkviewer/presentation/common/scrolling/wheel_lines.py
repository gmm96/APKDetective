"""
Turns a mouse-wheel event into the number of lines it asks to scroll, whatever the
platform reports: Linux/X11 sends one Button-4/5 event per notch, Windows reports 120 units
per notch (less on a precision touchpad, which sends many small events) and macOS reports lines.
"""

import sys
import tkinter as tk


class WheelLines:
    LINES_PER_NOTCH: int = 3
    _WINDOWS_DELTA_PER_NOTCH: int = 120

    @classmethod
    def of(cls, event: tk.Event) -> float:
        """Lines to scroll for this event: positive scrolls down, negative up, 0 if it did not turn."""
        if event.num == 4:
            return -float(cls.LINES_PER_NOTCH)
        if event.num == 5:
            return float(cls.LINES_PER_NOTCH)
        if sys.platform == "darwin":
            return -float(event.delta)
        return -event.delta * cls.LINES_PER_NOTCH / cls._WINDOWS_DELTA_PER_NOTCH
