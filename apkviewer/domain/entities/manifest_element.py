"""
A child element of a component other than <intent-filter> (meta-data, layout, ...).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ManifestElement:
    tag: str
    attributes: tuple[tuple[str, str], ...] = ()
