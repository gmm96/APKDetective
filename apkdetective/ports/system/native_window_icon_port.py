"""
Port for giving a window its icon through the operating system itself, for the platforms where the GUI toolkit does
not manage to do it by its own means.
"""

from abc import ABC, abstractmethod


class NativeWindowIconPort(ABC):
    @abstractmethod
    def apply(self, window_handle: int, icon_path: str) -> None:
        """
        Set the icon found at `icon_path` on the window that `window_handle` belongs to, so that it shows in the
        title bar as well as in the taskbar.

        `window_handle` is the native handle of the window (or of any window inside it) and must already exist on
        screen. Does nothing on a platform that needs no help, and never raises: an icon is not worth a crash.
        """
        raise NotImplementedError
