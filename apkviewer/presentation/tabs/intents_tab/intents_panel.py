"""
"Intents" tab: a flat table with one row per entry point of the app
(action + the exported component that answers it), the combination
needed to launch it from adb, Tasker or another app.
"""

import tkinter as tk
from collections.abc import Sequence

import ttkbootstrap as ttkb
import ttkbootstrap.constants as ttkb_constants

from apkviewer.domain.entities.manifest.components.exported_intent import ExportedIntent
from apkviewer.presentation.viewmodels.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.tree.record_table_panel import RecordTablePanel
from apkviewer.presentation.common.feedback.warning_banner import WarningBanner
from apkviewer.presentation.viewmodels.tree.tree_column import TreeColumn
from apkviewer.presentation.tabs.components_tab.component_tree_builder import ComponentTreeBuilder


class IntentsPanel(ttkb.Frame):
    _COLUMNS: tuple[TreeColumn, ...] = (
        TreeColumn(
            "#0",
            "Action",
            width=280,
            min_width=160,
            stretch=True,
            tooltip="The action the intent filter answers, for example android.intent.action.VIEW."
        ),
        TreeColumn(
            "component",
            "Component",
            width=300,
            min_width=140,
            stretch=True,
            tooltip="The exported component that answers the action."
        ),
        TreeColumn(
            "type",
            "Type",
            width=100,
            min_width=70,
            tooltip="Kind of that component: activity, service, receiver or provider."
        ),
        TreeColumn(
            "categories",
            "Categories",
            width=190,
            min_width=100,
            tooltip="Categories the filter requires, without the android.intent.category. prefix."
        ),
        TreeColumn(
            "data",
            "Data",
            width=220,
            min_width=100,
            stretch=True,
            tooltip="The URIs (scheme, host, path...) and MIME types the filter accepts."
        ),
        TreeColumn(
            "verify",
            "Auto-verify",
            width=100,
            min_width=80,
            tooltip="Whether the filter asks Android to verify that the app owns its web links (android:autoVerify)."
        ),
    )

    def __init__(
        self,
        parent: ttkb.Notebook,
        palette: ThemePalette,
        tree_builder: ComponentTreeBuilder | None = None,
    ) -> None:
        super().__init__(parent)
        self._tree_builder: ComponentTreeBuilder = tree_builder or ComponentTreeBuilder()
        self._table: RecordTablePanel = RecordTablePanel(
            self,
            palette,
            self._COLUMNS,
            item_noun="entry points",
            empty_text="No exported intents.",
            bootstyle=ttkb_constants.PRIMARY
        )
        self._table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._banner: WarningBanner = WarningBanner(self, palette, self._table)

    def apply_palette(self, palette: ThemePalette) -> None:
        self._table.apply_palette(palette)
        self._banner.apply_palette(palette)

    def show_warnings(self, messages: list[str]) -> None:
        self._banner.show(messages)

    def clear(self) -> None:
        self._banner.show(())
        self._table.clear()

    def render(self, intents: Sequence[ExportedIntent]) -> None:
        self._table.show(self._tree_builder.build_intents(intents))
