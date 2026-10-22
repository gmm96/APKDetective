"""
Popup dialog showing the parsed details of selected file(s) or folder(s).
"""

import tkinter as tk
from typing import Tuple

import ttkbootstrap as ttkb
import ttkbootstrap.constants as ttkb_constants
from ttkbootstrap.dialogs import Dialog


class FileDetailsDialog(Dialog):
    """Builds and shows the modal 'Details' popup for files/folders."""

    def __init__(self, parent: tk.Misc, items_data: list, summary: dict | None = None) -> None:
        title = "Item Details" if len(items_data) == 1 else "Multiple Items Details"
        super().__init__(parent.winfo_toplevel(), title=title)
        self._items_data: list = items_data
        self._summary: dict | None = summary

    def show(self, position: Tuple[int, int] | None = None, wait_for_result: bool = True) -> None:
        """Shows the details and returns once the dialog is closed; nothing happens when there are no items."""
        if self._items_data:
            super().show(position, wait_for_result)

    def create_body(self, master: tk.Misc) -> None:
        master.winfo_toplevel().minsize(350, 180)
        body = ttkb.Frame(master)
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=(20, 0))
        if len(self._items_data) == 1:
            self._build_single_item(body, self._items_data[0])
        else:
            self._build_multi_item(body, self._items_data, self._summary)

    def create_buttonbox(self, master: tk.Misc) -> None:
        close_button = ttkb.Button(master, text="Close", command=self.close, bootstyle=ttkb_constants.PRIMARY)
        close_button.pack(pady=20)
        self._initial_focus = close_button  # type: ignore[assignment]  # ttkbootstrap infers this hook as None

    def _build_single_item(self, parent: ttkb.Frame, item: dict) -> None:
        fields = {
            "Name:": item.get("name", ""),
            "Type:": item.get("type", ""),
            "Size:": item.get("size", ""),
            "Compressed:": item.get("compressed", ""),
            "Modified:": item.get("modified", ""),
        }
        self._render_grid(parent, fields)

    def _build_multi_item(
            self,
            parent: ttkb.Frame,
            items: list,
            summary: dict | None = None
        ) -> None:
        fields = {"Items Selected:": str(len(items))}
        if summary:
            # Real totals, computed from the raw byte counts - not the
            # already-formatted per-row strings, which can't be summed
            # directly (e.g. "1.5 KB" + "900 B").
            fields["Files:"] = str(summary.get("file_count", 0))
            fields["Folders:"] = str(summary.get("folder_count", 0))
            fields["Total size:"] = summary.get("total_size", "-")
            fields["Total compressed:"] = summary.get("total_compressed", "-")
        else:
            fields["Notice:"] = (
                "Multiple selections shown.\nDetailed metrics are available\n"
                "by inspecting items individually."
            )

        self._render_grid(parent, fields)

    @staticmethod
    def _render_grid(parent: ttkb.Frame, fields: dict) -> None:
        row_idx = 0
        for label_text, value_text in fields.items():
            label = ttkb.Label(parent, text=label_text, width=15, font=("", 0, "bold"))
            label.grid(row=row_idx, column=0, sticky="nw", pady=5)
            value = ttkb.Label(parent, text=str(value_text), wraplength=250)
            value.grid(row=row_idx, column=1, sticky="w", pady=5, padx=(10, 0))
            row_idx += 1
        parent.columnconfigure(1, weight=1)
