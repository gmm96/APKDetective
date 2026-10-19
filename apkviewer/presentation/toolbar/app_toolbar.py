"""
Generic, data-driven top menu bar. It knows nothing about what the items
do: the caller describes the menus declaratively (AppToolbarItem,
AppToolbarChoiceGroup, or None for a separator) and can enable/disable
items by key. Adding a menu or an entry therefore never requires touching
this class.

It is the window's own menu bar (a ttkbootstrap Menu attached to the root),
so opening the drop-downs, moving between them with the mouse or the
keyboard and dismissing them are all handled by Tk. A choice group is a
submenu of mutually exclusive radio entries.

ttkbootstrap restyles every Menu when the theme changes; `apply_palette`
only covers what it leaves out (the text of disabled entries) and re-tints
the icons. Note that on Windows and macOS the bar itself is drawn by the
operating system, which ignores the application colors.
"""

import tkinter as tk
from collections.abc import Callable, Iterable, Mapping, Sequence
from functools import partial

import ttkbootstrap as ttkb
from PIL import Image, ImageTk

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.icons.icon_loader import IconLoader
from apkviewer.presentation.viewmodels.app_toolbar_choice_group import AppToolbarChoiceGroup
from apkviewer.presentation.viewmodels.app_toolbar_item import AppToolbarItem


# A None entry renders as a separator.
MenuEntry = AppToolbarItem | AppToolbarChoiceGroup | None


