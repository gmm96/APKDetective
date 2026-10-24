"""
The "open" action of the Files tab: opens entries of the APK with the system's default application
and tells the user when that is not possible. The context menu and the double click / Enter all go through
it, so they all open files in exactly the same way.
"""

import tkinter as tk
from collections.abc import Callable, Sequence
from tkinter import messagebox

from apkviewer.application.files.entry_previewer import EntryPreviewer


class FileOpenAction:
    def __init__(
        self,
        parent: tk.Misc,
        entry_previewer: EntryPreviewer,
        get_apk_path: Callable[[], str | None],
    ) -> None:
        self._parent: tk.Misc = parent  # the window that error dialogs belong to
        self._entry_previewer: EntryPreviewer = entry_previewer
        self._get_apk_path: Callable[[], str | None] = get_apk_path

    def open(self, entry_paths: Sequence[str]) -> None:
        apk_path = self._get_apk_path()
        if not entry_paths or not apk_path:
            return
        try:
            self._entry_previewer.open_entries(apk_path, entry_paths)
        except Exception as exc:  # pylint: disable=broad-except
            messagebox.showerror("Open failed", str(exc), parent=self._parent)
