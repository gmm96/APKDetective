"""
Base class of the tabs made of "form" sections: read-only fields for
single values (with a copy icon) and read-only text boxes for lists. A tab
builds its sections explicitly (`add_section(...).add_entry(...)`), so it
decides what to show instead of rendering whatever a dictionary contains.

The panel does not lay its sections out while they are being filled: every
change only schedules ONE layout pass for when the UI is idle.
"""

from typing import Any
import tkinter as tk

import ttkbootstrap as ttkb

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.auto_scrolled_text import AutoScrolledText
from apkviewer.presentation.common.copy_icon_overlay import CopyIconOverlay
from apkviewer.presentation.common.copyable_entry import CopyableEntry
from apkviewer.presentation.common.form_section import FormSection
from apkviewer.presentation.common.label_width_meter import LabelWidthMeter
from apkviewer.presentation.common.scrollable_frame import ScrollableFrame
from apkviewer.presentation.common.text_context_menu import TextContextMenu
from apkviewer.presentation.common.text_line_marker import TextLineMarker
from apkviewer.presentation.common.warning_banner import WarningBanner
from apkviewer.presentation.config.theme import FONT_MONO_SMALL
from apkviewer.presentation.config.layout import FIELD_PADX, FIELD_PADY
from apkviewer.presentation.icons.icon_loader import IconLoader
from apkviewer.presentation.viewmodels.color_pair import ColorPair


