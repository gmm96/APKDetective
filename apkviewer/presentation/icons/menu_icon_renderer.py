"""
Renders the icon of a menu entry, whatever its kind (PNG asset or Bootstrap
icon), as an image of the same size, tinted and padded the same way, so a
menu can mix both indistinctly.
"""

import tkinter as tk

import ttkbootstrap as ttkb
from PIL import ImageTk

from apkviewer.presentation.icons.icon_loader import IconLoader
from apkviewer.presentation.viewmodels.asset_icon import AssetIcon
from apkviewer.presentation.viewmodels.bootstrap_icon import BootstrapIcon


class MenuIconRenderer:
    def __init__(self, master: tk.Misc, icon_loader: IconLoader | None = None) -> None:
        self._master: tk.Misc = master
        self._icon_loader: IconLoader = icon_loader or IconLoader()

    def render(
        self,
        icon: AssetIcon | BootstrapIcon,
        size: tuple[int, int],
        color: str,
        padding_left: int = 0,
        padding_right: int = 0,
    ) -> ImageTk.PhotoImage | tk.PhotoImage:
        """An image of `size` plus the horizontal paddings (transparent), with the icon tinted `color`."""
        match icon:
            case AssetIcon(path=path):
                return self._icon_loader.load_icon(
                    path,
                    size=size,
                    hex_color=color,
                    padding_left=padding_left,
                    padding_right=padding_right,
                )
            case BootstrapIcon(name=name):
                return self._render_bootstrap_icon(name, size, color, padding_left, padding_right)
        raise TypeError(f"Unsupported menu icon: {icon!r}")

    def _render_bootstrap_icon(
        self,
        name: str,
        size: tuple[int, int],
        color: str,
        padding_left: int,
        padding_right: int,
    ) -> tk.PhotoImage:
        # Bootstrap icons are square: draw it as large as fits and center it in the requested box.
        side = min(size)
        glyph = ttkb.Icon(name, side, color)

        image = tk.PhotoImage(master=self._master, width=size[0] + padding_left + padding_right, height=size[1])
        image.tk.call(image.name, "copy", glyph, "-to", padding_left + (size[0] - side) // 2, (size[1] - side) // 2)
        return image
