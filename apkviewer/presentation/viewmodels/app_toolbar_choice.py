from collections.abc import Callable
from dataclasses import dataclass

from apkviewer.presentation.viewmodels.asset_icon import AssetIcon
from apkviewer.presentation.viewmodels.bootstrap_icon import BootstrapIcon


@dataclass(frozen=True)
class AppToolbarChoice:
    key: str
    label: str
    command: Callable[[], None]
    icon: AssetIcon | BootstrapIcon | None = None
