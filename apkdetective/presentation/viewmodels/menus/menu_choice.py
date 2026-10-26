from collections.abc import Callable
from dataclasses import dataclass

from apkdetective.presentation.viewmodels.icons.asset_icon import AssetIcon
from apkdetective.presentation.viewmodels.icons.bootstrap_icon import BootstrapIcon


@dataclass(frozen=True)
class MenuChoice:
    key: str
    label: str
    command: Callable[[], None]
    icon: AssetIcon | BootstrapIcon | None = None
