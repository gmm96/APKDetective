"""
Modal "About" popup with basic information about the project.
"""

import tkinter as tk
from typing import Optional

import ttkbootstrap as ttkb
import ttkbootstrap.constants as ttkb_constants

from apkviewer.presentation.config.theme import FONT_TITLE
from apkviewer.presentation.config.about import PROJECT_DESCRIPTION, PROJECT_NAME
from apkviewer.presentation.common.modal_dialog_positioner import ModalDialogPositioner


class AboutDialog:
    def __init__(
        self,
        parent: tk.Misc,
        project_name: str = PROJECT_NAME,
        description: str = PROJECT_DESCRIPTION,
        positioner: Optional[ModalDialogPositioner] = None,
    ) -> None:
        self._parent: tk.Misc = parent
        self._project_name: str = project_name
        self._description: str = description
        self._positioner: ModalDialogPositioner = positioner or ModalDialogPositioner()

    def show(self) -> None:
        dialog = ttkb.Toplevel(title=f"About {self._project_name}")
        dialog.resizable(False, False)
        dialog.transient(self._parent.winfo_toplevel())

        main_frame = ttkb.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        ttkb.Label(main_frame, text=self._project_name, font=FONT_TITLE).pack(pady=(0, 10))
        ttkb.Label(main_frame, text=self._description, wraplength=380, justify=tk.LEFT).pack()
        ttkb.Button(main_frame, text="Close", command=dialog.destroy, bootstyle=ttkb_constants.PRIMARY).pack(pady=(20, 0))

        self._positioner.center_on_parent(dialog, self._parent)
        self._positioner.show_as_modal(dialog)
