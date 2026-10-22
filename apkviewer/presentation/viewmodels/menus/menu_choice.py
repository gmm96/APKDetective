from collections.abc import Callable
from dataclasses import dataclass

from apkviewer.presentation.viewmodels.icons.asset_icon import AssetIcon
from apkviewer.presentation.viewmodels.icons.bootstrap_icon import BootstrapIcon


@dataclass(frozen=True)
class MenuChoice:
    key: str
    label: str
    command: Callable[[], None]
    icon: AssetIcon | BootstrapIcon | None = None
