"""
Windows implementation of ClipboardFileCopier, using the CF_HDROP
clipboard format through user32 / kernel32.
"""

import ctypes
from ctypes import wintypes
from typing import Any

from apkviewer.domain.interfaces.clipboard_file_copier import ClipboardFileCopier
from apkviewer.infrastructure.clipboard.windows_drop_files import DropFiles


class WindowsClipboardFileCopier(ClipboardFileCopier):
    _GHND: int = 0x0042  # GMEM_MOVEABLE | GMEM_ZEROINIT
    _CF_HDROP: int = 15

    def copy(self, file_paths: list[str]) -> bool:
        try:
            return self._copy(file_paths)
        except (AttributeError, OSError, ctypes.ArgumentError):  # AttributeError: not running on Windows
            return False

    def _copy(self, file_paths: list[str]) -> bool:
        user32 = ctypes.WinDLL("user32", use_last_error=True)   # type: ignore[attr-defined]
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)   # type: ignore[attr-defined]
        self._declare_prototypes(user32, kernel32)

        file_bytes = ("\0".join(file_paths) + "\0\0").encode("utf-16le")
        header = DropFiles()
        header.pFiles = ctypes.sizeof(DropFiles)
        header.fWide = True

        handle = kernel32.GlobalAlloc(self._GHND, ctypes.sizeof(DropFiles) + len(file_bytes))
        if not handle:
            return False
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            kernel32.GlobalFree(handle)
            return False
        ctypes.memmove(pointer, ctypes.addressof(header), ctypes.sizeof(DropFiles))
        ctypes.memmove(pointer + ctypes.sizeof(DropFiles), file_bytes, len(file_bytes))
        kernel32.GlobalUnlock(handle)

        if not user32.OpenClipboard(None):
            kernel32.GlobalFree(handle)
            return False
        try:
            user32.EmptyClipboard()
            if not user32.SetClipboardData(self._CF_HDROP, handle):
                kernel32.GlobalFree(handle)  # the clipboard did not take the memory over
                return False
            return True
        finally:
            user32.CloseClipboard()

    @staticmethod
    def _declare_prototypes(user32: Any, kernel32: Any) -> None:
        """
        Without explicit prototypes ctypes treats every return value as a 32-bit int, which
        truncates the memory addresses of a 64-bit process.
        """
        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = wintypes.BOOL
        kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalFree.restype = wintypes.HGLOBAL
        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.EmptyClipboard.restype = wintypes.BOOL
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        user32.SetClipboardData.restype = wintypes.HANDLE
        user32.CloseClipboard.restype = wintypes.BOOL
