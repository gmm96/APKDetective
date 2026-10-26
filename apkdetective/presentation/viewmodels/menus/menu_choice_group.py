from collections.abc import Sequence
from dataclasses import dataclass

from apkdetective.presentation.viewmodels.menus.menu_choice import MenuChoice
from apkdetective.presentation.viewmodels.icons.asset_icon import AssetIcon
from apkdetective.presentation.viewmodels.icons.bootstrap_icon import BootstrapIcon


@dataclass(frozen=True)
class MenuChoiceGroup:
    """Mutually exclusive options, shown as a submenu of radio entries titled like the group."""
    key: str
    title: str
    choices: Sequence[MenuChoice]
    selected_key: str
    icon: AssetIcon | BootstrapIcon | None = None
