"""
A vertically scrollable Tkinter frame with mouse-wheel support (Windows,
macOS and Linux/X11-style Button-4/5 wheel events).

Scrolling is only possible while the content is taller than the visible
area; otherwise the scrollbar is hidden and the wheel does nothing.

Several instances can live in the same window (one per tab): the wheel
only scrolls the frame that is under the pointer.

Scrolling must stay cheap, because it happens on every wheel event:
- Moving the content inside the canvas makes Tk send a <Configure> to it, so the handlers of
  both widgets only act when a SIZE changes. Recomputing the scroll region on every scroll step
  made each step trigger one more pass, which is what made the scroll feel laggy.
- The scrollbar is only touched when it has to appear or disappear (see AutoHideScrollbar).
- The wheel moves a number of pixels, scaled by how far the wheel turned, instead of a fixed
  tenth of the viewport per event: a smooth touchpad sends many small events.
"""

import tkinter as tk

import ttkbootstrap as ttkb

from apkviewer.presentation.common.scrolling.auto_hide_scrollbar import AutoHideScrollbar
from apkviewer.presentation.common.scrolling.wheel_lines import WheelLines
from apkviewer.presentation.viewmodels.appearance.theme_palette import ThemePalette


class ScrollableFrame(ttkb.Frame):
    WHEEL_LINE_PX: int = 20  # one notch scrolls WheelLines.LINES_PER_NOTCH of them, like a desktop text area

    def __init__(self, container: ttkb.Frame, palette: ThemePalette, *args, **kwargs) -> None:
        super().__init__(container, *args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.canvas: ttkb.Canvas = ttkb.Canvas(self, borderwidth=0, highlightthickness=0)
        self._scrollbar: ttkb.Scrollbar = ttkb.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self._scrollbar_grid: dict[str, object] = {"row": 0, "column": 1, "sticky": "ns"}
        self.inner_frame: ttkb.Frame = ttkb.Frame(self.canvas)
        self.canvas_window: int = self.canvas.create_window(
            (0, 0),
            window=self.inner_frame,
            anchor="nw"
        )

        self._content_size: tuple[int, int] = (0, 0)   # sizes of the last <Configure> handled
        self._viewport_size: tuple[int, int] = (0, 0)
        self._region_height: int = 1                   # height of the current scroll region
        self._fits: bool = True                        # whether the content fits in the viewport

        self.inner_frame.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=AutoHideScrollbar(self._scrollbar, self._scrollbar_grid).scroll_command)

        self.apply_palette(palette)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self._scrollbar.grid(**self._scrollbar_grid)

        # add="+": bind_all is application-wide, so every instance must
        # append its handler instead of replacing the previous one.
        self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.bind_all("<Button-4>", self._on_mousewheel, add="+")
        self.bind_all("<Button-5>", self._on_mousewheel, add="+")

    def apply_palette(self, palette: ThemePalette) -> None:
        self.canvas.configure(background=palette.background)

    def collapse(self) -> None:
        """
        To call once all the content has been removed. A frame without children keeps the size it last
        had, so an emptied one would still look as tall as before, with its scrollbar and its scrolling.
        """
        self.inner_frame.configure(height=1)
        self._update_scrollregion()

    # --- Layout ----------------------------------------------------------------

    def _on_content_configure(self, event: tk.Event) -> None:
        # Also sent when the canvas merely moves the content while scrolling: only a new size matters.
        size = (event.width, event.height)
        if size != self._content_size:
            self._content_size = size
            self._update_scrollregion()

    def _on_canvas_configure(self, event: tk.Event) -> None:
        size = (event.width, event.height)
        if size == self._viewport_size:
            return
        if size[0] != self._viewport_size[0]:
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self._viewport_size = size
        self._update_scrollregion()

    def _update_scrollregion(self) -> None:
        # The region is never smaller than the viewport: Tk would otherwise
        # let a short content be dragged around inside a taller canvas.
        content_height = self.inner_frame.winfo_reqheight()
        viewport_height = self.canvas.winfo_height()
        self._region_height = max(content_height, viewport_height)
        self._fits = content_height <= viewport_height
        self.canvas.configure(scrollregion=(0, 0, self.canvas.winfo_width(), self._region_height))
        if self._fits:
            self.canvas.yview_moveto(0)

    # --- Mouse wheel -----------------------------------------------------------

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self._fits or not self._pointer_is_inside(event):
            return
        pixels = self._wheel_pixels(event)
        if pixels:
            first, _last = self.canvas.yview()
            self.canvas.yview_moveto(first + pixels / self._region_height)

    @classmethod
    def _wheel_pixels(cls, event: tk.Event) -> int:
        """How many pixels to scroll (positive: down) for this wheel event, at least 1 if it turned at all."""
        lines = WheelLines.of(event)
        pixels = round(lines * cls.WHEEL_LINE_PX)
        if pixels == 0 and lines != 0:
            return 1 if lines > 0 else -1
        return pixels

    def _pointer_is_inside(self, event: tk.Event) -> bool:
        if not self.winfo_ismapped():
            return False
        try:
            widget = self.winfo_containing(event.x_root, event.y_root)
        except KeyError:  # internal Tk windows (e.g. popup menus) have no Python wrapper
            return False
        while widget is not None:
            if widget is self:
                return True
            widget = widget.master
        return False
