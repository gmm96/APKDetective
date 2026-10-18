import tkinter as tk

import ttkbootstrap as ttkb


class WrapFrame(ttkb.Frame):
    """
    A frame that arranges its children like text, wrapping them to the next
    line when they reach the right edge.
    """
    def __init__(self, parent: tk.Misc, padding_x: int = 5, padding_y: int = 5, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._padding_x = padding_x
        self._padding_y = padding_y
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event: tk.Event | None = None) -> None:
        available_width = self.winfo_width()
        if available_width <= 0:
            return

        valid_children = [child for child in self.winfo_children() if isinstance(child, tk.Widget)]
        if not valid_children:
            return

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
                child.place(x=x, y=y)
                x += child.winfo_reqwidth() + self._padding_x
                row_max_height = max(row_max_height, child.winfo_reqheight())

            y += row_max_height + self._padding_y

        # Adjust the frame's height to fit all rows (removing the trailing padding_y)
        required_height = max(0, y - self._padding_y)
        if self.cget("height") != required_height:
            self.configure(height=required_height)
