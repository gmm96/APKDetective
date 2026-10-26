"""
Builds the application's palette from a ttkbootstrap theme.

ttkbootstrap's accents (info, success, warning...) are chosen as fills, and on many
themes they are too faint to read as text over the theme's own background. Instead of
keeping a static table per color scheme (which cannot know every background it will
land on), the colors used as text, icons or tinted bands are derived from the theme so
that they reach a minimum contrast on it, keeping its hue.
"""

from typing import Any

from apkdetective.presentation.appearance.contrast_adjuster import ContrastAdjuster
from apkdetective.presentation.viewmodels.appearance.theme_palette import ThemePalette
from apkdetective.presentation.config.theme import (
    DISABLED_TEXT_AMOUNT,
    FOLDER_ROW_TINT,
    MARKED_LINE_TINT,
    MIN_COMMENT_CONTRAST,
    MIN_ICON_CONTRAST,
    MIN_TEXT_CONTRAST,
    MUTED_TEXT_AMOUNT,
)
from apkdetective.presentation.viewmodels.appearance.color_pair import ColorPair
from apkdetective.presentation.viewmodels.appearance.theme_custom_colors import ThemeCustomColors


class ThemePaletteBuilder:
    def build(self, colors: Any, custom_colors: ThemeCustomColors) -> ThemePalette:
        """`colors`: the active ttkbootstrap theme's colors (`Style().colors`)."""
        # Text can land on the page background or on the input one (fields, tables).
        surfaces: tuple[str, str] = (colors.bg, colors.inputbg)

        def readable(color: str) -> str:
            return ContrastAdjuster.ensure_contrast(color, surfaces, MIN_TEXT_CONTRAST)

        def chip(fill: str) -> ColorPair:
            text: str = ContrastAdjuster.best_contrast(fill, (colors.bg, colors.fg))
            return ColorPair(ContrastAdjuster.ensure_contrast(fill, (text,), MIN_TEXT_CONTRAST), text)

        return ThemePalette(
            primary=colors.primary,
            secondary=colors.secondary,
            success=colors.success,
            info=colors.info,
            warning=colors.warning,
            danger=colors.danger,
            light=colors.light,
            dark=colors.dark,
            background=colors.bg,
            foreground=colors.fg,
            select_background=colors.selectbg,
            select_foreground=colors.selectfg,
            border=colors.border,
            input_background=colors.inputbg,
            input_foreground=colors.inputfg,
            active=colors.active,
            xml_tag=readable(custom_colors.xml_tag),
            xml_attr=readable(custom_colors.xml_attr),
            xml_value=readable(custom_colors.xml_value),
            xml_comment=ContrastAdjuster.ensure_contrast(
                custom_colors.xml_comment, surfaces, MIN_COMMENT_CONTRAST
            ),
            muted_text=readable(ContrastAdjuster.blend(colors.fg, colors.bg, MUTED_TEXT_AMOUNT)),
            info_text=readable(colors.info),
            primary_icon=ContrastAdjuster.ensure_contrast(colors.primary, surfaces, MIN_ICON_CONTRAST),
            success_text=readable(colors.success),
            danger_text=readable(colors.danger),
            disabled_text=ContrastAdjuster.blend(colors.fg, colors.bg, DISABLED_TEXT_AMOUNT),
            marked_line=self._tinted_band(colors.primary, colors, MARKED_LINE_TINT),
            folder_row=self._tinted_band(colors.primary, colors, FOLDER_ROW_TINT),
            chip_success=chip(colors.success),
            chip_danger=chip(colors.danger),
            chip_neutral=chip(colors.warning),
            chip_muted=chip(colors.dark),
        )

    @staticmethod
    def _tinted_band(tint: str, colors: Any, amount: float) -> ColorPair:
        """
        A band of the theme's `tint` over the input background (where the lists and tables are
        drawn), with the input text color nudged, if needed, so it stays readable on the band.
        """
        band: str = ContrastAdjuster.blend(tint, colors.inputbg, amount)
        text: str = ContrastAdjuster.ensure_contrast(colors.inputfg, (band,), MIN_TEXT_CONTRAST)
        return ColorPair(band, text)
