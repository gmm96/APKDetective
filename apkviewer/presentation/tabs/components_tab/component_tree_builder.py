"""
Maps the component/intent entities into RecordNode rows. Pure functions
of the entities: no Tk involved, so they are easy to test.
"""

from collections.abc import Sequence
from dataclasses import replace

from apkviewer.domain.entities.manifest.components.component import Component
from apkviewer.domain.entities.manifest.components.component_kind_enum import ComponentKindEnum
from apkviewer.domain.entities.manifest.components.declared_components import DeclaredComponents
from apkviewer.domain.entities.manifest.components.export_state_enum import ExportStateEnum
from apkviewer.domain.entities.manifest.components.exported_intent import ExportedIntent
from apkviewer.domain.entities.manifest.intents.intent_filter import IntentFilter
from apkviewer.domain.entities.manifest.components.manifest_element import ManifestElement
from apkviewer.presentation.viewmodels.tree.record_node import RecordNode


class ComponentTreeBuilder:
    # (category key, label) of the groups the components tab can restrict to.
    GROUPS: tuple[tuple[str, str], ...] = (
        ("activity", "Activities"),
        ("service", "Services"),
        ("receiver", "Receivers"),
        ("provider", "Providers"),
    )
    _KIND_GROUPS: dict[ComponentKindEnum, str] = {
        ComponentKindEnum.ACTIVITY: "activity",
        ComponentKindEnum.ACTIVITY_ALIAS: "activity",
        ComponentKindEnum.SERVICE: "service",
        ComponentKindEnum.RECEIVER: "receiver",
        ComponentKindEnum.PROVIDER: "provider",
    }

    _MAX_SUMMARY: int = 110
    _MAX_INLINE_ATTRIBUTES: int = 3
    _EXPORT_LABELS: dict[ExportStateEnum, str] = {
        ExportStateEnum.EXPORTED: "yes",
        ExportStateEnum.NOT_EXPORTED: "no",
        ExportStateEnum.IMPLICIT_EXPORTED: "yes (implicit)",
        ExportStateEnum.IMPLICIT_NOT_EXPORTED: "no (implicit)",
        ExportStateEnum.UNRESOLVED: "unknown",
    }

    def build_components(self, components: DeclaredComponents) -> RecordNode:
        rows = tuple(
            self._component_row(f"component:{index}", component)
            for index, component in enumerate(components.items)
        )
        return replace(RecordNode.create_root(), children=rows)

    def build_intents(self, intents: Sequence[ExportedIntent]) -> RecordNode:
        rows = tuple(
            RecordNode(
                iid=f"intent:{index}",
                cells=(
                    intent.name,
                    intent.component_name,
                    intent.component_kind.value,
                    ", ".join(intent.categories),
                    ", ".join(text for text in (d.as_text() for d in intent.data) if text),
                    "yes" if intent.auto_verify else "",
                ),
            )
            for index, intent in enumerate(intents)
        )
        return replace(RecordNode.create_root(), children=rows)

    # --- Components ------------------------------------------------------------

    def _component_row(self, iid: str, component: Component) -> RecordNode:
        properties = [
            self._field(f"{iid}/properties/attribute:{name}", name, value)
            for name, value in component.attributes
        ]
        properties += [
            self._element_row(f"{iid}/properties/element{index}", element)
            for index, element in enumerate(component.elements)
        ]
        filters = [
            self._filter_row(f"{iid}/filters/filter{index}", intent_filter)
            for index, intent_filter in enumerate(component.intent_filters)
        ]
        children = []
        if properties:  # what the manifest declares on the component itself
            children.append(
                RecordNode(f"{iid}/properties", (f"Properties ({len(properties)})",), tuple(properties))
            )
        if filters:  # the conditions under which other apps can reach it; shown open
            children.append(
                RecordNode(
                    f"{iid}/filters", (f"Intent filters ({len(filters)})",), tuple(filters),
                    open_by_default=True,
                )
            )
        return RecordNode(
            iid=iid,
            cells=(
                component.name,
                component.kind.value,
                self._EXPORT_LABELS[component.export_state],
                component.permission or "—",
            ),
            children=tuple(children),
            category=self._KIND_GROUPS[component.kind],
        )

    def _element_row(self, iid: str, element: ManifestElement) -> RecordNode:
        """Small elements (meta-data...) fit one line; bigger ones expand into their attributes."""
        if len(element.attributes) <= self._MAX_INLINE_ATTRIBUTES:
            text = ", ".join(f"{name}={value}" for name, value in element.attributes)
            return RecordNode(iid, (f"{element.tag} = {text}" if text else element.tag,))
        return RecordNode(
            iid,
            (element.tag,),
            children=tuple(
                self._field(f"{iid}/{name}", name, value) for name, value in element.attributes
            ),
        )

    def _filter_row(self, iid: str, intent_filter: IntentFilter) -> RecordNode:
        """One line per property; the properties that hold several values list them with commas."""
        data = [text for text in (d.as_text() for d in intent_filter.data) if text]
        properties = (
            ("actions", ", ".join(intent_filter.actions)),
            ("categories", ", ".join(intent_filter.categories)),
            ("data", ", ".join(data)),
            ("autoVerify", "true" if intent_filter.auto_verify else ""),
        )
        return RecordNode(
            iid,
            (self._filter_summary(intent_filter, data),),
            children=tuple(
                self._field(f"{iid}/{key}", key, value) for key, value in properties if value
            ),
        )

    @classmethod
    def _filter_summary(cls, intent_filter: IntentFilter, data: list[str]) -> str:
        """What tells one filter from another when it is closed: its actions and its data."""
        parts = [", ".join(intent_filter.actions), ", ".join(data)]
        summary = " · ".join(part for part in parts if part)
        if len(summary) > cls._MAX_SUMMARY:
            summary = summary[: cls._MAX_SUMMARY - 1] + "…"
        return f"Intent filter: {summary}" if summary else "Intent filter"

    @staticmethod
    def _field(iid: str, key: str, value: str) -> RecordNode:
        return RecordNode(iid, (f"{key} = {value}",))
