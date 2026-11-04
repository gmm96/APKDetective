"""
Declarative description of one column of a tree ("#0" is the tree column).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TreeColumn:
    id: str
    label: str
    width: int = 150      # preferred width of a column that does not stretch (and the first size of any)
    # The narrowest the automatic layout makes the column. If the window is too narrow for the
    # minimum width of every column, each gets its own and the table scrolls horizontally.
    min_width: int = 80
    stretch: bool = False  # takes part of the free width, as much as its own `width` unless it has a weight
    # Share of the width left over by the columns that don't stretch: a column with weight 2 gets
    # twice the width of one with weight 1. It takes the place of `stretch`.
    weight: float | None = None
    # What the column shows, as a tooltip over its heading (none if the heading says it all).
    tooltip: str | None = None
