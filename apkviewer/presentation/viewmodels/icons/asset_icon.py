from dataclasses import dataclass


@dataclass(frozen=True)
class AssetIcon:
    """A PNG icon shipped with the application; `path` is relative to the assets, as IconLoader expects."""
    path: str
