"""
Semantic importance of a status-bar message; the palette decides its color.
"""

from enum import Enum


class StatusLevelEnum(Enum):
    NEUTRAL = "neutral"
    INFO = "info"
    SUCCESS = "success"
    ERROR = "error"
