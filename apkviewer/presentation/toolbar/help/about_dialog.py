"""
Modal "About" popup with basic information about the project.
"""

import tkinter as tk

import ttkbootstrap as ttkb
import ttkbootstrap.constants as ttkb_constants
from ttkbootstrap.dialogs import Dialog

from apkviewer.presentation.config.about import PROJECT_DESCRIPTION, PROJECT_NAME
from apkviewer.presentation.config.theme import FONT_TITLE


class AboutDialog(Dialog):
    """Centered on the main window, modal, and closed with the button or Escape."""

    def __init__(
        self,
        parent: tk.Misc,
        project_name: str = PROJECT_NAME,
        description: str = PROJECT_DESCRIPTION,
    ) -> None:
        super().__init__(parent.winfo_toplevel(), title=f"About {project_name}")
        self._project_name: str = project_name
        self._description: str = description

    def create_body(self, master: tk.Misc) -> None:
        body = ttkb.Frame(master)
        body.pack(fill=tk.BOTH, expand=True, padx=30, pady=(20, 0))

        ttkb.Label(body, text=self._project_name, font=FONT_TITLE).pack(pady=(0, 10))
        ttkb.Label(body, text=self._description, wraplength=380, justify=tk.LEFT).pack()

    def create_buttonbox(self, master: tk.Misc) -> None:
        close_button = ttkb.Button(master, text="Close", command=self.close, bootstyle=ttkb_constants.PRIMARY)
        close_button.pack(pady=20)
        self._initial_focus = close_button
