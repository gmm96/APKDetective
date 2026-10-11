"""
A component declared in the manifest, with its intent filters.
"""

from dataclasses import dataclass

from apkviewer.domain.entities.component_kind import ComponentKind
from apkviewer.domain.entities.export_state import ExportState
from apkviewer.domain.entities.intent_filter import IntentFilter
from apkviewer.domain.entities.manifest_element import ManifestElement


@dataclass(frozen=True)
class Component:
    name: str
    kind: ComponentKind
    export_state: ExportState
    permission: str | None = None
    intent_filters: tuple[IntentFilter, ...] = ()
    # Every other attribute / child element the manifest declares for it, in manifest order.
    attributes: tuple[tuple[str, str], ...] = ()
    elements: tuple[ManifestElement, ...] = ()

    @property
    def may_be_exported(self) -> bool:
        return self.export_state.may_be_exported
