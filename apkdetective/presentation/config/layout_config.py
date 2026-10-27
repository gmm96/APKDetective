"""
UI sizing/layout constants shared across widgets.
"""


class LayoutConfig:
    MIN_LIST_LINES: int = 3
    # The list boxes of the forms show at most this many lines and scroll inside beyond that: a box as tall
    # as its whole content makes every scroll of the page repaint it, and for thousands of lines Tk fails.
    MAX_LIST_LINES: int = 15
    LABEL_WIDTH: int = 25

    # Tag name shared between the line-marker and the copy context menu
    MARKED_LINE_TAG: str = "marked_line"

    FIELD_PADX: int = 10
    FIELD_PADY: int = 5
