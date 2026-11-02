from dataclasses import dataclass


@dataclass(frozen=True)
class ResourcesRemovedConfig:
    """The configuration of a chunk of resources that was removed: the language and the screen it was for."""
    package_index: int
    type_name: str
    config: bytes  # the ResTable_config structure, as it is in the file
