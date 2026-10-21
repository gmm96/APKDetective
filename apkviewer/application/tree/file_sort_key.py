"""
The properties a file tree can be ordered by. Toolkit-agnostic: the front end
only translates its own column identifiers into a FileSortKey.
"""

from enum import Enum


class FileSortKey(Enum):
    NAME = "name"
    TYPE = "type"
    SIZE = "size"
    COMPRESSED = "compressed"
    MODIFIED = "modified"