class AppToolbar:
    _ICON_SIZE: tuple[int, int] = (16, 16)
    _ICON_PADDING: int = 8
    _LABEL_WIDTH: int = 40  # labels are padded to this width so the menus are not too narrow

    def __init__(
        self,
        root: ttkb.App,
        menus: Mapping[str, Sequence[MenuEntry]],
        palette: ThemePalette,
        icon_loader: IconLoader | None = None,
    ) -> None:
        self._root: ttkb.App = root
        self._palette: ThemePalette = palette
        self._icon_loader: IconLoader = icon_loader or IconLoader()
        self._icons: list[ImageTk.PhotoImage] = []
        self._blank_icon: ImageTk.PhotoImage = self._create_blank_icon()
        self._positions: dict[str, tuple[tk.Menu, int]] = {}
        self._entry_icons: list[tuple[tk.Menu, int, str]] = []  # (menu, index, icon path)
        self._choice_vars: dict[str, tk.StringVar] = {}
        self._commands: dict[str, Callable[[], None]] = {}
        self._enabled: dict[str, bool] = {}
        self._all_menus: list[ttkb.Menu] = []  # the bar, every drop-down and every submenu

        self._menubar: ttkb.Menu = self._create_menu(root)
        for title, entries in menus.items():
            menu = self._create_menu(self._menubar)
            self._populate(menu, entries)
            self._menubar.add_cascade(label=title, menu=menu)
        root.configure(menu=self._menubar)
        self._style_menus()

    def set_enabled(self, keys: Iterable[str], enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        for key in keys:
            menu, index = self._positions[key]
            menu.entryconfigure(index, state=state)
            self._enabled[key] = enabled

    def apply_palette(self, palette: ThemePalette) -> None:
        self._palette = palette
        self._style_menus()
        self._icons.clear()
        for menu, index, icon_path in self._entry_icons:
            menu.entryconfigure(index, image=self._load_icon(icon_path))

    # --- Styling -------------------------------------------------------------

    def _create_menu(self, parent: tk.Misc) -> ttkb.Menu:
        menu = ttkb.Menu(parent, tearoff=False)
        self._all_menus.append(menu)
        return menu

    def _style_menus(self) -> None:
        for menu in self._all_menus:
            menu.configure(disabledforeground=self._palette.disabled_text)

    # --- Construction --------------------------------------------------------

    def _populate(self, menu: tk.Menu, entries: Sequence[MenuEntry]) -> None:
        # Entries without an icon get a transparent spacer so labels stay aligned.
        has_icons = self._uses_icons(entries)
        for entry in entries:
            if entry is None:
                menu.add_separator()
            elif isinstance(entry, AppToolbarChoiceGroup):
                self._add_choice_group(menu, entry, has_icons)
            else:
                self._add_item(menu, entry, has_icons)

    @staticmethod
    def _uses_icons(entries: Sequence[MenuEntry]) -> bool:
        # A group's icons live in its own submenu, so they do not affect the menu that holds it.
        return any(isinstance(entry, AppToolbarItem) and entry.icon_path for entry in entries)

    def _add_item(self, menu: tk.Menu, item: AppToolbarItem, use_icons: bool) -> None:
        options: dict = {
            "label": self._padded(item.label),
            "command": partial(self._invoke, item.key),
        }
        if item.accelerator:
            options["accelerator"] = item.accelerator
        if use_icons:
            options["image"] = self._icon_option(item.icon_path)
            options["compound"] = tk.LEFT
        menu.add_command(**options)

        index = self._last_index(menu)
        self._positions[item.key] = (menu, index)
        self._commands[item.key] = item.command
        self._enabled[item.key] = True
        if item.icon_path:
            self._entry_icons.append((menu, index, item.icon_path))
        if item.shortcut:
            self._root.bind(item.shortcut, partial(self._on_shortcut, item.key))

    def _add_choice_group(self, menu: tk.Menu, group: AppToolbarChoiceGroup, use_icons: bool) -> None:
        """A submenu of radio entries (exactly one selected), opened from an entry titled like the group."""
        submenu = self._create_menu(menu)
        group_uses_icons = any(choice.icon_path for choice in group.choices)

        variable = tk.StringVar(master=submenu, value=group.selected_key)
        self._choice_vars[group.key] = variable
        for choice in group.choices:
            options: dict = {
                "label": self._padded(choice.label),
                "variable": variable,
                "value": choice.key,
                "command": choice.command,
            }
            if group_uses_icons:
                options["image"] = self._icon_option(choice.icon_path)
                options["compound"] = tk.LEFT
            submenu.add_radiobutton(**options)
            if choice.icon_path:
                self._entry_icons.append((submenu, self._last_index(submenu), choice.icon_path))

        cascade_options: dict = {"label": self._padded(group.title), "menu": submenu}
        if use_icons:
            cascade_options["image"] = self._blank_icon
            cascade_options["compound"] = tk.LEFT
        menu.add_cascade(**cascade_options)

    def _padded(self, label: str) -> str:
        return f"{label:<{self._LABEL_WIDTH}}"

    @staticmethod
    def _last_index(menu: tk.Menu) -> int:
        index = menu.index(tk.END)
        return index if index is not None else 0

    def _icon_option(self, icon_path: str | None) -> ImageTk.PhotoImage:
        return self._load_icon(icon_path) if icon_path else self._blank_icon

    def _load_icon(self, icon_path: str) -> ImageTk.PhotoImage:
        icon = self._icon_loader.load_icon(
            icon_path,
            size=self._ICON_SIZE,
            hex_color=self._palette.foreground,
            padding_left=self._ICON_PADDING,
            padding_right=self._ICON_PADDING,
        )
        self._icons.append(icon)
        return icon

    def _create_blank_icon(self) -> ImageTk.PhotoImage:
        width = self._ICON_SIZE[0] + 2 * self._ICON_PADDING
        return ImageTk.PhotoImage(Image.new("RGBA", (width, self._ICON_SIZE[1]), (0, 0, 0, 0)))

    def _on_shortcut(self, key: str, _event: tk.Event) -> None:
        self._invoke(key)

    def _invoke(self, key: str) -> None:
        # Keyboard shortcuts bypass the menu's own disabled state, so check it here.
        if self._enabled.get(key, False):
            self._commands[key]()
