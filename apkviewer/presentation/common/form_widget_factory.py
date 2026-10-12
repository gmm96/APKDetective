"""
What a FormSection needs from the panel that owns it: the widgets that depend
on the panel's palette, icons and context menu. Defined as a protocol so the
section depends on this abstraction and not on FormPanel itself.
"""

import tkinter as tk
from tkinter import ttk
from typing import Protocol

from apkviewer.presentation.common.copyable_entry import CopyableEntry


class FormWidgetFactory(Protocol):
    def create_muted_label(self, parent: tk.Misc, text: str) -> ttk.Label:
        ...

    def create_copy_entry(self, parent: tk.Misc, text: str, monospace: bool = False) -> CopyableEntry:
        ...

    def build_list_widget(
        self, container: ttk.Frame, text: str, line_count: int, copy_text: str | None = None
    ) -> None:
        ...
