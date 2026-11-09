"""
What the DEX files of an APK contain that the detection of trackers looks at.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DexContents:
    class_names: tuple[str, ...] = ()  # type descriptors, e.g. "Lcom/example/Main;"
