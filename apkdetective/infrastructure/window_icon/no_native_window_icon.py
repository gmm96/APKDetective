"""
NativeWindowIconPort for the platforms where the toolkit's own icon (Tk's `iconphoto`) is all that is needed.
"""

from apkdetective.ports.system.native_window_icon_port import NativeWindowIconPort


class NoNativeWindowIcon(NativeWindowIconPort):
    def apply(self, window_handle: int, icon_path: str) -> None:
        """Nothing to do: the window already has its icon."""
