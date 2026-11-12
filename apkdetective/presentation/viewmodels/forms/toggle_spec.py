from typing import NamedTuple


class ToggleSpec(NamedTuple):
    """What a read-only toggle shows: its text and, optionally, a tooltip that explains it."""
    text: str
    description: str | None = None
