"""
Top header: app icon, name/package labels and the "Load APK" button.
"""

import io
import tkinter as tk
from typing import Optional
from collections.abc import Callable

import ttkbootstrap as ttkb
import ttkbootstrap.constants as ttkb_constants
from PIL import Image, ImageTk

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.config.layout import ICON_SIZE
from apkviewer.presentation.config.theme import FONT_SUBTITLE, FONT_TITLE
from apkviewer.presentation.icons.placeholder_icon_factory import PlaceholderIconFactory


class AppHeader(ttkb.Frame):
    # Characters; wide enough for both labels so the button keeps its size when it changes.
    _BUTTON_WIDTH: int = 8

    def __init__(
        self,
        parent: ttkb.Frame,
        on_load_click: Callable[[], None],
        on_cancel_click: Callable[[], None],
        palette: ThemePalette,
        icon_factory: Optional[PlaceholderIconFactory] = None
    ) -> None:
        super().__init__(parent)
        self._on_load_click: Callable[[], None] = on_load_click
        self._on_cancel_click: Callable[[], None] = on_cancel_click
        self._icon_factory: PlaceholderIconFactory = icon_factory or PlaceholderIconFactory()
        self._placeholder_icon: tk.PhotoImage = self._icon_factory.create(palette)
        self._current_icon: Optional[ImageTk.PhotoImage] = None

        left = ttkb.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.Y)

        self.icon_label: ttkb.Label = ttkb.Label(left, image=self._placeholder_icon)
        self.icon_label.pack(side=tk.LEFT, padx=(0, 15))

        text_frame = ttkb.Frame(left)
        text_frame.pack(side=tk.LEFT, expand=True, fill=tk.Y)

        self.name_label: ttkb.Label = ttkb.Label(text_frame, text="No APK Loaded", font=FONT_TITLE)
        self.name_label.pack(side=tk.TOP, anchor="sw", expand=True)

        self.package_label: ttkb.Label = ttkb.Label(
            text_frame,
            text="Select an application file to begin analysis.",
            font=FONT_SUBTITLE,
            foreground=palette.foreground,
        )
        self.package_label.pack(side=tk.TOP, anchor="nw", expand=True)

        self.load_button: ttkb.Button = ttkb.Button(
            self,
            text="Load APK",
            command=on_load_click,
            bootstyle=ttkb_constants.PRIMARY,
            width=self._BUTTON_WIDTH,
        )
        self.load_button.pack(side=tk.RIGHT)

    def apply_palette(self, palette: ThemePalette) -> None:
        self._placeholder_icon = self._icon_factory.create(palette)
        if self._current_icon is None:
            self.icon_label.configure(image=self._placeholder_icon)
        self.package_label.configure(foreground=palette.foreground)

    def reset_to_placeholder(self, file_name: str) -> None:
        self._current_icon = None
        self.icon_label.configure(image=self._placeholder_icon)
        self.name_label.configure(text="Analyzing APK...")
        self.package_label.configure(text=file_name)

    def show_error(self) -> None:
        self.name_label.configure(text="Error loading APK")

    def set_loading(self, loading: bool) -> None:
        """While an APK is being loaded the button turns into a red "Cancel" button."""
        if loading:
            self.load_button.configure(text="Cancel", command=self._on_cancel_click, bootstyle=ttkb_constants.DANGER)
        else:
            self.load_button.configure(text="Load APK", command=self._on_load_click, bootstyle=ttkb_constants.PRIMARY)

    def show_result(self, app_name: str, package_name: str, icon_png: bytes | None = None) -> None:
        thumbnail = self._create_thumbnail(icon_png)
        if thumbnail is not None:
            self._current_icon = thumbnail
            self.icon_label.configure(image=self._current_icon)

        self.name_label.configure(text=app_name or "Unknown App")
        self.package_label.configure(text=package_name or "Unknown Package")

    @staticmethod
    def _create_thumbnail(icon_png: bytes | None) -> Optional[ImageTk.PhotoImage]:
        """Scale the full-resolution icon to the header size; None if it can't be decoded."""
        if icon_png is None:
            return None
        try:
            image = Image.open(io.BytesIO(icon_png)).resize(ICON_SIZE, Image.Resampling.LANCZOS)
        except (OSError, ValueError):
            return None
        return ImageTk.PhotoImage(image)
