from dataclasses import dataclass


@dataclass(frozen=True)
class ColorPair:
    """A background and the text color that reads well on it."""
    background: str
    foreground: str
