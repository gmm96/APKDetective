"""
Every component declared in the manifest.
"""

from dataclasses import dataclass

from apkviewer.domain.entities.component import Component
from apkviewer.domain.entities.component_kind import ComponentKind
from apkviewer.domain.entities.exported_intent import ExportedIntent


@dataclass(frozen=True)
class DeclaredComponents:
    items: tuple[Component, ...] = ()

    def of_kind(self, *kinds: ComponentKind) -> tuple[Component, ...]:
        return tuple(component for component in self.items if component.kind in kinds)

    def exported_intents(self) -> tuple[ExportedIntent, ...]:
        """
        Every action of every filter of the components that may be exported,
        one entry each. Components whose exported value could not be resolved
        are included rather than hidden.
        """
        intents = {
            ExportedIntent(
                name=action,
                component_name=component.name,
                component_kind=component.kind,
                categories=intent_filter.categories,
                data=intent_filter.data,
                auto_verify=intent_filter.auto_verify,
            ): None
            for component in self.items
            if component.may_be_exported
            for intent_filter in component.intent_filters
            for action in intent_filter.actions
        }
        return tuple(sorted(intents, key=lambda i: (i.name.lower(), i.component_name)))
