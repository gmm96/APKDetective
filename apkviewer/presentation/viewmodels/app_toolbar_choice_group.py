from collections.abc import Sequence
from dataclasses import dataclass

from apkviewer.presentation.viewmodels.app_toolbar_choice import AppToolbarChoice
from apkviewer.presentation.viewmodels.asset_icon import AssetIcon
from apkviewer.presentation.viewmodels.bootstrap_icon import BootstrapIcon


@dataclass(frozen=True)
class AppToolbarChoiceGroup:
    """Mutually exclusive options, shown as a submenu of radio entries titled like the group."""
    key: str
    title: str
    choices: Sequence[AppToolbarChoice]
    selected_key: str
    icon: AssetIcon | BootstrapIcon | None = None
