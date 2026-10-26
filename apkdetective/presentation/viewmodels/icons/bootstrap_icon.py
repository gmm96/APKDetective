from dataclasses import dataclass


@dataclass(frozen=True)
class BootstrapIcon:
    """An icon of the Bootstrap Icons set that ttkbootstrap bundles, by its name (e.g. "palette")."""
    name: str
