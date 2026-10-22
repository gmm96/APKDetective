"""
Windows implementation of OsFileOpener: default-app open via os.startfile,
and the native "Open with..." picker via shell32's SHOpenWithDialog.
"""

import ctypes
import os
from ctypes import wintypes

from apkviewer.ports.system.os_file_opener_port import OsFileOpenerPort
from apkviewer.infrastructure.os_integration.windows_open_as_info import OpenAsInfo


class WindowsFileOpener(OsFileOpenerPort):
    _OAIF_EXEC: int = 0x00000004
    _OAIF_HIDE_REGISTRATION: int = 0x00000020

    def open(self, path: str) -> None:
        getattr(os, "startfile")(path)  # only exists on Windows

    def open_with(self, path: str) -> None:
        info = OpenAsInfo(path, None, self._OAIF_EXEC | self._OAIF_HIDE_REGISTRATION)
        shell32 = ctypes.WinDLL("shell32", use_last_error=True)     # type: ignore[attr-defined]
        shell32.SHOpenWithDialog.argtypes = [wintypes.HWND, ctypes.POINTER(OpenAsInfo)]
        shell32.SHOpenWithDialog.restype = wintypes.LONG
        result = shell32.SHOpenWithDialog(None, ctypes.byref(info))
        if result != 0:
            raise OSError(f"SHOpenWithDialog failed with HRESULT 0x{result & 0xffffffff:08X}")
