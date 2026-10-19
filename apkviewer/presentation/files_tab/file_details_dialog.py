"""
Popup dialog showing the parsed details of selected file(s) or folder(s).
"""

import tkinter as tk
from typing import Optional

import ttkbootstrap as ttkb
import ttkbootstrap.constants as ttkb_constants
from ttkbootstrap.dialogs import Dialog


class FileDetailsDialog(Dialog):
    """Builds and shows the modal 'Details' popup for files/folders."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent.winfo_toplevel())
        self._items_data: list = []
        self._summary: Optional[dict] = None
        self._initial_focus: ttkb.Button | None     # type: ignore

    def show(self, items_data: list, summary: Optional[dict] = None, **options) -> None:    # type: ignore
        """
        Shows the details of `items_data` and returns once the dialog is closed; nothing happens
        when there are no items. `options`: the ones of `Dialog.show` (`position`, `wait_for_result`).
        """
        if not items_data:
            return
        self._items_data = items_data
        self._summary = summary
        self._title = "Item Details" if len(items_data) == 1 else "Multiple Items Details"
        super().show(**options)

    def create_body(self, master: tk.Misc) -> None:
        toplevel_window: tk.Tk | tk.Toplevel = master.winfo_toplevel()
        toplevel_window.minsize(350, 180)
        body = ttkb.Frame(master)
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=(20, 0))

        if len(self._items_data) == 1:
            self._build_single_item(body, self._items_data[0])
        else:
            self._build_multi_item(body, self._items_data, self._summary)

    def create_buttonbox(self, master: tk.Misc) -> None:
        close_button = ttkb.Button(master, text="Close", command=self.close, bootstyle=ttkb_constants.PRIMARY)
        close_button.pack(pady=20)
        self._initial_focus = close_button

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
            summary: Optional[dict] = None
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
