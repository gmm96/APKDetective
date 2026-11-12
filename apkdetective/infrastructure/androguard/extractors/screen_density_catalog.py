"""
What is known about Android screen densities: the standard ones, with their names and what they mean, and how to
describe any other value an APK may carry.

A density in the resource table is the `dpi` number of the configuration (0 when it has none), plus two special
values: 0xFFFE for "anydpi" (resources that scale to any density) and 0xFFFF for "nodpi" (never scaled). Any other
number is valid in a qualifier (`drawable-420dpi`).
"""

import re

from apkdetective.domain.entities.analysis.sections.screen_density import ScreenDensity


class ScreenDensityCatalog:
    ANY_DENSITY: int = 0xFFFE
    NO_DENSITY: int = 0xFFFF

    # density -> (qualifier, what it means)
    _STANDARD: dict[int, tuple[str, str]] = {
        120: ("ldpi", "Low density (0.75x). Primarily for legacy screens. Practically obsolete."),
        160: ("mdpi", "Medium density (1x). The baseline reference scale for Android."),
        213: ("tvdpi", "TV density (~1.33x). Used by some television screens. Rarely found in apps."),
        240: ("hdpi", "High density (1.5x)."),
        320: ("xhdpi", "Extra-high density (2x)."),
        480: ("xxhdpi", "Extra-extra-high density (3x). Standard resolution for modern smartphones."),
        640: ("xxxhdpi", "Extra-extra-extra-high density (4x). Mainly used for high-definition launcher icons."),
    }
    _SPECIAL: dict[int, tuple[str, str]] = {
        ANY_DENSITY: (
            "anydpi",
            "Vector graphics (XML). Automatically scales to any resolution without loss of quality.",
        ),
        NO_DENSITY: (
            "nodpi",
            "Static bitmaps. The Android system will not scale these resources under any circumstances.",
        ),
    }
    _CUSTOM_DESCRIPTION: str = (
        "Custom/Non-standard density. Specific density injected during Android App Bundle compilation "
        "for a particular device model."
    )

    # A density qualifier in a resource path: `res/drawable-xxhdpi-v4/icon.png`, `res/mipmap-420dpi/icon.png`.
    _FOLDER_PATTERN: re.Pattern = re.compile(r"-(ldpi|mdpi|hdpi|xhdpi|xxhdpi|xxxhdpi|tvdpi|anydpi|nodpi|\d+dpi)(?=[-/])")
    _QUALIFIER_DENSITIES: dict[str, int] = {
        **{qualifier: density for density, (qualifier, _) in _STANDARD.items()},
        **{qualifier: density for density, (qualifier, _) in _SPECIAL.items()},
    }

    @classmethod
    def describe(cls, density: int) -> ScreenDensity:
        """The name and the meaning of a density; any value that is not a standard one is a custom density."""
        if density in cls._STANDARD:
            qualifier, description = cls._STANDARD[density]
            return ScreenDensity(f"{qualifier} ({density}dpi)", description)
        if density in cls._SPECIAL:
            qualifier, description = cls._SPECIAL[density]
            return ScreenDensity(qualifier, description)
        return ScreenDensity(f"{density}dpi", cls._CUSTOM_DESCRIPTION)

    @classmethod
    def density_in_path(cls, path: str) -> int | None:
        """The density a resource path is qualified with, if any."""
        match = cls._FOLDER_PATTERN.search(path)
        if match is None:
            return None
        qualifier = match.group(1)
        return cls._QUALIFIER_DENSITIES.get(qualifier) or int(qualifier.removesuffix("dpi"))
