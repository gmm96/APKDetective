"""
Decides how many columns of "label + value" pairs fit in a given width.
Pure arithmetic, with no Tk involved, so it can be tested on its own.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnPlanner:
    max_columns: int
    min_field_width: int   # the narrowest a value field may get before a column is dropped
    label_value_gap: int   # space between a label and its value
    column_gap: int        # space between two label + value pairs
    side_margins: int      # space the section keeps free on both sides of the grid

    @property
    def is_responsive(self) -> bool:
        """Whether the number of columns can change with the width."""
        return self.max_columns > 1

    def columns_for(self, frame_width: int, label_width: int, entry_count: int) -> int:
        """The most columns that still leave each value field its minimum width."""
        if not self.is_responsive:
            return 1
        available = frame_width - self.side_margins
        pair_width = label_width + self.label_value_gap + self.min_field_width
        fitting = (available + self.column_gap) // (pair_width + self.column_gap)
        return max(1, min(self.max_columns, entry_count, fitting))
