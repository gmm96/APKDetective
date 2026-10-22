"""
Main application window: wires together the header, status bar, tabs and
the background analysis. It is the composition root of the *presentation*
layer only: every use case and platform service it needs is handed in
from outside (see apkviewer.composition_root), so this layer never
imports the infrastructure layer.
"""

import os
import threading
import tkinter as tk
from functools import partial
from tkinter import filedialog, messagebox

import ttkbootstrap as ttkb
import ttkbootstrap.constants as ttkb_constants

from apkviewer.application.analysis.analyze_apk import AnalyzeApk
from apkviewer.application.files.entry_previewer import EntryPreviewer
from apkviewer.application.export.export_app_info import ExportAppInfo
from apkviewer.application.export.export_icon import ExportIcon
from apkviewer.application.export.extract_apk_entries import ExtractApkEntries
from apkviewer.application.appearance.resolve_color_scheme import ResolveColorScheme
from apkviewer.domain.entities.analysis.analysis_result import AnalysisResult
from apkviewer.domain.entities.analysis.analysis_section_enum import AnalysisSectionEnum
from apkviewer.domain.entities.appearance.color_mode_enum import ColorModeEnum
from apkviewer.ports.system.url_opener_port import UrlOpenerPort
from apkviewer.ports.formatting.size_formatter_port import SizeFormatterPort
from apkviewer.ports.formatting.date_formatter_port import DateFormatterPort
from apkviewer.presentation.appearance.theme_manager import ThemeManager
from apkviewer.presentation.common.dialogs.extract_to_dialog import ExtractToDialog
from apkviewer.presentation.status_bar.status_bar import StatusBar
from apkviewer.presentation.viewmodels.status_bar.status_level_enum import StatusLevelEnum
from apkviewer.presentation.common.menus.text_context_menu import TextContextMenu
from apkviewer.presentation.tabs.components_tab.components_panel import ComponentsPanel
from apkviewer.presentation.tabs.files_tab.files_panel import FilesPanel
from apkviewer.presentation.common.feedback.loading_bar import LoadingBar
from apkviewer.presentation.common.layout.notebook_lock import NotebookLock
from apkviewer.presentation.header.app_header import AppHeader
from apkviewer.presentation.common.icons.icon_loader import IconLoader
from apkviewer.presentation.tabs.info_tab.info_panel import InfoPanel
from apkviewer.presentation.tabs.intents_tab.intents_panel import IntentsPanel
from apkviewer.presentation.tabs.manifest_tab.manifest_panel import ManifestPanel
from apkviewer.presentation.tabs.permissions_tab.permissions_panel import PermissionsPanel
from apkviewer.presentation.tabs.security_tab.security_panel import SecurityPanel
from apkviewer.presentation.menu_bar.app_menu_bar import AppMenuBar
from apkviewer.presentation.menu_bar.file.file_menu import FileMenu
from apkviewer.presentation.menu_bar.help.help_menu import HelpMenu
from apkviewer.presentation.menu_bar.settings.settings_menu import SettingsMenu
from apkviewer.presentation.viewmodels.menus.menu_choice import MenuChoice
from apkviewer.presentation.viewmodels.menus.menu_choice_group import MenuChoiceGroup
from apkviewer.presentation.viewmodels.menus.menu_item import MenuItem
from apkviewer.presentation.viewmodels.icons.asset_icon import AssetIcon
from apkviewer.presentation.viewmodels.icons.bootstrap_icon import BootstrapIcon


