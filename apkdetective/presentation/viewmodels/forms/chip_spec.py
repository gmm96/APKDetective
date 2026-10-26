from typing import NamedTuple


class ChipSpec(NamedTuple):
    """What a chip shows: its text, its kind (see FormPanel.CHIP_KINDS) and, optionally, a tooltip."""
    text: str
    kind: str
    description: str | None = None
