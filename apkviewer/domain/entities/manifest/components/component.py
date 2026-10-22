"""
A component declared in the manifest, with its intent filters.
"""

from dataclasses import dataclass

from apkviewer.domain.entities.manifest.components.component_kind_enum import ComponentKindEnum
from apkviewer.domain.entities.manifest.components.export_state_enum import ExportStateEnum
from apkviewer.domain.entities.manifest.intents.intent_filter import IntentFilter
from apkviewer.domain.entities.manifest.components.manifest_element import ManifestElement


@dataclass(frozen=True)
class Component:
    name: str
    kind: ComponentKindEnum
    export_state: ExportStateEnum
    permission: str | None = None
    intent_filters: tuple[IntentFilter, ...] = ()
    # Every other attribute / child element the manifest declares for it, in manifest order.
    attributes: tuple[tuple[str, str], ...] = ()
    elements: tuple[ManifestElement, ...] = ()

    @property
    def may_be_exported(self) -> bool:
        return self.export_state.may_be_exported
