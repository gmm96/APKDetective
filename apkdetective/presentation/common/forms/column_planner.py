"""
Decides how many columns of "label + value" pairs fit in a given width, and
which cell each entry takes. The entries are read down each column and then
on to the next one (like a newspaper), so the order of the entries is the same
whatever the number of columns. Pure arithmetic, with no Tk involved, so it
can be tested on its own.
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
        """The most columns that still leave each value field its minimum width, and that all get entries."""
        if not self.is_responsive:
            return 1
        available = frame_width - self.side_margins
        pair_width = label_width + self.label_value_gap + self.min_field_width
        fitting = (available + self.column_gap) // (pair_width + self.column_gap)
        columns = max(1, min(self.max_columns, entry_count, fitting))
        # Filling the columns top to bottom can leave the last ones empty (5 entries in 4 columns are 2 + 2 + 1):
        # those columns would only take up space, so they are dropped.
        return -(-entry_count // self.rows_for(columns, entry_count)) if entry_count else 1

    @staticmethod
    def rows_for(columns: int, entry_count: int) -> int:
        """The height of the tallest column when `entry_count` entries are spread over `columns` columns."""
        return max(1, -(-entry_count // columns))

    @staticmethod
    def cell_of(index: int, rows: int) -> tuple[int, int]:
        """The (row, column) of the entry at `index` when each column holds `rows` entries."""
        return index % rows, index // rows
