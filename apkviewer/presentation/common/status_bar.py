"""
Bottom status bar showing the current operation state.
"""

import ttkbootstrap as ttkb

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.status_level import StatusLevel


class StatusBar(ttkb.Frame):
    def __init__(self, parent: ttkb.App, palette: ThemePalette) -> None:
        super().__init__(parent, relief="sunken", borderwidth=1)
        self._palette: ThemePalette
        self._level: StatusLevel = StatusLevel.NEUTRAL
        self.label: ttkb.Label = ttkb.Label(self, text="Ready.")
        self.label.pack(side="left", padx=10, pady=2)
        self.apply_palette(palette)

    def set_status(self, message: str, level: StatusLevel = StatusLevel.NEUTRAL) -> None:
        self._level = level
        self.label.configure(text=message)
        self.apply_palette(self._palette)

    def apply_palette(self, palette: ThemePalette) -> None:
        self._palette = palette
        colors = {
            StatusLevel.NEUTRAL: palette.foreground,
            StatusLevel.INFO: palette.info_text,
            StatusLevel.SUCCESS: palette.success_text,
            StatusLevel.ERROR: palette.danger_text,
        }
        self.label.configure(foreground=colors[self._level])
