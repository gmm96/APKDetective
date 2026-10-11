"""
One action of one intent filter of a component that may be exported: the
flattened view of the manifest that tells how another app can reach it.
"""

from dataclasses import dataclass

from apkviewer.domain.entities.component_kind import ComponentKind
from apkviewer.domain.entities.intent_data import IntentData


@dataclass(frozen=True)
class ExportedIntent:
    name: str
    component_name: str
    component_kind: ComponentKind
    categories: tuple[str, ...] = ()
    data: tuple[IntentData, ...] = ()
    auto_verify: bool = False
