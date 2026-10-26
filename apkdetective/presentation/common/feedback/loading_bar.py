"""
A slim indeterminate progress bar for the whole window. It lives in a strip
that keeps its height while the bar is hidden, so showing or hiding it never
moves what is below.
"""

import tkinter as tk

import ttkbootstrap as ttkb
import ttkbootstrap.constants as ttkb_constants


class LoadingBar(ttkb.Frame):
    _STRIP_HEIGHT: int = 30  # the gap that used to separate the header from the tabs
    _BAR_MARGIN: tuple[int, int] = (10, 10)
    _STEP_MS: int = 15

    def __init__(self, parent: tk.Misc, **options) -> None:
        super().__init__(parent, height=self._STRIP_HEIGHT, **options)
        self.pack_propagate(False)
        self._bar: ttkb.Progressbar = ttkb.Progressbar(
            self, mode="indeterminate", bootstyle=ttkb_constants.PRIMARY
        )

    def start(self) -> None:
        self._bar.pack(fill=tk.X, pady=self._BAR_MARGIN)
        self._bar.start(self._STEP_MS)

    def stop(self) -> None:
        self._bar.stop()
        self._bar.pack_forget()
