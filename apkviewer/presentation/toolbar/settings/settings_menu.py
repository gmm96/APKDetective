"""
Actions behind the Settings menu. UI-agnostic callables, like the rest of
the toolbar actions.
"""

from tkinter import messagebox

import ttkbootstrap as ttkb

from apkviewer.domain.entities.color_mode import ColorMode
from apkviewer.presentation.appearance.theme_manager import ThemeManager


class SettingsMenu:
    def __init__(
        self,
        parent: ttkb.App,
        theme_manager: ThemeManager
    ) -> None:
        self._parent: ttkb.App = parent
        self._theme_manager: ThemeManager = theme_manager

    @property
    def color_mode(self) -> ColorMode:
        return self._theme_manager.color_mode

    def set_color_mode(self, mode: ColorMode) -> None:
        try:
            self._theme_manager.set_mode(mode)
        except Exception as exc:
            messagebox.showerror("Color mode", f"Could not apply the theme:\n{exc}", parent=self._parent)
