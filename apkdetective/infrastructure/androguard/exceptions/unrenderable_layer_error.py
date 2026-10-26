"""
Raised when a layer of an adaptive icon is not an image or a color
(e.g. a vector drawable), so the icon can't be composed.
"""


class UnrenderableLayerError(Exception):
    pass
