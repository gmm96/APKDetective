"""
What the DEX files of an APK contain that the analysis cares about.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DexContents:
    strings: tuple[str, ...] = ()
    class_names: tuple[str, ...] = ()  # type descriptors, e.g. "Lcom/example/Main;"
