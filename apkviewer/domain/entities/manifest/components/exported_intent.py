"""
One action of one intent filter of a component that may be exported: the
flattened view of the manifest that tells how another app can reach it.
"""

from dataclasses import dataclass

from apkviewer.domain.entities.manifest.components.component_kind_enum import ComponentKindEnum
from apkviewer.domain.entities.manifest.intents.intent_data import IntentData


@dataclass(frozen=True)
class ExportedIntent:
    name: str
    component_name: str
    component_kind: ComponentKindEnum
    categories: tuple[str, ...] = ()
    data: tuple[IntentData, ...] = ()
    auto_verify: bool = False
