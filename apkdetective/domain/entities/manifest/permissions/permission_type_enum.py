""" Type of the permission, as defined by the Android framework. """

from enum import Enum


class PermissionTypeEnum(Enum):
    PERMISSION = "permission"
    APPOPS = "appops"
    CUSTOM = "custom"
