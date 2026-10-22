from collections.abc import Sequence
from dataclasses import dataclass

from apkviewer.presentation.viewmodels.menus.menu_choice import MenuChoice
from apkviewer.presentation.viewmodels.icons.asset_icon import AssetIcon
from apkviewer.presentation.viewmodels.icons.bootstrap_icon import BootstrapIcon


@dataclass(frozen=True)
class MenuChoiceGroup:
    """Mutually exclusive options, shown as a submenu of radio entries titled like the group."""
    key: str
    title: str
    choices: Sequence[MenuChoice]
    selected_key: str
    icon: AssetIcon | BootstrapIcon | None = None
