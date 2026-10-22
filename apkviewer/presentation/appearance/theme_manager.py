"""
Manages the application's ttkbootstrap theme and custom palette.

The operating system preference is resolved dynamically when set to AUTO.
Theme variants (light/dark) are automatically switched based on the active mode.
"""

from typing import Any
from collections.abc import Callable
import ttkbootstrap as ttkb

from apkviewer.application.appearance.resolve_color_scheme import ResolveColorScheme
from apkviewer.domain.entities.appearance.color_mode_enum import ColorModeEnum
from apkviewer.domain.entities.appearance.color_scheme_enum import ColorSchemeEnum
from apkviewer.presentation.viewmodels.appearance.theme_palette import ThemePalette
from apkviewer.presentation.appearance.theme_palette_builder import ThemePaletteBuilder
from apkviewer.presentation.viewmodels.appearance.theme_custom_colors import ThemeCustomColors
from apkviewer.presentation.config.theme import THEMES, CUSTOM_COLORS


class ThemeManager:
    """Coordinates ttkbootstrap themes and application-specific colors."""

    def __init__(
        self,
        root: ttkb.App,
        resolve_color_scheme: ResolveColorScheme,
        initial_mode: ColorModeEnum = ColorModeEnum.AUTO,
    ) -> None:
        self._root: ttkb.App = root
        self._system_color_scheme_detector: ResolveColorScheme = resolve_color_scheme
        self._color_mode: ColorModeEnum = initial_mode

        self._style: ttkb.Style = ttkb.Style()
        self._listeners: list[Callable[[ThemePalette], None]] = []
        self._palette_builder: ThemePaletteBuilder = ThemePaletteBuilder()
        self._palette: ThemePalette
        self._theme_name: str = ""
        self._base_theme: str = THEMES[0] if THEMES else "bootstrap"

        # Resolve initial setup
        self._color_scheme: ColorSchemeEnum
        self._update_theme_state()

    @property
    def color_mode(self) -> ColorModeEnum:
        """Return the selected color mode."""
        return self._color_mode

    @property
    def color_scheme(self) -> ColorSchemeEnum:
        """Return the selected color mode."""
        return self._color_scheme

    @property
    def palette(self) -> ThemePalette:
        """Return the palette associated with the active theme."""
        return self._palette

    @property
    def theme_name(self) -> str:
        """Return the currently active ttkbootstrap theme variant."""
        return self._theme_name

    @property
    def base_theme(self) -> str:
        """Return the active base theme name without light/dark suffixes."""
        return self._base_theme

    @property
    def style(self) -> ttkb.Style:
        """Expose ttkbootstrap's Style for application-specific styling."""
        return self._style

    def subscribe(self, listener: Callable[[ThemePalette], None]) -> None:
        """Register a listener for palette changes."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[[ThemePalette], None]) -> None:
        """Remove a previously registered listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def set_mode(self, color_mode: ColorModeEnum) -> None:
        """Apply a manually selected light/dark mode, or resolve AUTO."""
        self._color_mode = color_mode
        self._update_theme_state()

    def set_theme(self, base_theme_name: str) -> None:
        """Apply a base theme, selecting the correct variant based on the current mode."""
        if THEMES and base_theme_name not in THEMES:
            raise ValueError(f"Unsupported base theme: {base_theme_name!r}")
        self._base_theme = base_theme_name
        self._update_theme_state()

    def _update_theme_state(self) -> None:
        self._resolve_active_color_scheme()
        target_theme: str = self._get_theme_variant(self._base_theme, self._color_scheme)
        self._apply_theme(target_theme, self._color_scheme)

    def _resolve_active_color_scheme(self) -> None:
        """Determine the target ColorScheme based on the current ColorMode."""
        if self._color_mode == ColorModeEnum.AUTO:
            scheme: ColorSchemeEnum = self._system_color_scheme_detector.execute(self._color_mode)
            self._color_scheme = scheme if scheme in (ColorSchemeEnum.LIGHT, ColorSchemeEnum.DARK) else ColorSchemeEnum.LIGHT
        else:
            self._color_scheme = ColorSchemeEnum.DARK if self._color_mode == ColorModeEnum.DARK else ColorSchemeEnum.LIGHT

    def _get_theme_variant(self, base_theme: str, target_scheme: ColorSchemeEnum) -> str:
        """Construct the theme variant name based on the target scheme."""
        suffix: str = "-light" if target_scheme == ColorSchemeEnum.LIGHT else "-dark"
        variant: str = f"{base_theme}{suffix}"
        if variant in self._style.theme_names():
            return variant
        fallback_base: str = THEMES[0] if THEMES else "bootstrap"
        return f"{fallback_base}{suffix}"

    def _apply_theme(self, theme_name: str, color_scheme: ColorSchemeEnum) -> None:
        """Apply the theme and notify listeners of palette changes."""
        if theme_name not in self._style.theme_names():
            raise ValueError(f"ttkbootstrap theme {theme_name!r} is not available.")
        self._theme_name = theme_name
        self._style.theme_use(theme_name)
        self._palette = self._extract_theme_palette(color_scheme)
        self._root.option_add("*Toplevel.background", self._palette.background)
        self._notify_listeners()

    def _extract_theme_palette(self, color_scheme: ColorSchemeEnum) -> ThemePalette:
        """Create a ThemePalette combining ttkbootstrap colors and custom static colors."""
        custom_colors: ThemeCustomColors = CUSTOM_COLORS[color_scheme]
        try:
            colors: Any = self._style.colors
            return self._palette_builder.build(colors, custom_colors)
        except AttributeError as error:
            raise RuntimeError(
                f"Failed to extract palette colors for theme '{self._theme_name}'. "
                f"The theme might be corrupted or unsupported. Details: {error}"
            ) from error

    def _notify_listeners(self) -> None:
        """
        Broadcast the updated palette to all registered listeners. A listener that fails does
        not stop the rest from repainting: the first error is raised once all have run.
        """
        first_error: Exception | None = None
        for listener in tuple(self._listeners):
            try:
                listener(self._palette)
            except Exception as error:
                if first_error is None:
                    first_error = error
        if first_error is not None:
            raise first_error
