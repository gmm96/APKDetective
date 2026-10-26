import tkinter as tk

import ttkbootstrap as ttkb


class WrapFrame(ttkb.Frame):
    """
    A frame that arranges its children like text, wrapping them to the next
    line when they reach the right edge.

    The children are placed by this frame, which lays them out again whenever
    its own width or the size of any child changes (e.g. the text of a button
    grows), so they never end up on top of each other.
    """
    def __init__(self, parent: tk.Misc, padding_x: int = 5, padding_y: int = 5, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._padding_x = padding_x
        self._padding_y = padding_y
        self._pending_layout: str | None = None
        self._watched_children: set[str] = set()
        self._positions: dict[str, tuple[int, int]] = {}
        self.bind("<Configure>", self._schedule_layout)

    def destroy(self) -> None:
        if self._pending_layout is not None:
            self.after_cancel(self._pending_layout)
            self._pending_layout = None
        super().destroy()

    def _schedule_layout(self, _event: tk.Event | None = None) -> None:
        # Several changes (a resize, a few buttons updating their text) are laid out in one go.
        if self._pending_layout is None:
            self._pending_layout = self.after_idle(self._layout)

    def _watch(self, child: tk.Widget) -> None:
        """A child that changes size (its text changed, it was restyled...) needs the rows to be recomputed."""
        if str(child) not in self._watched_children:
            self._watched_children.add(str(child))
            child.bind("<Configure>", self._schedule_layout, add="+")

    def _layout(self) -> None:
        self._pending_layout = None
        available_width = self.winfo_width()
        if available_width <= 0:
            return

        valid_children = [child for child in self.winfo_children() if isinstance(child, tk.Widget)]
        if not valid_children:
            return
        for child in valid_children:
            self._watch(child)

        # 1. Group children into rows based on available width
        rows: list[list[tk.Widget]] = []
        current_row: list[tk.Widget] = []
        current_row_width = 0

        for child in valid_children:
            child_width = child.winfo_reqwidth()

            # If adding this child exceeds the width (and the row is not empty), wrap
            if current_row and (current_row_width + child_width > available_width):
                rows.append(current_row)
                current_row = [child]
                current_row_width = child_width + self._padding_x
            else:
                current_row.append(child)
                current_row_width += child_width + self._padding_x

        if current_row:
            rows.append(current_row)

        # 2. Place children row by row, calculating the starting X to center them
        y = 0
        for row in rows:
            # Calculate the exact width of the items in the current row
            row_width = sum(child.winfo_reqwidth() for child in row) + self._padding_x * (len(row) - 1)

            # Center the row by dividing the remaining space by 2
            x = max(0, (available_width - row_width) // 2)
            row_max_height = 0

            for child in row:
                self._place(child, x, y)
                x += child.winfo_reqwidth() + self._padding_x
                row_max_height = max(row_max_height, child.winfo_reqheight())

            y += row_max_height + self._padding_y

        # Adjust the frame's height to fit all rows (removing the trailing padding_y)
        required_height = max(0, y - self._padding_y)
        if self.cget("height") != required_height:
            self.configure(height=required_height)

    def _place(self, child: tk.Widget, x: int, y: int) -> None:
        """Places `child` unless it is already there, so a stable layout produces no more events."""
        if self._positions.get(str(child)) != (x, y) or child.winfo_manager() != "place":
            child.place(x=x, y=y)
            self._positions[str(child)] = (x, y)
