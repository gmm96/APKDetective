"""
Base class of the tabs made of "form" sections: read-only fields for
single values (with a copy icon) and read-only text boxes for lists. A tab
builds its sections explicitly (`add_section(...).add_entry(...)`), so it
decides what to show instead of rendering whatever a dictionary contains.
"""

import tkinter as tk
from collections.abc import Sequence
from tkinter import ttk
from tkinter import font as tkfont
from typing import Any

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.appearance.tk_widget_styler import TkWidgetStyler
from apkviewer.presentation.common.auto_hide_scrollbar import AutoHideScrollbar
from apkviewer.presentation.common.copy_icon_overlay import CopyIconOverlay
from apkviewer.presentation.common.copyable_entry import CopyableEntry
from apkviewer.presentation.common.scrollable_frame import ScrollableFrame
from apkviewer.presentation.common.text_context_menu import TextContextMenu
from apkviewer.presentation.common.text_line_marker import TextLineMarker
from apkviewer.presentation.common.warning_banner import WarningBanner
from apkviewer.presentation.config.layout import LABEL_WIDTH, MIN_LIST_LINES
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
    ) -> "FormSection":
        """Create a section; badge is an optional (text, chip kind) pair."""
        frame = ttk.LabelFrame(self.scroll_frame.inner_frame, text=title)
        frame.grid(row=self._next_row, column=0, sticky="ew", padx=self.SECTION_PAD_X, pady=self.SECTION_PAD_Y)
        self._next_row += 1
        if badge is not None:
            self.create_chip(frame, *badge).place(relx=1.0, x=self.BADGE_OFFSET_X, y=self.BADGE_OFFSET_Y, anchor="ne")
        section = FormSection(self, frame, responsive, max_columns, min_field_width)
        self._sections.append(section)
        return section

    def create_copy_entry(self, parent: tk.Misc, text: str, monospace: bool = False) -> CopyableEntry:
        entry = CopyableEntry(parent, text, self._icons, font=FONT_MONO_SMALL if monospace else None)
        self._copy_entries.append(entry)
        return entry

    def create_chip(self, parent: tk.Misc, text: str, kind: str) -> tk.Label:
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
        """Create a read-only text widget; copy_text=None suppresses its copy icon."""
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

    def _shared_entry_label_width_px(self) -> int:
        """Measure the widest entry or list label across the whole panel, plus a small margin."""
        labels = [label for section in self._sections for label, _field, _row in section._entries]
        labels.extend([label for section in self._sections for label in section._list_labels])
        if not labels:
            return 0

        max_width = 0
        for label in labels:
            font_spec = label.cget("font") or ttk.Style(label).lookup("TLabel", "font") or "TkDefaultFont"
            font = tkfont.Font(root=self, font=font_spec)
            max_width = max(max_width, font.measure(label.cget("text")))
            del font
        return max_width + self.LABEL_EXTRA_WIDTH_PX

    def _refresh_section_layouts(self) -> None:
        """Reflow sections because adding a label can change the shared label width."""
        for section in self._sections:
            section._apply_layout()


