"""
Windows implementation of NativeWindowIconPort.

Windows draws two icons per window: a big one (taskbar, Alt+Tab) and a small one (the title bar). Tk does not always
set the small one (`iconbitmap` / `iconphoto` leave the title bar with the generic icon of Windows), so both are
loaded here from the .ico file at the exact size the system asks for at the DPI of the window, and handed to the
window with WM_SETICON. They are also set as the icons of the window class, which keeps them if the toolkit rebuilds
the frame of the window and gives every other window of the application the same icon.
"""

import ctypes
from ctypes import wintypes
from typing import Any

from apkdetective.ports.system.native_window_icon_port import NativeWindowIconPort


class WindowsNativeWindowIcon(NativeWindowIconPort):
    _WM_SETICON: int = 0x0080
    _ICON_SMALL: int = 0
    _ICON_BIG: int = 1
    _IMAGE_ICON: int = 1
    _LR_LOADFROMFILE: int = 0x0010
    _GA_ROOT: int = 2
    _GCLP_HICON: int = -14
    _GCLP_HICONSM: int = -34
    _SM_CXICON: int = 11
    _SM_CYICON: int = 12
    _SM_CXSMICON: int = 49
    _SM_CYSMICON: int = 50
    _DEFAULT_DPI: int = 96

    def __init__(self) -> None:
        # The icons must outlive the window: Windows only borrows them.
        self._loaded_icons: list[int] = []

    def apply(self, window_handle: int, icon_path: str) -> None:
        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)  # type: ignore[attr-defined]
            self._declare_signatures(user32)
            # The handle of a Tk window is the one of its client area; the title bar belongs to the frame around it.
            frame: int = user32.GetAncestor(window_handle, self._GA_ROOT) or window_handle
            dpi: int = self._dpi_of(user32, frame)
            small = self._load(user32, icon_path, self._SM_CXSMICON, self._SM_CYSMICON, dpi)
            big = self._load(user32, icon_path, self._SM_CXICON, self._SM_CYICON, dpi)
        except (AttributeError, OSError, ctypes.ArgumentError):  # AttributeError: not running on Windows
            return
        for icon, message_size, class_slot in (
            (small, self._ICON_SMALL, self._GCLP_HICONSM),
            (big, self._ICON_BIG, self._GCLP_HICON),
        ):
            if icon:
                user32.SendMessageW(frame, self._WM_SETICON, message_size, icon)
                self._set_class_icon(user32, frame, class_slot, icon)

    def _load(self, user32: Any, icon_path: str, width_metric: int, height_metric: int, dpi: int) -> int:
        """The HICON of the file at the size Windows uses for that kind of icon; 0 if it can't be loaded."""
        handle = user32.LoadImageW(
            None,
            icon_path,
            self._IMAGE_ICON,
            self._metric(user32, width_metric, dpi),
            self._metric(user32, height_metric, dpi),
            self._LR_LOADFROMFILE,
        )
        if handle:
            self._loaded_icons.append(handle)
        return handle or 0

    def _metric(self, user32: Any, index: int, dpi: int) -> int:
        for_dpi = getattr(user32, "GetSystemMetricsForDpi", None)  # Windows 10 1607 and later
        if for_dpi is not None:
            return int(for_dpi(index, dpi))
        return int(user32.GetSystemMetrics(index))

    def _dpi_of(self, user32: Any, window: int) -> int:
        dpi_of_window = getattr(user32, "GetDpiForWindow", None)  # Windows 10 1607 and later
        return int(dpi_of_window(window)) if dpi_of_window is not None else self._DEFAULT_DPI

    def _set_class_icon(self, user32: Any, window: int, slot: int, icon: int) -> None:
        # SetClassLongPtrW does not exist in 32-bit Windows, where SetClassLongW is the same function.
        set_class_long = getattr(user32, "SetClassLongPtrW", None) or user32.SetClassLongW
        set_class_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
        set_class_long.restype = ctypes.c_size_t
        set_class_long(window, slot, icon)

    @staticmethod
    def _declare_signatures(user32: Any) -> None:
        """Without explicit prototypes ctypes treats handles as 32-bit ints, which truncates them in 64-bit Windows."""
        user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        user32.GetAncestor.restype = wintypes.HWND
        user32.LoadImageW.argtypes = [
            wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT,
        ]
        user32.LoadImageW.restype = wintypes.HANDLE
        user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.SendMessageW.restype = wintypes.LPARAM
        user32.GetSystemMetrics.argtypes = [ctypes.c_int]
        user32.GetSystemMetrics.restype = ctypes.c_int
        if hasattr(user32, "GetSystemMetricsForDpi"):
            user32.GetSystemMetricsForDpi.argtypes = [ctypes.c_int, wintypes.UINT]
            user32.GetSystemMetricsForDpi.restype = ctypes.c_int
        if hasattr(user32, "GetDpiForWindow"):
            user32.GetDpiForWindow.argtypes = [wintypes.HWND]
            user32.GetDpiForWindow.restype = wintypes.UINT
