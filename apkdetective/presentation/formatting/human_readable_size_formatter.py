"""
Formats byte counts as B / KB / MB / GB / TB, as most file browsers do.
"""

from apkdetective.ports.formatting.size_formatter_port import SizeFormatterPort


class HumanReadableSizeFormatter(SizeFormatterPort):
    _UNITS: tuple[str, ...] = ("B", "KB", "MB", "GB", "TB")

    def format(self, num_bytes: int, full_mode: bool = False) -> str:
        size = float(num_bytes)
        unit = self._UNITS[0]
        for unit in self._UNITS:
            if size < 1024.0 or unit == self._UNITS[-1]:
                break
            size /= 1024.0
        readable = f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        return f"{readable} ({num_bytes:,} B)" if full_mode else readable