class FormSection:
    """One LabelFrame of a FormPanel; each call adds a row to it."""

    LABEL_VALUE_GAP_PX = 8
    COLUMN_GAP_PX = 128
    OUTER_HORIZONTAL_PADDING_PX = 10
    GRID_BORDER_RESERVE_PX = 6
    DEFAULT_MIN_FIELD_WIDTH_PX = 200
    FIELD_VERTICAL_PADDING_PX = 5
    DEFAULT_LAYOUT_HORIZONTAL_PADDING_PX = 10
    GROUP_HORIZONTAL_PADDING_PX = 10
    GROUP_TOP_PADDING_PX = 10
    LIST_HORIZONTAL_PADDING_PX = 10
    LIST_VERTICAL_PADDING_PX = 5

    def __init__(
        self,
        panel: FormPanel,
        frame: ttk.LabelFrame,
        responsive: bool = False,
        max_columns: int = 1,
        min_field_width: int | None = None,
    ) -> None:
        self._panel: FormPanel = panel
        self.frame: ttk.LabelFrame = frame
        self._responsive: bool = responsive
        self._max_columns: int = max(1, max_columns)
        self._min_field_width: int = max(1, min_field_width if min_field_width is not None else self.DEFAULT_MIN_FIELD_WIDTH_PX)
        self._row: int = 0
        self._column: int = 1
        self._entries: list[tuple[ttk.Label, CopyableEntry, int]] = []
        self._list_labels: list[ttk.Label] = []
        self._has_non_entry_content = False
        
        self.frame.bind("<Configure>", self._on_resize, add="+")

    def add_group(self, title: str) -> None:
        """Add a small caption that starts a group of rows."""
        self._has_non_entry_content = True
        
        # Spans across label (1), gap (2), and value (3) columns
        self._panel.create_muted_label(self.frame, title.upper()).grid(
            row=self._row, column=1, columnspan=3, sticky="w",
            pady=(self.GROUP_TOP_PADDING_PX, 0)
        )
        self._row += 1
        self._panel._refresh_section_layouts()

    def add_entry(self, label_text: str, value: Any, monospace: bool = False) -> None:
        """Add a selectable, read-only field with a copy icon."""
        label = ttk.Label(self.frame, text=label_text, width=LABEL_WIDTH)
        field = self._panel.create_copy_entry(self.frame, "" if value is None else str(value), monospace)
        original_row = self._row
        self._entries.append((label, field, original_row))
        self._row += 1
        self._panel._refresh_section_layouts()

    def add_list(self, label_text: str, items: Sequence[str], separator: str = "\n") -> None:
        self._has_non_entry_content = True
        
        # Position label in column 1 to align with entry labels
        label = ttk.Label(self.frame, text=f"{label_text} ({len(items)})", width=-1, anchor="w")
        label.grid(row=self._row, column=1, sticky="nw", pady=self.LIST_VERTICAL_PADDING_PX)
        self._list_labels.append(label)
        
        text, line_count = _build_display_text(items, separator)
        container = ttk.Frame(self.frame)
        
        # Position container in column 3 to align with entry values
        container.grid(row=self._row, column=3, sticky="ew", pady=self.LIST_VERTICAL_PADDING_PX)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        
        self._panel.build_list_widget(container, text, line_count, copy_text=separator.join(items) if items else None)
        self._row += 1
        self._panel._refresh_section_layouts()

    def _on_resize(self, _event: tk.Event) -> None:
        self._apply_layout()

    def _apply_layout(self) -> None:
        """Lay out entry-only sections responsively; leave mixed sections on their original layout."""
        if self._has_non_entry_content:
            self._apply_default_layout()
            return
        if not self._entries:
            return
        self._apply_responsive_layout(self._column_count())

    def _column_count(self) -> int:
        """Choose the most columns that still leave each value field enough room."""
        if not self._responsive or self._max_columns <= 1:
            return 1
        frame_width = self.frame.winfo_width()
        label_width = self._panel._shared_entry_label_width_px()
        available_width = frame_width - 2 * self.OUTER_HORIZONTAL_PADDING_PX - self.GRID_BORDER_RESERVE_PX
        min_pair_width = label_width + self.LABEL_VALUE_GAP_PX + self._min_field_width
        fitting_columns = (available_width + self.COLUMN_GAP_PX) // (min_pair_width + self.COLUMN_GAP_PX)
        return max(1, min(self._max_columns, len(self._entries), int(fitting_columns)))

    def _reset_columns(self) -> None:
        """Clear grid settings left by a previous responsive layout."""
        for column in range(max(2, 4 * self._max_columns + 1)):
            self.frame.columnconfigure(column, weight=0, minsize=0, uniform="")

    def _apply_default_layout(self) -> None:
        """Preserve the original layout for sections containing groups or lists, aligning with responsive layout."""
        self._reset_columns()
        label_width = self._panel._shared_entry_label_width_px()
        
        # Explicit column definition mimicking a 1-column responsive layout
        self.frame.columnconfigure(0, weight=0, minsize=self.OUTER_HORIZONTAL_PADDING_PX)
        self.frame.columnconfigure(1, weight=0, minsize=label_width)
        self.frame.columnconfigure(2, weight=0, minsize=self.LABEL_VALUE_GAP_PX)
        self.frame.columnconfigure(3, weight=1, minsize=0)
        self.frame.columnconfigure(4, weight=0, minsize=self.OUTER_HORIZONTAL_PADDING_PX)

        # Re-grid entries using the new responsive-aligned columns
        for label, field, original_row in self._entries:
            label.configure(width=-1, wraplength=label_width, anchor="w")
            label.grid(row=original_row, column=1, sticky="w", pady=self.FIELD_VERTICAL_PADDING_PX)
            field.grid(row=original_row, column=3, sticky="ew", pady=self.FIELD_VERTICAL_PADDING_PX)
            
        # Update dynamically stored list labels
        for lst_label in self._list_labels:
            lst_label.configure(wraplength=label_width)

    def _apply_responsive_layout(self, columns: int) -> None:
        """Use fixed label/gutter widths and let only value columns absorb spare space."""
        self._reset_columns()
        label_width = self._panel._shared_entry_label_width_px()
        self.frame.columnconfigure(0, weight=0, minsize=self.OUTER_HORIZONTAL_PADDING_PX)
        self.frame.columnconfigure(4 * columns, weight=0, minsize=self.OUTER_HORIZONTAL_PADDING_PX)
        for column in range(columns):
            label_column = 1 + 4 * column
            gap_column = label_column + 1
            value_column = label_column + 2
            self.frame.columnconfigure(label_column, weight=0, minsize=label_width)
            self.frame.columnconfigure(gap_column, weight=0, minsize=self.LABEL_VALUE_GAP_PX)
            self.frame.columnconfigure(value_column, weight=1, minsize=0, uniform="entry_values")
            if column < columns - 1:
                self.frame.columnconfigure(value_column + 1, weight=0, minsize=self.COLUMN_GAP_PX)
        last_row = (len(self._entries) - 1) // columns
        for index, (label, field, _original_row) in enumerate(self._entries):
            row, column = divmod(index, columns)
            label_column = 1 + 4 * column
            value_column = label_column + 2
            top_padding = (0 if row == 0 else self.FIELD_VERTICAL_PADDING_PX)
            bottom_padding = (self.FIELD_VERTICAL_PADDING_PX * 2 if row == last_row else self.FIELD_VERTICAL_PADDING_PX)
            vertical_padding = (top_padding, bottom_padding)
            label.configure(width=-1, wraplength=label_width, anchor="w")
            label.grid(row=row, column=label_column, sticky="w", pady=vertical_padding)
            field.grid(row=row, column=value_column, sticky="ew", pady=vertical_padding)


def _build_display_text(items: Sequence[str], separator: str) -> tuple[str, int]:
    text = separator.join(items) if items else "None found"
    line_count = max(text.count("\n") + 1, MIN_LIST_LINES)
    text += "\n" * (line_count - (text.count("\n") + 1))
    return text, line_count
