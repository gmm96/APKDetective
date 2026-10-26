"""
Where a permission comes from, as far as this app is concerned.
"""

from enum import Enum


class PermissionOriginEnum(Enum):
    REQUESTED = "Requested"
    DECLARED = "Declared by this app"
    DECLARED_AND_REQUESTED = "Declared and requested"
