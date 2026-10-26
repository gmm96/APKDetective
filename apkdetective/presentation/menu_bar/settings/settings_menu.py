"""
Actions behind the Settings menu. UI-agnostic callables, like the rest of
the toolbar actions.
"""

from collections.abc import Callable
from tkinter import messagebox

import ttkbootstrap as ttkb

from apkdetective.domain.entities.appearance.color_mode_enum import ColorModeEnum
from apkdetective.presentation.appearance.theme_manager import ThemeManager
from apkdetective.presentation.config.theme import THEMES


class SettingsMenu:
    def __init__(
        self,
        parent: ttkb.App,
        theme_manager: ThemeManager
    ) -> None:
        self._parent: ttkb.App = parent
        self._theme_manager: ThemeManager = theme_manager

    @property
    def color_mode(self) -> ColorModeEnum:
        return self._theme_manager.color_mode

    @property
    def base_theme(self) -> str:
        """The active theme, without its light/dark suffix."""
        return self._theme_manager.base_theme

    @property
    def themes(self) -> tuple[str, ...]:
        """Every theme the user can choose."""
        return tuple(THEMES)

    @staticmethod
    def theme_label(base_theme: str) -> str:
        return base_theme.replace("-", " ").title()

    def set_color_mode(self, mode: ColorModeEnum) -> None:
        self._apply("Color mode", lambda: self._theme_manager.set_mode(mode))

    def set_theme(self, base_theme: str) -> None:
        """Changes the theme; the color mode (light / dark / auto) stays as it is."""
        self._apply("Theme", lambda: self._theme_manager.set_theme(base_theme))

    def _apply(self, title: str, change: Callable[[], None]) -> None:
        try:
            change()
        except Exception as exc:
            messagebox.showerror(title, f"Could not apply the theme:\n{exc}", parent=self._parent)
