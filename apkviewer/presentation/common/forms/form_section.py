"""
One titled frame of a FormPanel; each call adds a row to it.

Widgets are created as the rows are added but laid out later, by
`apply_layout`: the panel asks for it once when the UI is idle, and the
section asks for it again when its width changes. A layout that would come
out the same as the last one is skipped, so resizing the window only costs
something when the number of columns (or the shared label width) changes.
"""

import tkinter as tk
from collections.abc import Callable, Sequence
from typing import Any

import ttkbootstrap as ttkb

from apkviewer.presentation.common.forms.column_planner import ColumnPlanner
from apkviewer.presentation.common.inputs.copyable_entry import CopyableEntry
from apkviewer.presentation.common.forms.form_widget_factory import FormWidgetFactory
from apkviewer.presentation.common.forms.label_width_meter import LabelWidthMeter
from apkviewer.presentation.config.layout import MAX_LIST_LINES, MIN_LIST_LINES


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

    _MIXED_LAYOUT: int = 0  # the layout of sections that contain groups or lists

    def __init__(
        self,
        frame: ttkb.LabelFrame,
        widgets: FormWidgetFactory,
        label_meter: LabelWidthMeter,
        on_changed: Callable[[], None],
        responsive: bool = False,
        max_columns: int = 1,
        min_field_width: int | None = None,
    ) -> None:
        """`on_changed`: called when rows are added, so the owner can schedule the layout."""
        self.frame: ttkb.LabelFrame = frame
        self._widgets: FormWidgetFactory = widgets
        self._label_meter: LabelWidthMeter = label_meter
        self._on_changed: Callable[[], None] = on_changed
        min_width = self.DEFAULT_MIN_FIELD_WIDTH_PX if min_field_width is None else min_field_width
        self._planner: ColumnPlanner = ColumnPlanner(
            max_columns=max(1, max_columns) if responsive else 1,
            min_field_width=max(1, min_width),
            label_value_gap=self.LABEL_VALUE_GAP_PX,
            column_gap=self.COLUMN_GAP_PX,
            side_margins=2 * self.OUTER_HORIZONTAL_PADDING_PX + self.GRID_BORDER_RESERVE_PX,
        )
        self._row: int = 0
        self._entries: list[tuple[ttkb.Label, CopyableEntry, int]] = []  # (label, field, row it was added in)
        self._list_labels: list[ttkb.Label] = []
        self._has_non_entry_content: bool = False
        self._width: int = 0
        self._dirty: bool = True  # rows were added since the last layout
        self._applied: tuple[int, int] | None = None  # (columns, label width) of the last layout
        self.frame.bind("<Configure>", self._on_resize, add="+")

    # --- Rows ----------------------------------------------------------------------------

    def add_group(self, title: str) -> None:
        """Add a small caption that starts a group of rows."""
        self._has_non_entry_content = True
        # Spans the label (1), gap (2) and value (3) columns
        self._widgets.create_muted_label(self.frame, title.upper()).grid(
            row=self._row, column=1, columnspan=3, sticky="w", pady=(self.GROUP_TOP_PADDING_PX, 0)
        )
        self._row += 1
        self._content_changed()

    def add_entry(self, label_text: str, value: Any, monospace: bool = False) -> None:
        """Add a selectable, read-only field with a copy icon."""
        self._label_meter.register(label_text)
        label = ttkb.Label(self.frame, text=label_text, anchor="w")
        field = self._widgets.create_copy_entry(self.frame, self._format_entry_value(value), monospace)
        self._entries.append((label, field, self._row))
        self._row += 1
        self._content_changed()

    def add_list(self, label_text: str, items: Sequence[str], separator: str = "\n") -> None:
        self._has_non_entry_content = True
        text_label = f"{label_text} ({len(items)})"
        self._label_meter.register(text_label)
        # The label goes in column 1 and the box in column 3, aligned with the entries
        label = ttkb.Label(self.frame, text=text_label, anchor="w")
        label.grid(row=self._row, column=1, sticky="nw", pady=self.LIST_VERTICAL_PADDING_PX)
        self._list_labels.append(label)
        text, line_count = self._display_text(items, separator)
        container = ttkb.Frame(self.frame)
        container.grid(row=self._row, column=3, sticky="ew", pady=self.LIST_VERTICAL_PADDING_PX)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        self._widgets.build_list_widget(
            container, text, line_count, copy_text=separator.join(items) if items else None
        )
        self._row += 1
        self._content_changed()

    def _content_changed(self) -> None:
        self._dirty = True
        self._on_changed()

    # --- Layout --------------------------------------------------------------------------

    def _on_resize(self, event: tk.Event) -> None:
        # Only a change of WIDTH matters: laying the rows out changes the height, which would
        # otherwise trigger this handler again.
        if event.width != self._width:
            self._width = event.width
            self.apply_layout()

    def apply_layout(self) -> None:
        """Grid the entries for the current width. Does nothing if the result would be the last one."""
        label_width = self._label_meter.width_px
        if self._has_non_entry_content:
            columns = self._MIXED_LAYOUT
        elif self._entries:
            width = self._width or self.frame.winfo_width()
            if self._planner.is_responsive and width <= 1:
                return  # no size yet: the first <Configure> lays it out
            columns = self._planner.columns_for(width, label_width, len(self._entries))
        else:
            return  # nothing of its own to lay out (the owner may grid its widgets in `frame`)

        state = (columns, label_width)
        if not self._dirty and state == self._applied:
            return
        self._reset_columns()
        if columns == self._MIXED_LAYOUT:
            self._apply_mixed_layout(label_width)
        else:
            self._apply_columns_layout(columns, label_width)
        self._applied = state
        self._dirty = False

    def _reset_columns(self) -> None:
        """Clear grid settings left by a previous layout."""
        for column in range(max(2, 4 * self._planner.max_columns + 1)):
            self.frame.columnconfigure(column, weight=0, minsize=0, uniform="")

    def _apply_mixed_layout(self, label_width: int) -> None:
        """Sections with groups or lists: one column of rows, aligned like a one-column responsive layout."""
        self.frame.columnconfigure(0, weight=0, minsize=self.OUTER_HORIZONTAL_PADDING_PX)
        self.frame.columnconfigure(1, weight=0, minsize=label_width)
        self.frame.columnconfigure(2, weight=0, minsize=self.LABEL_VALUE_GAP_PX)
        self.frame.columnconfigure(3, weight=1, minsize=0)
        self.frame.columnconfigure(4, weight=0, minsize=self.OUTER_HORIZONTAL_PADDING_PX)
        for label, field, row in self._entries:
            label.configure(wraplength=label_width)
            label.grid(row=row, column=1, sticky="w", pady=self.FIELD_VERTICAL_PADDING_PX)
            field.grid(row=row, column=3, sticky="ew", pady=self.FIELD_VERTICAL_PADDING_PX)
        for list_label in self._list_labels:
            list_label.configure(wraplength=label_width)

    def _apply_columns_layout(self, columns: int, label_width: int) -> None:
        """Fixed label and gutter widths; only the value columns absorb the spare space."""
        self.frame.columnconfigure(0, weight=0, minsize=self.OUTER_HORIZONTAL_PADDING_PX)
        self.frame.columnconfigure(4 * columns, weight=0, minsize=self.OUTER_HORIZONTAL_PADDING_PX)
        for column in range(columns):
            label_column = 1 + 4 * column
            value_column = label_column + 2
            self.frame.columnconfigure(label_column, weight=0, minsize=label_width)
            self.frame.columnconfigure(label_column + 1, weight=0, minsize=self.LABEL_VALUE_GAP_PX)
            self.frame.columnconfigure(value_column, weight=1, minsize=0, uniform="entry_values")
            if column < columns - 1:
                self.frame.columnconfigure(value_column + 1, weight=0, minsize=self.COLUMN_GAP_PX)
        last_row = (len(self._entries) - 1) // columns
        for index, (label, field, _row) in enumerate(self._entries):
            row, column = divmod(index, columns)
            label_column = 1 + 4 * column
            top_padding = 0 if row == 0 else self.FIELD_VERTICAL_PADDING_PX
            bottom_padding = self.FIELD_VERTICAL_PADDING_PX * (2 if row == last_row else 1)
            vertical_padding = (top_padding, bottom_padding)
            label.configure(wraplength=label_width)
            label.grid(row=row, column=label_column, sticky="w", pady=vertical_padding)
            field.grid(row=row, column=label_column + 2, sticky="ew", pady=vertical_padding)

    @staticmethod
    def _display_text(items: Sequence[str], separator: str) -> tuple[str, int]:
        text = separator.join(items) if items else "None found"
        content_lines = text.count("\n") + 1
        line_count = max(min(content_lines, MAX_LIST_LINES), MIN_LIST_LINES)
        text += "\n" * max(0, line_count - content_lines)
        return text, line_count

    @staticmethod
    def _format_entry_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return str(value).lower()
        return str(value)
