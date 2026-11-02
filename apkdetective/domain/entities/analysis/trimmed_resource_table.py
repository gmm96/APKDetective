"""
What is left of a resource table (resources.arsc) after its translations have been removed, and what the
parser needs to know about them anyway.
"""

from dataclasses import dataclass

from apkdetective.domain.entities.analysis.resources_removed_config import ResourcesRemovedConfig


@dataclass(frozen=True)
class TrimmedResourceTable:
    data: bytes  # a valid resource table, without the removed chunks
    removed: tuple[ResourcesRemovedConfig, ...]
