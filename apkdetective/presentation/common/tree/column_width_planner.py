"""
Decides the width of each column of a table for a given available width.
Pure arithmetic, with no Tk involved, so it can be tested on its own.

The rules, in this order:

  1. The columns that stretch (they have a weight, or `stretch` without one) share the
     width the others leave, in proportion to their weights. A column that would end up
     under its `min_width` gets that minimum and the rest share what is left. A column
     with `stretch` and no weight counts as much as its own `width`.
  2. If even that does not fit, the other columns shrink too, each in proportion to how
     much it can still give, down to its `min_width`.
  3. If the minimum widths do not fit either, every column keeps its `min_width`: the
     table is wider than its viewport and the horizontal scrollbar shows.
"""

import math
from collections.abc import Sequence

from apkdetective.presentation.viewmodels.tree.tree_column import TreeColumn


class ColumnWidthPlanner:
    def plan(self, columns: Sequence[TreeColumn], available: int) -> dict[str, int]:
        """Column id -> width, for a viewport `available` pixels wide."""
        stretching = [column for column in columns if self._weight_of(column) > 0]
        fixed = [column for column in columns if self._weight_of(column) <= 0]
        widths: dict[str, int] = {column.id: max(column.width, column.min_width) for column in fixed}
        widths.update(self._share(stretching, available - sum(widths.values())))
        overflow = sum(widths.values()) - available
        if overflow > 0:
            widths.update(self._shrink(fixed, widths, overflow))
        return widths

    @staticmethod
    def _weight_of(column: TreeColumn) -> float:
        if column.weight:
            return column.weight
        return float(column.width) if column.stretch else 0.0

    @classmethod
    def _share(cls, columns: Sequence[TreeColumn], remaining: float) -> dict[str, int]:
        """Split `remaining` by weight; a column that would get less than its minimum gets the minimum."""
        widths: dict[str, int] = {}
        pending = list(columns)
        while pending:
            total_weight = sum(cls._weight_of(column) for column in pending)
            too_narrow = next(
                (c for c in pending if remaining * cls._weight_of(c) / total_weight < c.min_width), None
            )
            if too_narrow is None:
                for column in pending:
                    widths[column.id] = int(remaining * cls._weight_of(column) / total_weight)
                break
            widths[too_narrow.id] = too_narrow.min_width
            remaining -= too_narrow.min_width
            pending.remove(too_narrow)
        return widths

    @staticmethod
    def _shrink(columns: Sequence[TreeColumn], widths: dict[str, int], overflow: int) -> dict[str, int]:
        """Take `overflow` pixels from the columns, in proportion to what they can give."""
        slack = {column.id: widths[column.id] - column.min_width for column in columns}
        total_slack = sum(slack.values())
        if total_slack <= 0:
            return {}
        ratio = min(1.0, overflow / total_slack)
        # Rounded up so that the table never ends a pixel too wide, which would show the scrollbar.
        return {
            column_id: widths[column_id] - min(give, math.ceil(give * ratio))
            for column_id, give in slack.items()
        }
