"""
What the scan of one DEX file finds. It has everything needed to add that file to the metrics of the APK, so the
files can be scanned in any order, in any process, and combined afterwards.
"""

from dataclasses import dataclass

from apkdetective.infrastructure.androguard.dex.dex_code_scanner import DexCodeStats


@dataclass(frozen=True)
class DexFileScan:
    number: int  # the position of the file among the DEX files of the APK, from 1
    classes: int = 0
    method_references: int = 0
    strings: int = 0
    stats: DexCodeStats | None = None  # None when the code of the file could not be scanned
    most_complex_method: str | None = None
    longest_method: str | None = None
    problems: tuple[str, ...] = ()  # what to warn about, already written