class FormPanel(ttkb.Frame):
    """Base class for tabs containing read-only fields and lists."""

    # Chip kinds: "success", "danger", "neutral" and "muted"; all of them are filled.
    CHIP_KINDS: tuple[str, ...] = ("success", "danger", "neutral", "muted")

    SECTION_PAD_X = 15
    SECTION_PAD_Y = 10
    BADGE_OFFSET_X = -14
    BADGE_OFFSET_Y = -4
    LABEL_EXTRA_WIDTH_PX = 10
    CHIP_PAD_X = 8
    CHIP_PAD_Y = 1

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
        self._label_meter: LabelWidthMeter = LabelWidthMeter(self, self.LABEL_EXTRA_WIDTH_PX)
        self._layout_job: str | None = None
        self._list_widgets: list[AutoScrolledText] = []
        self._copy_entries: list[CopyableEntry] = []
        self._list_copy_icons: list[CopyIconOverlay] = []
        self._chips: list[tuple[ttkb.Label, str]] = []
        self._muted_labels: list[ttkb.Label] = []
        self._sections: list[FormSection] = []
        self._next_row: int = 0

        self.scroll_frame: ScrollableFrame = ScrollableFrame(self, palette)
        self.scroll_frame.pack(expand=True, fill=tk.BOTH)
        self.scroll_frame.inner_frame.columnconfigure(0, weight=1)
        self._banner: WarningBanner = WarningBanner(self, palette, self.scroll_frame)

    def apply_palette(self, palette: ThemePalette) -> None:
        self._palette = palette
        self._banner.apply_palette(palette)
        icon_colors: dict[str, str] = {
            "icon_color": palette.info_text,
            "active_icon_color": palette.success_text,
            "background": palette.input_background,
        }
        for entry in self._copy_entries:
            entry.update_colors(**icon_colors)
        for overlay in self._list_copy_icons:
            overlay.update_colors(**icon_colors)
        for text_widget in self._list_widgets:
            self._style_list_widget(text_widget.text)
        for chip, kind in self._chips:
            self._style_chip(chip, kind)
        for label in self._muted_labels:
            label.configure(foreground=palette.muted_text)

    def show_warnings(self, messages: list[str]) -> None:
        self._banner.show(messages)

    def clear(self) -> None:
        self._banner.show(())
        if self._layout_job is not None:
            self.after_cancel(self._layout_job)
            self._layout_job = None
        self._label_meter.reset()
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
        """
        `badge`: optional (text, chip kind) shown on the section's title line, at its right.
        `responsive`: lay the entries out in up to `max_columns` columns, as many as fit while
        each value field keeps `min_field_width` pixels (sections with groups or lists use one).
        """
        frame = ttkb.LabelFrame(self.scroll_frame.inner_frame, text=title)
        frame.grid(row=self._next_row, column=0, sticky="ew", padx=self.SECTION_PAD_X, pady=self.SECTION_PAD_Y)
        self._next_row += 1
        if badge is not None:
            self.create_chip(frame, *badge).place(relx=1.0, x=self.BADGE_OFFSET_X, y=self.BADGE_OFFSET_Y, anchor="ne")
        section = FormSection(
            frame,
            self,
            self._label_meter,
            self.refresh_section_layouts,
            responsive,
            max_columns,
            min_field_width,
        )
        self._sections.append(section)
        return section

    # --- Widgets shared by the sections ------------------------------------------------------

    def create_copy_entry(self, parent: tk.Misc, text: str, monospace: bool = False) -> CopyableEntry:
        entry = CopyableEntry(
            parent,
            text,
            icon_color=self._palette.info_text,
            active_icon_color=self._palette.success_text,
            background=self._palette.input_background,
            font=FONT_MONO_SMALL if monospace else None
        )
        self._copy_entries.append(entry)
        return entry

    def create_chip(self, parent: tk.Misc, text: str, kind: str) -> ttkb.Label:
        """`kind`: one of CHIP_KINDS."""
        if kind not in self.CHIP_KINDS:
            raise ValueError(f"Unknown chip kind {kind!r}; expected one of {self.CHIP_KINDS}")
        chip = ttkb.Label(parent, text=text, padding=(self.CHIP_PAD_X, self.CHIP_PAD_Y), borderwidth=0)
        self._chips.append((chip, kind))
        self._style_chip(chip, kind)
        return chip

    def create_muted_label(self, parent: tk.Misc, text: str) -> ttkb.Label:
        label = ttkb.Label(parent, text=text, foreground=self._palette.muted_text)
        self._muted_labels.append(label)
        return label

    def _style_chip(self, chip: ttkb.Label, kind: str) -> None:
        colors: ColorPair = {
            "success": self._palette.chip_success,
            "danger": self._palette.chip_danger,
            "neutral": self._palette.chip_neutral,
            "muted": self._palette.chip_muted,
        }[kind]
        chip.configure(background=colors.background, foreground=colors.foreground)

    def build_list_widget(
        self,
        container: ttkb.Frame,
        text: str,
        line_count: int,
        copy_text: str | None = None
    ) -> None:
        """`copy_text`: what the copy icon of the box copies (None: no icon, e.g. an empty list)."""
        text_widget = AutoScrolledText(
            container,
            height=line_count,
            wrap=tk.NONE,
            borderwidth=1,
            relief="solid",
            font=FONT_MONO_SMALL,
            auto_hide=False
        )
        text_widget.grid(row=0, column=0, sticky="ew")
        text_widget.insert(tk.END, text)
        text_widget.configure(state="disabled")
        self._line_marker.bind(text_widget.text)
        self._list_widgets.append(text_widget)
        self._style_list_widget(text_widget.text)
        self._context_menu.attach(text_widget.text)
        if copy_text:
            self._list_copy_icons.append(
                CopyIconOverlay(
                    text_widget,
                    lambda: copy_text,
                    icon_color=self._palette.info_text,
                    active_icon_color=self._palette.success_text,
                    background=self._palette.input_background,
                    top_offset=FIELD_PADX,
                    right_offset=FIELD_PADY
                )
            )

    def _style_list_widget(self, text_widget: tk.Text) -> None:
        self._line_marker.apply_palette(text_widget, self._palette)

    # --- Layout ------------------------------------------------------------------------------------

    def shared_entry_label_width_px(self) -> int:
        """The width of the widest entry or list label of the panel, plus a small margin."""
        return self._label_meter.width_px

    def refresh_section_layouts(self) -> None:
        """
        Ask for the sections to be laid out again. Many calls in a row (one per added row)
        schedule a single pass, run when the UI is idle.
        """
        if self._layout_job is None:
            self._layout_job = self.after_idle(self._reflow)

    def _reflow(self) -> None:
        self._layout_job = None
        for section in self._sections:
            section.apply_layout()
