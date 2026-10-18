"""
Themed icon label overlaid on a target widget.

Shared by every field that shows a clickable icon inside its own area (copy icon,
clear icon...). It owns what used to be duplicated across those widgets: the label,
the ttk style that keeps the label background in sync with the field it covers, and
the placement over the target.
"""

import re
import tkinter as tk
from tkinter import ttk
from collections.abc import Callable

import ttkbootstrap as ttkb


class OverlayIcon:
    # Gap between the icon and the right border of the target, in pixels.
    _RIGHT_MARGIN: int = 8

    def __init__(
        self,
        target: tk.Widget,
        icon_name: str,
        icon_style: str,
        background: str | None = None,
        on_click: Callable[[tk.Event], str | None] | None = None,
        top_offset: int | None = None,
        right_offset: int | None = None,
    ) -> None:
        self._target: tk.Widget = target
        self._icon_name: str = icon_name
        self._icon_style: str = icon_style
        self._background: str | None = background  # explicit override; None = follow the target
        self._top_offset: int | None = top_offset
        self._right_offset: int = right_offset or 0

        self._applied: tuple[str, str, str | None] | None = None
        self._shown: bool = False

        # Child of the target (not a sibling): it is clipped to it, always stacked above it,
        # and destroyed with it, so no z-order or lifecycle handling is needed.
        self._label: ttkb.Label = ttkb.Label(target, cursor="hand2")
        if on_click is not None:
            self._label.bind("<Button-1>", on_click)
        self._apply()

    @property
    def widget(self) -> ttkb.Label:
        """The label, so callers can bind their own events (hover, etc.)."""
        return self._label

    def configure(
        self,
        icon_name: str | None = None,
        icon_style: str | None = None,
        background: str | None = None,
    ) -> None:
        """Changes the icon glyph, its color style or the background override. None keeps the current value."""
        if icon_name is not None:
            self._icon_name = icon_name
        if icon_style is not None:
            self._icon_style = icon_style
        if background is not None:
            self._background = background
        self._apply()

    def show(self) -> None:
        if not self._shown:
            self._shown = True
            self._place()
        self._apply()  # the target may have changed state (focus...) while the icon was hidden

    def hide(self) -> None:
        if self._shown:
            self._shown = False
            self._label.place_forget()

    def refresh_background(self) -> None:
        """Re-syncs the background after the target changed state (focus, readonly...)."""
        if self._shown:
            self._apply()

    # --- Internals -------------------------------------------------------------------------------

    def _place(self) -> None:
        options: dict = {"relx": 1.0, "x": -(self._RIGHT_MARGIN + self._right_offset)}
        if self._top_offset is None and not self._right_offset:
            options.update(rely=0.5, anchor="e")
        else:
            options.update(anchor="ne", y=self._top_offset or 0)
        self._label.place(**options)

    def _apply(self) -> None:
        """Applies glyph, color and background, touching ttk only when something actually changed."""
        background = self._resolve_background()
        state = (self._icon_name, self._icon_style, background)
        if state == self._applied:
            return
        self._applied = state

        if background is None:
            self._label.configure(icon=self._icon_name, bootstyle=self._icon_style)
            return

        # bootstyle first so ttkbootstrap builds "<style>.TLabel"; the derived style only overrides the background.
        self._label.configure(bootstyle=self._icon_style)
        clean_bg: str = re.sub(r'\W', '', background)
        style_name = f"OverlayIcon.{clean_bg}.{self._icon_style}.TLabel"
        ttkb.Style().configure(style_name, background=background)
        self._label.configure(icon=self._icon_name, style=style_name)

    def _resolve_background(self) -> str | None:
        if self._background is not None:
            return self._background
        try:
            if isinstance(self._target, ttk.Widget):
                style_name = str(self._target.cget("style")) or self._target.winfo_class()
                color = ttkb.Style().lookup(style_name, "fieldbackground", self._target.state())
                return str(color) or None
            return str(self._target.cget("background")) or None
        except tk.TclError:
            return None
