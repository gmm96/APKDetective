"""
A screen density the app has resources for.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenDensity:
    """`name`: how the density is called ("xhdpi (320dpi)", "280dpi"); `description`: what it means."""
    name: str
    description: str

    def as_text(self) -> str:
        return f"{self.name}: {self.description}"
