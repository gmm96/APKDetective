"""
One titled frame of a FormPanel; each call adds a row to it.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Sequence
from tkinter import ttk
from typing import TYPE_CHECKING, Any

from apkviewer.presentation.config.layout import LABEL_WIDTH, MIN_LIST_LINES
from apkviewer.presentation.common.copyable_entry import CopyableEntry

if TYPE_CHECKING:
    from apkviewer.presentation.common.form_panel import FormPanel


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
        self.entries: list[tuple[ttk.Label, CopyableEntry, int]] = []
        self.list_labels: list[ttk.Label] = []
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
        self._panel.refresh_section_layouts()

    def add_entry(self, label_text: str, value: Any, monospace: bool = False) -> None:
        """Add a selectable, read-only field with a copy icon."""
        label = ttk.Label(self.frame, text=label_text, width=LABEL_WIDTH)
        field = self._panel.create_copy_entry(self.frame, "" if value is None else str(value), monospace)
        original_row = self._row
        self.entries.append((label, field, original_row))
        self._row += 1
        self._panel.refresh_section_layouts()

    def add_list(self, label_text: str, items: Sequence[str], separator: str = "\n") -> None:
        self._has_non_entry_content = True
        # Position label in column 1 to align with entry labels
        label = ttk.Label(self.frame, text=f"{label_text} ({len(items)})", width=-1, anchor="w")
        label.grid(row=self._row, column=1, sticky="nw", pady=self.LIST_VERTICAL_PADDING_PX)
        self.list_labels.append(label)
        text, line_count = self._display_text(items, separator)
        container = ttk.Frame(self.frame)
        # Position container in column 3 to align with entry values
        container.grid(row=self._row, column=3, sticky="ew", pady=self.LIST_VERTICAL_PADDING_PX)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        self._panel.build_list_widget(container, text, line_count, copy_text=separator.join(items) if items else None)
        self._row += 1
        self._panel.refresh_section_layouts()

    def _on_resize(self, _event: tk.Event) -> None:
        self.apply_layout()

    def apply_layout(self) -> None:
        """Lay out entry-only sections responsively; leave mixed sections on their original layout."""
        if self._has_non_entry_content:
            self._apply_default_layout()
            return
        if not self.entries:
            return
        self._apply_responsive_layout(self._column_count())

    def _column_count(self) -> int:
        """Choose the most columns that still leave each value field enough room."""
        if not self._responsive or self._max_columns <= 1:
            return 1
        frame_width = self.frame.winfo_width()
        label_width = self._panel.shared_entry_label_width_px()
        available_width = frame_width - 2 * self.OUTER_HORIZONTAL_PADDING_PX - self.GRID_BORDER_RESERVE_PX
        min_pair_width = label_width + self.LABEL_VALUE_GAP_PX + self._min_field_width
        fitting_columns = (available_width + self.COLUMN_GAP_PX) // (min_pair_width + self.COLUMN_GAP_PX)
        return max(1, min(self._max_columns, len(self.entries), int(fitting_columns)))

    def _reset_columns(self) -> None:
        """Clear grid settings left by a previous responsive layout."""
        for column in range(max(2, 4 * self._max_columns + 1)):
            self.frame.columnconfigure(column, weight=0, minsize=0, uniform="")

    def _apply_default_layout(self) -> None:
        """Preserve the original layout for sections containing groups or lists, aligning with responsive layout."""
        self._reset_columns()
        label_width = self._panel.shared_entry_label_width_px()
        # Explicit column definition mimicking a 1-column responsive layout
        self.frame.columnconfigure(0, weight=0, minsize=self.OUTER_HORIZONTAL_PADDING_PX)
        self.frame.columnconfigure(1, weight=0, minsize=label_width)
        self.frame.columnconfigure(2, weight=0, minsize=self.LABEL_VALUE_GAP_PX)
        self.frame.columnconfigure(3, weight=1, minsize=0)
        self.frame.columnconfigure(4, weight=0, minsize=self.OUTER_HORIZONTAL_PADDING_PX)
        # Re-grid entries using the new responsive-aligned columns
        for label, field, original_row in self.entries:
            label.configure(width=-1, wraplength=label_width, anchor="w")
            label.grid(row=original_row, column=1, sticky="w", pady=self.FIELD_VERTICAL_PADDING_PX)
            field.grid(row=original_row, column=3, sticky="ew", pady=self.FIELD_VERTICAL_PADDING_PX)
        # Update dynamically stored list labels
        for lst_label in self.list_labels:
            lst_label.configure(wraplength=label_width)

    def _apply_responsive_layout(self, columns: int) -> None:
        """Use fixed label/gutter widths and let only value columns absorb spare space."""
        self._reset_columns()
        label_width = self._panel.shared_entry_label_width_px()
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
        last_row = (len(self.entries) - 1) // columns
        for index, (label, field, _original_row) in enumerate(self.entries):
            row, column = divmod(index, columns)
            label_column = 1 + 4 * column
            value_column = label_column + 2
            top_padding = (0 if row == 0 else self.FIELD_VERTICAL_PADDING_PX)
            bottom_padding = (self.FIELD_VERTICAL_PADDING_PX * 2 if row == last_row else self.FIELD_VERTICAL_PADDING_PX)
            vertical_padding = (top_padding, bottom_padding)
            label.configure(width=-1, wraplength=label_width, anchor="w")
            label.grid(row=row, column=label_column, sticky="w", pady=vertical_padding)
            field.grid(row=row, column=value_column, sticky="ew", pady=vertical_padding)

    @staticmethod
    def _display_text(items: Sequence[str], separator: str) -> tuple[str, int]:
        text = separator.join(items) if items else "None found"
        line_count = max(text.count("\n") + 1, MIN_LIST_LINES)
        text += "\n" * (line_count - (text.count("\n") + 1))
        return text, line_count
