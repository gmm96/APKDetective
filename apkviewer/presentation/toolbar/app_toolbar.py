"""
Generic, data-driven top menu bar. It knows nothing about what the items
do: the caller describes the menus declaratively (AppToolbarItem,
AppToolbarChoiceGroup, or None for a separator) and can enable/disable
items by key. Adding a menu or an entry therefore never requires touching
this class.

It is the window's own menu bar (a ttkbootstrap Menu attached to the root),
so opening the drop-downs, moving between them with the mouse or the
keyboard and dismissing them are handled by Tk. A choice group is a
submenu of mutually exclusive radio entries.

Items, choices and groups can show a PNG asset or a Bootstrap icon
indistinctly (see MenuIconRenderer). Every entry reserves the same space on
the left, whether it has an icon or not, so the labels of all the menus line
up. In a choice group that space starts with a column for the check mark of
the selected entry.

ttkbootstrap restyles every Menu when the theme changes; `apply_palette`
only covers what it leaves out (the text of disabled entries) and redraws
the icons. Note that on Windows and macOS the bar itself is drawn by the
operating system, which ignores the application colors.
"""

import tkinter as tk
from collections.abc import Callable, Iterable, Mapping, Sequence
from functools import partial

import ttkbootstrap as ttkb
from PIL import Image, ImageTk

from apkviewer.presentation.appearance.theme_palette import ThemePalette
from apkviewer.presentation.common.app_focus_watcher import AppFocusWatcher
from apkviewer.presentation.icons.icon_loader import IconLoader
from apkviewer.presentation.icons.menu_icon_renderer import MenuIconRenderer
from apkviewer.presentation.viewmodels.app_toolbar_choice_group import AppToolbarChoiceGroup
from apkviewer.presentation.viewmodels.app_toolbar_item import AppToolbarItem
from apkviewer.presentation.viewmodels.asset_icon import AssetIcon
from apkviewer.presentation.viewmodels.bootstrap_icon import BootstrapIcon


