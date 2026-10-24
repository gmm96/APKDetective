"""
Keeps the user on one tab of a notebook while the others have nothing to show (a load
is going on, or no file has been loaded yet): the other tabs are disabled, so neither the
mouse nor the keyboard can leave it, and they are enabled again afterwards.
"""

import tkinter as tk

import ttkbootstrap as ttkb


class NotebookLock:
    def __init__(self, notebook: ttkb.Notebook) -> None:
        self._notebook: ttkb.Notebook = notebook
        self._locked_tabs: list[str] = []

    def lock(self, keep: tk.Widget) -> None:
        """Selects `keep` and disables every other tab."""
        self.unlock()
        self._notebook.select(keep)
        for tab in self._notebook.tabs():
            if str(tab) != str(keep) and self._notebook.tab(tab, "state") == tk.NORMAL:
                self._notebook.tab(tab, state=tk.DISABLED)
                self._locked_tabs.append(str(tab))

    def unlock(self) -> None:
        """Enables again the tabs that `lock` disabled (and only those)."""
        for tab in self._locked_tabs:
            self._notebook.tab(tab, state=tk.NORMAL)
        self._locked_tabs.clear()
