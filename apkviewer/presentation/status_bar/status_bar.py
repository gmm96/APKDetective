"""
Bottom status bar showing the current operation state.
"""

import ttkbootstrap as ttkb

from apkviewer.presentation.viewmodels.appearance.theme_palette import ThemePalette
from apkviewer.presentation.viewmodels.status_bar.status_level_enum import StatusLevelEnum


class StatusBar(ttkb.Frame):
    def __init__(self, parent: ttkb.App, palette: ThemePalette) -> None:
        super().__init__(parent, relief="sunken", borderwidth=1)
        self._palette: ThemePalette
        self._level: StatusLevelEnum = StatusLevelEnum.NEUTRAL
        self.label: ttkb.Label = ttkb.Label(self, text="Ready.")
        self.label.pack(side="left", padx=10, pady=2)
        self.apply_palette(palette)

    def set_status(self, message: str, level: StatusLevelEnum = StatusLevelEnum.NEUTRAL) -> None:
        self._level = level
        self.label.configure(text=message)
        self.apply_palette(self._palette)

    def apply_palette(self, palette: ThemePalette) -> None:
        self._palette = palette
        colors = {
            StatusLevelEnum.NEUTRAL: palette.foreground,
            StatusLevelEnum.INFO: palette.info_text,
            StatusLevelEnum.SUCCESS: palette.success_text,
            StatusLevelEnum.ERROR: palette.danger_text,
        }
        self.label.configure(foreground=colors[self._level])
