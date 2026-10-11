"""
The DROPFILES header that precedes the file list of the CF_HDROP clipboard format.
"""

import ctypes
from ctypes import wintypes


class DropFiles(ctypes.Structure):
    _fields_ = [
        ("pFiles", wintypes.DWORD),
        ("pt", wintypes.POINT),
        ("fNC", wintypes.BOOL),
        ("fWide", wintypes.BOOL),
    ]
