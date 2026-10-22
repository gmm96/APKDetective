"""
Color math used to derive readable colors from a theme (WCAG contrast ratio).

Pure functions on "#rrggbb" strings, with no Tk involved, so they can be reasoned about and
tested on their own.
"""

import colorsys
from collections.abc import Iterable, Sequence


class ContrastAdjuster:
    @staticmethod
    def contrast_ratio(first: str, second: str) -> float:
        """WCAG contrast ratio, from 1 (identical) to 21 (black on white)."""
        lighter, darker = sorted(
            (ContrastAdjuster._luminance(first), ContrastAdjuster._luminance(second)),
            reverse=True,
        )
        return (lighter + 0.05) / (darker + 0.05)

    @staticmethod
    def blend(color: str, other: str, amount: float) -> str:
        """`amount` (0..1) of `color` laid over `other`."""
        mixed: list[int] = [
            round(a * amount + b * (1 - amount))
            for a, b in zip(ContrastAdjuster._channels(color), ContrastAdjuster._channels(other))
        ]
        return ContrastAdjuster._hex(mixed)

    @staticmethod
    def ensure_contrast(color: str, backgrounds: Sequence[str], min_ratio: float) -> str:
        """
        `color` itself when it already reaches `min_ratio` against every background; otherwise
        the closest color with the same hue and saturation that does. It moves away from the
        backgrounds (lighter if it is already lighter than them, darker if not), by the least
        amount needed.
        """
        if ContrastAdjuster._worst_ratio(color, backgrounds) >= min_ratio:
            return color

        hue, lightness, saturation = colorsys.rgb_to_hls(
            *(channel / 255 for channel in ContrastAdjuster._channels(color))
        )
        mean_luminance: float = sum(ContrastAdjuster._luminance(b) for b in backgrounds) / len(backgrounds)
        limit: float = 1.0 if ContrastAdjuster._luminance(color) >= mean_luminance else 0.0

        def candidate(step: float) -> str:
            level: float = lightness + (limit - lightness) * step
            return ContrastAdjuster._hex(
                [round(c * 255) for c in colorsys.hls_to_rgb(hue, level, saturation)]
            )

        low, high = 0.0, 1.0
        for _ in range(20):
            middle: float = (low + high) / 2
            if ContrastAdjuster._worst_ratio(candidate(middle), backgrounds) >= min_ratio:
                high = middle
            else:
                low = middle
        return candidate(high)

    @staticmethod
    def best_contrast(fill: str, candidates: Iterable[str]) -> str:
        """The candidate that reads best on `fill`."""
        return max(candidates, key=lambda candidate: ContrastAdjuster.contrast_ratio(candidate, fill))

    # --- Internals -------------------------------------------------------------------------------

    @staticmethod
    def _worst_ratio(color: str, backgrounds: Sequence[str]) -> float:
        return min(ContrastAdjuster.contrast_ratio(color, background) for background in backgrounds)

    @staticmethod
    def _luminance(color: str) -> float:
        def linear(channel: int) -> float:
            value: float = channel / 255
            return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

        red, green, blue = (linear(channel) for channel in ContrastAdjuster._channels(color))
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    @staticmethod
    def _channels(color: str) -> list[int]:
        digits: str = color.lstrip("#")
        return [int(digits[index:index + 2], 16) for index in (0, 2, 4)]

    @staticmethod
    def _hex(channels: Sequence[int]) -> str:
        return "#" + "".join(f"{max(0, min(255, channel)):02x}" for channel in channels)
