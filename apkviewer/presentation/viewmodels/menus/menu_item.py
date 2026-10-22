from collections.abc import Callable
from dataclasses import dataclass

from apkviewer.presentation.viewmodels.icons.asset_icon import AssetIcon
from apkviewer.presentation.viewmodels.icons.bootstrap_icon import BootstrapIcon


@dataclass(frozen=True)
class MenuItem:
    key: str
    label: str
    command: Callable[[], None]
    icon: AssetIcon | BootstrapIcon | None = None
    accelerator: str | None = None
    shortcut: str | None = None
