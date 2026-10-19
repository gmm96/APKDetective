from collections.abc import Sequence
from dataclasses import dataclass

from .app_toolbar_choice import AppToolbarChoice


@dataclass(frozen=True)
class AppToolbarChoiceGroup:
    """Mutually exclusive options, shown as a submenu of radio entries titled like the group."""
    key: str
    title: str
    choices: Sequence[AppToolbarChoice]
    selected_key: str
