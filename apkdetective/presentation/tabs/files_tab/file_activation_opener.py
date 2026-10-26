"""
Opens the files of the Files tree when the user activates them: with a double click on one, or with
Enter on the selected ones. Folders are left alone: on them both gestures keep the Treeview's own
behaviour (expanding or collapsing the folder), which is why the handlers never stop the event.
"""

import tkinter as tk
from collections.abc import Callable, Iterable
from tkinter import ttk

from apkdetective.domain.entities.archive.file_node import FileNode
from apkdetective.presentation.tabs.files_tab.file_open_action import FileOpenAction


class FileActivationOpener:
    def __init__(
        self,
        tree: ttk.Treeview,
        get_node: Callable[[str], FileNode | None],
        open_action: FileOpenAction,
    ) -> None:
        self._tree: ttk.Treeview = tree
        self._get_node: Callable[[str], FileNode | None] = get_node
        self._open_action: FileOpenAction = open_action
        # add="+": the tree has other handlers, and the class bindings still have to run for folders.
        self._tree.bind("<Double-1>", self._on_double_click, add="+")
        self._tree.bind("<Return>", self._on_enter, add="+")
        self._tree.bind("<KP_Enter>", self._on_enter, add="+")  # Enter of the numeric keypad

    def _on_double_click(self, event: tk.Event) -> None:
        # The row under the pointer, not the selection: it is the one that was double-clicked.
        iid = self._tree.identify_row(event.y)
        self._open_files([iid] if iid else [])

    def _on_enter(self, _event: tk.Event) -> None:
        self._open_files(self._tree.selection())

    def _open_files(self, iids: Iterable[str]) -> None:
        """Opens those of `iids` that are files; the folders among them are ignored."""
        files = [iid for iid in iids if self._is_file(iid)]
        if files:
            self._open_action.open(files)

    def _is_file(self, iid: str) -> bool:
        node = self._get_node(iid)
        return node is not None and node.is_file
