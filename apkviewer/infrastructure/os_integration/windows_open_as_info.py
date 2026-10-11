"""
The OPENASINFO structure taken by the shell's "Open with..." dialog.
"""

import ctypes
from ctypes import wintypes


class OpenAsInfo(ctypes.Structure):
    _fields_ = [
        ("pcszFile", wintypes.LPCWSTR),
        ("pcszClass", wintypes.LPCWSTR),
        ("oaifInFlags", wintypes.DWORD),
    ]
