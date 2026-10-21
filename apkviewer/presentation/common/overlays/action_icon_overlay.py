import tkinter as tk
from abc import ABC, abstractmethod

from apkviewer.presentation.common.overlays.overlay_icon import OverlayIcon


class ActionIconOverlay(ABC):
    """
    Base of the icons overlaid on a field that run an action when clicked (copy, clear...).

    It owns what every such overlay shares: the icon, the target it covers and the sync of
    the icon background when the target gains or loses the focus. Subclasses decide when the
    icon is visible (refresh) and what the click does (_activate).
    """

    def __init__(
        self,
        target: tk.Widget,
        icon_name: str,
        icon_color: str,
        background: str | None = None,
        top_offset: int | None = None,
        right_offset: int | None = None,
    ) -> None:
        self._target: tk.Widget = target
        self._icon: OverlayIcon = OverlayIcon(
            target=target,
            icon_name=icon_name,
            icon_color=icon_color,
            background=background,
            on_click=self._activate,
            top_offset=top_offset,
            right_offset=right_offset,
        )
        target.bind("<FocusIn>", lambda _event: self._focus_changed(True), add="+")
        target.bind("<FocusOut>", lambda _event: self._focus_changed(False), add="+")

    @abstractmethod
    def refresh(self) -> None:
        """Shows or hides the icon according to the overlay's visibility rule."""

    @abstractmethod
    def _activate(self, event: tk.Event | None = None) -> str:
        """Runs the icon's action. Must return "break" to stop the event propagation."""

    def _focus_changed(self, focused: bool) -> None:
        """Hook called when the target gains or loses the focus; subclasses may extend it."""
        self._icon.refresh_background()
