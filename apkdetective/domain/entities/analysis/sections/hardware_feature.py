"""
A hardware or software feature the app declares with <uses-feature>.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HardwareFeature:
    """`required` is None when android:required can't be resolved."""
    name: str
    required: bool | None = True  # android:required defaults to true

    def as_text(self) -> str:
        status = {True: "Required", False: "Optional", None: "Required status unknown"}[self.required]
        return f"{self.name} ({status})"
