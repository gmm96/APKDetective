"""
Base class of the tabs made of "form" sections: read-only fields for
single values (with a copy icon) and read-only text boxes for lists. A tab
builds its sections explicitly (`add_section(...).add_entry(...)`), so it
decides what to show instead of rendering whatever a dictionary contains.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.appearance.tk_widget_styler import TkWidgetStyler
from apkviewer.presentation.common.auto_hide_scrollbar import AutoHideScrollbar
from apkviewer.presentation.common.copy_icon_overlay import CopyIconOverlay
from apkviewer.presentation.common.copyable_entry import CopyableEntry
from apkviewer.presentation.common.form_section import FormSection
from apkviewer.presentation.common.scrollable_frame import ScrollableFrame
from apkviewer.presentation.common.text_context_menu import TextContextMenu
from apkviewer.presentation.common.text_line_marker import TextLineMarker
from apkviewer.presentation.common.warning_banner import WarningBanner
from apkviewer.presentation.config.theme import FONT_MONO_SMALL
from apkviewer.presentation.icons.field_icons import FieldIcons
from apkviewer.presentation.icons.icon_loader import IconLoader

# Chip kinds: "success", "danger", "neutral" (filled) and "muted" (outlined).
CHIP_KINDS: tuple[str, ...] = ("success", "danger", "neutral", "muted")


class FormPanel(ttk.Frame):
    """Base class for tabs containing read-only fields and lists."""

    SECTION_PAD_X = 15
    SECTION_PAD_Y = 10
    BADGE_OFFSET_X = -14
    BADGE_OFFSET_Y = -4
    LABEL_EXTRA_WIDTH_PX = 10
    CHIP_PAD_X = 8
    CHIP_PAD_Y = 1
    LIST_COPY_ICON_TOP_OFFSET = 4

    def __init__(
        self,
        parent: tk.Misc,
        context_menu: TextContextMenu,
        palette: ThemePalette,
        line_marker: TextLineMarker | None = None,
        icon_loader: IconLoader | None = None,
    ) -> None:
        super().__init__(parent)
        self._palette: ThemePalette = palette
        self._context_menu: TextContextMenu = context_menu
        self._line_marker: TextLineMarker = line_marker or TextLineMarker()
        self._icons: FieldIcons = FieldIcons(icon_loader or IconLoader(), palette)
        self._list_widgets: list[tk.Text] = []
        self._copy_entries: list[CopyableEntry] = []
        self._list_copy_icons: list[CopyIconOverlay] = []
        self._chips: list[tuple[tk.Label, str]] = []
        self._muted_labels: list[ttk.Label] = []
        self._sections: list["FormSection"] = []
        self._next_row: int = 0

        self.scroll_frame: ScrollableFrame = ScrollableFrame(self, palette)
        self.scroll_frame.pack(expand=True, fill=tk.BOTH)
        self.scroll_frame.inner_frame.columnconfigure(0, weight=1)
        self._banner: WarningBanner = WarningBanner(self, palette, before=self.scroll_frame)

    def apply_palette(self, palette: ThemePalette) -> None:
        self._palette = palette
        self.scroll_frame.apply_palette(palette)
        self._banner.apply_palette(palette)
        self._icons.apply_palette(palette)
        for widget in self._list_widgets:
            self._style_list_widget(widget)
        for entry in self._copy_entries:
            entry.refresh_icons()
        for overlay in self._list_copy_icons:
            overlay.refresh_icons()
            overlay.set_background(palette.text_bg)
        for chip, kind in self._chips:
            self._style_chip(chip, kind)
        for label in self._muted_labels:
            label.configure(foreground=palette.secondary_fg)

    def show_warnings(self, messages: list[str]) -> None:
        self._banner.show(messages)

    def clear(self) -> None:
        self._banner.show(())
        self._list_widgets.clear()
        self._copy_entries.clear()
        self._list_copy_icons.clear()
        self._chips.clear()
        self._muted_labels.clear()
        self._sections.clear()
        self._next_row = 0
        for widget in self.scroll_frame.inner_frame.winfo_children():
            widget.destroy()

    def add_section(
        self,
        title: str,
        badge: tuple[str, str] | None = None,
        responsive: bool = False,
        max_columns: int = 1,
        min_field_width: int | None = None,
    ) -> FormSection:
        """`badge`: optional (text, chip kind) shown on the section's title line, at its right."""
        frame = ttk.LabelFrame(self.scroll_frame.inner_frame, text=title)
        frame.grid(row=self._next_row, column=0, sticky="ew", padx=self.SECTION_PAD_X, pady=self.SECTION_PAD_Y)
        self._next_row += 1
        if badge is not None:
            self.create_chip(frame, *badge).place(relx=1.0, x=self.BADGE_OFFSET_X, y=self.BADGE_OFFSET_Y, anchor="ne")
        section = FormSection(self, frame, responsive, max_columns, min_field_width)
        self._sections.append(section)
        return section

    # --- Widgets shared by the sections ------------------------------------------------------

    def create_copy_entry(self, parent: tk.Misc, text: str, monospace: bool = False) -> CopyableEntry:
        entry = CopyableEntry(parent, text, self._icons, font=FONT_MONO_SMALL if monospace else None)
        self._copy_entries.append(entry)
        return entry

    def create_chip(self, parent: tk.Misc, text: str, kind: str) -> tk.Label:
        """`kind`: "success", "danger", "neutral" (filled) or "muted" (outlined)."""
        chip = tk.Label(parent, text=text, padx=self.CHIP_PAD_X, pady=self.CHIP_PAD_Y, borderwidth=0)
        self._chips.append((chip, kind))
        self._style_chip(chip, kind)
        return chip

    def create_muted_label(self, parent: tk.Misc, text: str) -> ttk.Label:
        label = ttk.Label(parent, text=text, foreground=self._palette.secondary_fg)
        self._muted_labels.append(label)
        return label

    def _style_chip(self, chip: tk.Label, kind: str) -> None:
        p = self._palette
        foreground, background, border = {
            "success": (p.status_success, p.mark_bg, p.mark_bg),
            "danger": (p.status_error, p.folder_bg, p.folder_bg),
            "neutral": (p.secondary_fg, p.folder_bg, p.folder_bg),
            "muted": (p.secondary_fg, p.window_bg, p.placeholder_border),
        }[kind]
        chip.configure(
            foreground=foreground,
            background=background,
            highlightthickness=1,
            highlightbackground=border,
            highlightcolor=border,
        )

    def build_list_widget(
        self, container: ttk.Frame, text: str, line_count: int, copy_text: str | None = None
    ) -> None:
        """`copy_text`: what the copy icon of the box copies (None: no icon, e.g. an empty list)."""
        text_widget = tk.Text(container, height=line_count, wrap=tk.NONE, borderwidth=1, relief="solid", font=FONT_MONO_SMALL)
        h_scroll = ttk.Scrollbar(container, orient="horizontal", command=text_widget.xview)
        autohide = AutoHideScrollbar(h_scroll, {"row": 1, "column": 0, "sticky": "ew"})
        text_widget.configure(xscrollcommand=autohide.scroll_command)
        text_widget.grid(row=0, column=0, sticky="ew")
        text_widget.insert(tk.END, text)
        text_widget.configure(state="disabled")
        self._line_marker.bind(text_widget)
        self._list_widgets.append(text_widget)
        self._style_list_widget(text_widget)
        self._context_menu.attach(text_widget)
        if copy_text:
            self._list_copy_icons.append(
                CopyIconOverlay(
                    text_widget,
                    self._icons,
                    lambda: copy_text,
                    background=self._palette.text_bg,
                    top_offset=self.LIST_COPY_ICON_TOP_OFFSET
                )
            )

    def _style_list_widget(self, text_widget: tk.Text) -> None:
        TkWidgetStyler.style_text(text_widget, self._palette)
        self._line_marker.apply_palette(text_widget, self._palette)

    def shared_entry_label_width_px(self) -> int:
        """Measure the widest entry or list label across the whole panel, plus a small margin."""
        labels = [label for section in self._sections for label, _field, _row in section.entries]
        labels.extend([label for section in self._sections for label in section.list_labels])
        if not labels:
            return 0
        max_width = 0
        for label in labels:
            font_spec = label.cget("font") or ttk.Style(label).lookup("TLabel", "font") or "TkDefaultFont"
            font = tkfont.Font(root=self, font=font_spec)
            max_width = max(max_width, font.measure(label.cget("text")))
            del font
        return max_width + self.LABEL_EXTRA_WIDTH_PX

    def refresh_section_layouts(self) -> None:
        """Reflow sections because adding a label can change the shared label width."""
        for section in self._sections:
            section.apply_layout()