class ApkAnalyzerApp:
    # Menu items that only make sense once an APK has been analyzed.
    _ANALYSIS_DEPENDENT_ITEMS: tuple[str, ...] = ("export_app_info", "extract_apk", "extract_icon")

    # Which parts of the analysis each tab reports problems for. The analysis only says WHAT it
    # could not read; deciding where the user is told is the job of the presentation.
    _INFO_SECTIONS: tuple[AnalysisSectionEnum, ...] = (
        AnalysisSectionEnum.APPLICATION,
        AnalysisSectionEnum.CONFIGURATION,
        AnalysisSectionEnum.EMBEDDED_CONTENT,
        AnalysisSectionEnum.DEX_METRICS,
        AnalysisSectionEnum.ICON,
    )
    _SECURITY_SECTIONS: tuple[AnalysisSectionEnum, ...] = (
        AnalysisSectionEnum.SIGNATURES,
        AnalysisSectionEnum.THIRD_PARTY,
    )
    _PERMISSIONS_SECTIONS: tuple[AnalysisSectionEnum, ...] = (AnalysisSectionEnum.PERMISSIONS,)
    _COMPONENTS_SECTIONS: tuple[AnalysisSectionEnum, ...] = (  # also for the Intents tab, derived from them
        AnalysisSectionEnum.COMPONENTS,
        AnalysisSectionEnum.MANIFEST,
    )

    _ICONS_DIR: str = "assets/icons/outline"

    def __init__(
        self,
        root: ttkb.App,
        analyze_apk: AnalyzeApk,
        extract_entries: ExtractApkEntries,
        entry_previewer: EntryPreviewer,
        export_app_info: ExportAppInfo,
        export_icon: ExportIcon,
        url_opener: UrlOpenerPort,
        resolve_color_scheme: ResolveColorScheme,
        icon_loader: IconLoader | None = None,
        size_formatter: SizeFormatterPort | None = None,
        date_formatter: DateFormatterPort | None = None,
    ) -> None:
        self.root: ttkb.App = root
        self.root.title("APKViewer")
        self.root.minsize(600, 600)
        self.root.geometry("1000x750")
        self.maximize_window()
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        self._analyze_apk: AnalyzeApk = analyze_apk
        self._entry_previewer: EntryPreviewer = entry_previewer
        self._icon_loader: IconLoader = icon_loader or IconLoader()
        self._size_formatter: SizeFormatterPort | None = size_formatter
        self._date_formatter: DateFormatterPort | None = date_formatter

        # Activates the ttk theme (AUTO = follow the OS) before any widget exists.
        self._theme: ThemeManager = ThemeManager(root, resolve_color_scheme)

        # The analysis currently shown (None while nothing is loaded).
        self._result: AnalysisResult | None = None

        extract_dialog = ExtractToDialog(root, extract_entries)
        self._extract_dialog: ExtractToDialog = extract_dialog
        self._file_actions: FileMenu = FileMenu(
            parent=root,
            extract_dialog=extract_dialog,
            export_app_info=export_app_info,
            export_icon=export_icon,
            get_result=lambda: self._result,
        )
        self._help_actions: HelpMenu = HelpMenu(root, url_opener=url_opener)
        self._settings_actions: SettingsMenu = SettingsMenu(root, self._theme)

        self.context_menu: TextContextMenu = TextContextMenu(root, self._theme.palette)
        self._build_menu()  # first: the menu bar must be packed at the very top of the window
        self._build_layout()
        self._subscribe_to_theme_changes()

    def _subscribe_to_theme_changes(self) -> None:
        for listener in (
            self.header.apply_palette,
            self.status_bar.apply_palette,
            self.context_menu.apply_palette,
            self.menu_bar.apply_palette,
            self.info_panel.apply_palette,
            self.security_panel.apply_palette,
            self.permissions_panel.apply_palette,
            self.components_panel.apply_palette,
            self.intents_panel.apply_palette,
            self.manifest_panel.apply_palette,
            self.files_panel.apply_palette,
        ):
            self._theme.subscribe(listener)

    def _build_layout(self) -> None:
        top_frame = ttkb.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=(15, 0))
        self.header: AppHeader = AppHeader(
            top_frame,
            on_load_click=self.load_apk,
            on_cancel_click=self.cancel_analysis,
            palette=self._theme.palette,
        )
        self.header.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Between the header and the tabs, in the gap that used to separate them: the load affects the
        # whole window, not a single tab, and being a strip of fixed height it moves nothing when shown.
        self.loading_bar: LoadingBar = LoadingBar(self.root)
        self.loading_bar.pack(side=tk.TOP, fill=tk.X, padx=10)
        self.status_bar: StatusBar = StatusBar(self.root, self._theme.palette)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        notebook = ttkb.Notebook(self.root, bootstyle=ttkb_constants.SECONDARY)
        notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

        palette = self._theme.palette
        self.info_panel: InfoPanel = InfoPanel(
            notebook,
            self.context_menu,
            palette,
            size_formatter=self._size_formatter,
            date_formatter=self._date_formatter,
        )
        self.security_panel: SecurityPanel = SecurityPanel(notebook, self.context_menu, palette)
        self.permissions_panel: PermissionsPanel = PermissionsPanel(notebook, palette)
        self.components_panel: ComponentsPanel = ComponentsPanel(notebook, palette)
        self.intents_panel: IntentsPanel = IntentsPanel(notebook, palette)
        self.manifest_panel: ManifestPanel = ManifestPanel(notebook, self.context_menu, palette)
        self.files_panel: FilesPanel = FilesPanel(
            notebook,
            get_default_folder_name=self._default_extract_folder_name,
            extract_dialog=self._extract_dialog,
            entry_previewer=self._entry_previewer,
            palette=palette,
            icon_loader=self._icon_loader,
        )

        notebook.add(self.info_panel, text="Info")
        notebook.add(self.security_panel, text="Security")
        notebook.add(self.permissions_panel, text="Permissions")
        notebook.add(self.components_panel, text="Components")
        notebook.add(self.intents_panel, text="Intents")
        notebook.add(self.manifest_panel, text="Manifest")
        notebook.add(self.files_panel, text="Files")
        self._tab_lock: NotebookLock = NotebookLock(notebook)

    def _build_menu(self) -> None:
        export, help_ = self._file_actions, self._help_actions
        settings = self._settings_actions
        self.menu_bar: AppMenuBar = AppMenuBar(
            self.root,
            {
                "File": [
                    MenuItem("load_apk", "Load APK", self.load_apk, self._asset_icon("android.png"), "Ctrl+O", "<Control-o>"),
                    None,
                    MenuItem("export_app_info", "Export app info", export.export_app_info, self._asset_icon("save_file.png")),
                    MenuItem("extract_apk", "Extract to...", export.extract_apk, self._asset_icon("unarchive_file.png")),
                    MenuItem("extract_icon", "Extract icon as PNG", export.extract_icon, self._asset_icon("image.png")),
                    None,
                    MenuItem("exit", "Exit", self.exit_app, self._asset_icon("exit_app.png")),
                ],
                "Settings": [
                    MenuChoiceGroup(
                        key="color_mode",
                        title="Color mode",
                        choices=(
                            MenuChoice(
                                ColorModeEnum.LIGHT.value, "Light mode",
                                lambda: settings.set_color_mode(ColorModeEnum.LIGHT),
                                self._asset_icon("light_mode.png"),
                            ),
                            MenuChoice(
                                ColorModeEnum.DARK.value, "Dark mode",
                                lambda: settings.set_color_mode(ColorModeEnum.DARK),
                                self._asset_icon("dark_mode.png"),
                            ),
                            MenuChoice(
                                ColorModeEnum.AUTO.value, "Auto (follow system)",
                                lambda: settings.set_color_mode(ColorModeEnum.AUTO),
                                self._asset_icon("auto_color_mode.png")
                            ),
                        ),
                        selected_key=settings.color_mode.value,
                        icon=BootstrapIcon("circle-half"),
                    ),
                    MenuChoiceGroup(
                        key="theme",
                        title="Theme",
                        choices=tuple(
                            MenuChoice(name, settings.theme_label(name), partial(settings.set_theme, name))
                            for name in settings.themes
                        ),
                        selected_key=settings.base_theme,
                        icon=BootstrapIcon("palette"),
                    ),
                ],
                "Help": [
                    MenuItem("source_code", "Source code", help_.open_source_code, self._asset_icon("code.png")),
                    MenuItem("report_issue", "Report issue", help_.report_issue, self._asset_icon("bug_report.png")),
                    MenuItem("about", "About", help_.show_about, self._asset_icon("info.png")),
                ],
            },
            self._theme.palette,
            icon_loader=self._icon_loader,
        )
        self.menu_bar.set_enabled(self._ANALYSIS_DEPENDENT_ITEMS, False)

    # --- Public actions ----------------------------------------------------

    def load_apk(self) -> None:
        apk_path = filedialog.askopenfilename(
            title="Select APK file",
            filetypes=[("APK files", "*.apk"), ("All files", "*.*")],
        )
        if apk_path:
            self.start_analysis(apk_path)

    def cancel_analysis(self) -> None:
        """
        What the header's Cancel button does. The analysis cannot be interrupted yet (AnalyzeApk has
        no cancellation), so for now it only says so; this is where stopping it would go.
        """
        self._set_status(
            "Cancelling an analysis is not supported yet: it will finish on its own.", StatusLevelEnum.INFO
        )

    def exit_app(self) -> None:
        self.files_panel.cleanup()  # drop temp files extracted for Open / Open with / Copy
        self.root.destroy()

    def maximize_window(self) -> None:
        try:
            self.root.state("zoomed")   # Windows & macOS
        except tk.TclError:
            try:
                self.root.attributes("-zoomed", True)   # Linux
            except tk.TclError:
                self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0") # Fallback

    def start_analysis(self, apk_path: str) -> None:
        if not os.path.exists(apk_path):
            messagebox.showerror("Error", f"File not found:\n{apk_path}")
            return
        self._result = None
        self.menu_bar.set_enabled(self._ANALYSIS_DEPENDENT_ITEMS, False)
        self._set_status(
            f"Analyzing: {os.path.basename(apk_path)}... (Please wait)", StatusLevelEnum.INFO
        )
        self._set_loading(True)
        self.header.reset_to_placeholder(os.path.basename(apk_path))
        self.info_panel.clear()
        self.security_panel.clear()
        self.permissions_panel.clear()
        self.components_panel.clear()
        self.intents_panel.clear()
        self.manifest_panel.clear()
        self.files_panel.clear()
        threading.Thread(target=self._analyze_in_background, args=(apk_path,), daemon=True).start()

    def _default_extract_folder_name(self) -> str:
        return self._result.default_name if self._result else "app"

    # --- Background worker (runs off the Tk main thread) ----------------------

    def _analyze_in_background(self, apk_path: str) -> None:
        try:
            result = self._analyze_apk.execute(apk_path)
        except Exception as exc:  # pylint: disable=broad-except
            # `exc` is unbound once the except block ends, so keep its text.
            self._report_failure(str(exc))
        else:
            self.root.after(0, lambda: self._render_result(result))
            count = len(result.inspection.warnings)
            if count:
                self._set_status(
                    f"Analysis completed with {count} warning(s): some data could not be read "
                    "(see the notice at the top of the tabs).",
                    StatusLevelEnum.INFO,
                )
            else:
                self._set_status("Analysis completed successfully.", StatusLevelEnum.SUCCESS)
        finally:
            self.root.after(0, lambda: self._set_loading(False))

    def _report_failure(self, message: str) -> None:
        self.root.after(
            0,
            lambda: messagebox.showerror(
                "Error",
                f"An error occurred while analyzing the APK:\n{message}"
            ),
        )
        self.root.after(0, self.header.show_error)
        self._set_status("Analysis failed.", StatusLevelEnum.ERROR)

    # --- UI updates (must run on the Tk main thread) ---------------------------

    def _set_status(self, message: str, level: StatusLevelEnum = StatusLevelEnum.NEUTRAL) -> None:
        self.root.after(0, lambda: self.status_bar.set_status(message, level))

    def _set_loading(self, loading: bool) -> None:
        self.header.set_loading(loading)
        self.menu_bar.set_enabled(("load_apk",), not loading)
        if loading:
            # Whatever was on screen is about to be cleared: show the Info tab and keep the user on it
            # until everything has been loaded and drawn.
            self._tab_lock.lock(keep=self.info_panel)
            self.loading_bar.start()
        else:
            self.loading_bar.stop()
            self._tab_lock.unlock()

    def _render_result(self, result: AnalysisResult) -> None:
        self._result = result
        inspection = result.inspection
        self.header.show_result(
            app_name=result.app_name,
            package_name=result.package_name,
            icon_png=result.icon_png,
        )
        self.info_panel.render(
            inspection.application,
            inspection.configuration,
            inspection.embedded_content,
            inspection.dex_metrics
        )
        self.security_panel.render(inspection.security, inspection.third_party)
        self.permissions_panel.render(inspection.permissions)
        self.components_panel.render(inspection.components)
        self.intents_panel.render(inspection.components.exported_intents())
        self.manifest_panel.render(result.manifest_xml)
        self.files_panel.render(result.apk_path, result.file_tree)
        self._show_warnings(result)
        self.menu_bar.set_enabled(self._ANALYSIS_DEPENDENT_ITEMS, True)

    def _show_warnings(self, result: AnalysisResult) -> None:
        components_warnings = result.warning_messages(*self._COMPONENTS_SECTIONS)
        self.info_panel.show_warnings(result.warning_messages(*self._INFO_SECTIONS))
        self.security_panel.show_warnings(result.warning_messages(*self._SECURITY_SECTIONS))
        self.permissions_panel.show_warnings(result.warning_messages(*self._PERMISSIONS_SECTIONS))
        self.components_panel.show_warnings(components_warnings)
        self.intents_panel.show_warnings(components_warnings)

    @staticmethod
    def _asset_icon(file_name: str) -> AssetIcon:
        return AssetIcon(f"{ApkAnalyzerApp._ICONS_DIR}/{file_name}")