class AppToolbar:
    _ICON_SIZE: tuple[int, int] = (16, 16)
    _ICON_PADDING: int = 8
    _ICON_SLOT_WIDTH: int = _ICON_SIZE[0] + 2 * _ICON_PADDING
    _CHECK_SLOT_WIDTH: int = _ICON_SIZE[0] + _ICON_PADDING  # the check mark, padded on its left only
    _CHECK_ICON: str = "check-lg"
    _LABEL_WIDTH: int = 30  # labels are padded to this width so the menus are not too narrow

    def __init__(
        self,
        root: ttkb.App,
        menus: Mapping[str, Sequence[AppToolbarItem | AppToolbarChoiceGroup | None]],
        palette: ThemePalette,
        icon_loader: IconLoader | None = None,
    ) -> None:
        self._root: ttkb.App = root
        self._palette: ThemePalette = palette
        self._icon_renderer: MenuIconRenderer = MenuIconRenderer(root, icon_loader)
        self._icons: list[ImageTk.PhotoImage | tk.PhotoImage] = []  # Tk drops an image as soon as its Python object is collected
        self._blank_icon: ImageTk.PhotoImage = self._create_blank_icon()
        self._positions: dict[str, tuple[tk.Menu, int]] = {}
        # (menu, index, builder of the image options of that entry): the images depend on the palette.
        self._entry_images: list[tuple[tk.Menu, int, Callable[[], dict]]] = []
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
        AppFocusWatcher(root, self._close_open_menus, widget_classes=("Menu",))

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
        for menu, index, build_options in self._entry_images:
            menu.entryconfigure(index, **build_options())

    # --- Styling -------------------------------------------------------------

    def _create_menu(self, parent: tk.Misc) -> ttkb.Menu:
        menu = ttkb.Menu(parent, tearoff=False)
        self._all_menus.append(menu)
        return menu

    def _style_menus(self) -> None:
        for menu in self._all_menus:
            menu.configure(disabledforeground=self._palette.disabled_text)

    # --- Dismissal -----------------------------------------------------------

    def _close_open_menus(self) -> None:
        """
        Closes the drop-down of the bar that is open (with its submenus), if any. On Windows and
        macOS the OS does it when the application is left; Tk's own bar (X11) would keep it on screen.
        """
        tcl = self._root.tk.call
        if not tcl("info", "exists", "::tk::Priv(menuBar)"):
            return
        active_bar = str(tcl("set", "::tk::Priv(menuBar)"))
        if not active_bar:
            return

        # Tk shows clones of the bar and of its drop-downs, so they are looked up by their path.
        open_dropdowns = [
            str(child) for child in tcl("winfo", "children", active_bar)
            if tcl("winfo", "class", child) == "Menu" and int(tcl("winfo", "ismapped", child))
        ]
        # What Escape does: unposts the menu hierarchy and gives the grab and the focus back.
        tcl("tk::MenuEscape", open_dropdowns[0] if open_dropdowns else active_bar)

    # --- Construction --------------------------------------------------------

    def _populate(self, menu: tk.Menu, entries: Sequence[AppToolbarItem | AppToolbarChoiceGroup | None]) -> None:
        for entry in entries:
            if entry is None:
                menu.add_separator()
            elif isinstance(entry, AppToolbarChoiceGroup):
                self._add_choice_group(menu, entry)
            else:
                self._add_item(menu, entry)

    def _add_item(self, menu: tk.Menu, item: AppToolbarItem) -> None:
        options: dict = {
            "label": self._padded(item.label),
            "command": partial(self._invoke, item.key),
            "image": self._icon_option(item.icon),
            "compound": tk.LEFT,
        }
        if item.accelerator:
            options["accelerator"] = item.accelerator
        menu.add_command(**options)

        index = self._last_index(menu)
        self._positions[item.key] = (menu, index)
        self._commands[item.key] = item.command
        self._enabled[item.key] = True
        if item.icon:
            self._entry_images.append((menu, index, partial(self._item_image_options, item.icon)))
        if item.shortcut:
            self._root.bind(item.shortcut, partial(self._on_shortcut, item.key))

    def _add_choice_group(self, menu: tk.Menu, group: AppToolbarChoiceGroup) -> None:
        """A submenu of radio entries (exactly one selected), opened from an entry titled like the group."""
        submenu = self._create_menu(menu)

        variable = tk.StringVar(master=submenu, value=group.selected_key)
        self._choice_vars[group.key] = variable
        for choice in group.choices:
            # The native indicator is turned off: the check mark is part of the entry's image.
            submenu.add_radiobutton(
                label=self._padded(choice.label),
                variable=variable,
                value=choice.key,
                command=choice.command,
                compound=tk.LEFT,
                indicatoron=False,
                **self._choice_image_options(choice.icon),
            )
            self._entry_images.append(
                (submenu, self._last_index(submenu), partial(self._choice_image_options, choice.icon))
            )

        menu.add_cascade(
            label=self._padded(group.title),
            menu=submenu,
            image=self._icon_option(group.icon),
            compound=tk.LEFT,
        )
        if group.icon:
            self._entry_images.append((menu, self._last_index(menu), partial(self._item_image_options, group.icon)))

    def _padded(self, label: str) -> str:
        return f"{label:<{self._LABEL_WIDTH}}"

    @staticmethod
    def _last_index(menu: tk.Menu) -> int:
        index = menu.index(tk.END)
        return index if index is not None else 0

    # --- Images --------------------------------------------------------------

    def _item_image_options(self, icon: AssetIcon | BootstrapIcon) -> dict:
        return {"image": self._render_icon(icon)}

    def _choice_image_options(self, icon: AssetIcon | BootstrapIcon | None) -> dict:
        """
        Image of a radio entry: [check column][icon column], with the check mark only while it is
        selected (`selectimage`). The selected entry keeps the menu background (`selectcolor`).
        """
        image = self._render_icon(icon) if icon else None
        return {
            "image": self._compose_choice_image(image, selected=False),
            "selectimage": self._compose_choice_image(image, selected=True),
            "selectcolor": self._palette.background,
        }

    def _compose_choice_image(
            self,
            icon: ImageTk.PhotoImage | tk.PhotoImage | None,
            selected: bool
        ) -> tk.PhotoImage:
        image = tk.PhotoImage(
            master=self._root,
            width=self._CHECK_SLOT_WIDTH + self._ICON_SLOT_WIDTH,
            height=self._ICON_SIZE[1],
        )
        if selected:
            check = ttkb.Icon(self._CHECK_ICON, self._ICON_SIZE[0], self._palette.foreground)
            image.tk.call(image.name, "copy", check, "-to", self._ICON_PADDING, 0)
        if icon is not None:
            image.tk.call(image.name, "copy", str(icon), "-to", self._CHECK_SLOT_WIDTH, 0)
        self._icons.append(image)
        return image

    def _icon_option(self, icon: AssetIcon | BootstrapIcon | None) -> ImageTk.PhotoImage | tk.PhotoImage:
        return self._render_icon(icon) if icon else self._blank_icon

    def _render_icon(self, icon: AssetIcon | BootstrapIcon) -> ImageTk.PhotoImage | tk.PhotoImage:
        image = self._icon_renderer.render(
            icon,
            size=self._ICON_SIZE,
            color=self._palette.foreground,
            padding_left=self._ICON_PADDING,
            padding_right=self._ICON_PADDING,
        )
        self._icons.append(image)
        return image

    def _create_blank_icon(self) -> ImageTk.PhotoImage:
        return ImageTk.PhotoImage(Image.new("RGBA", (self._ICON_SLOT_WIDTH, self._ICON_SIZE[1]), (0, 0, 0, 0)))

    def _on_shortcut(self, key: str, _event: tk.Event) -> None:
        self._invoke(key)

    def _invoke(self, key: str) -> None:
        # Keyboard shortcuts bypass the menu's own disabled state, so check it here.
        if self._enabled.get(key, False):
            self._commands[key]()
