"""
Reads the strings and class names of every DEX file of an APK exactly once.
The extractors that need code-level data (embedded URLs, trackers) share
this result.

DEX files are read directly from their string / type / class tables
instead of through androguard's DEX object, which builds the whole
class/method model (about 20 s for a 7-DEX app) when only these two lists
are needed. It also keeps working with DEX versions the library can't parse.
"""

import struct
from collections.abc import Iterable

from apkviewer.domain.entities.analysis.analysis_section import AnalysisSection
from apkviewer.infrastructure.androguard.analysis_warnings import AnalysisWarningCollector
from apkviewer.infrastructure.androguard.dex_contents import DexContents
from apkviewer.infrastructure.androguard.dex_header import DexHeader
from apkviewer.infrastructure.androguard.dex_strings import DexStrings

_CLASS_DEF_WORDS: int = 8  # a class_def_item is 8 uint32 (32 bytes); the first is the class type


class DexReader:
    def read(self, dex_files: Iterable[bytes], warnings: AnalysisWarningCollector | None = None) -> DexContents:
        strings: list[str] = []
        class_names: list[str] = []
        for number, dex_bytes in enumerate(dex_files, start=1):
            dex_strings, dex_classes, problem = self._parse(dex_bytes)
            strings.extend(dex_strings)
            class_names.extend(dex_classes)
            if problem and warnings is not None:
                warnings.add(
                    f"DEX file #{number} {problem}: embedded URLs and trackers may be incomplete.",
                    AnalysisSection.EMBEDDED_CONTENT, AnalysisSection.THIRD_PARTY,
                )
        return DexContents(strings=tuple(strings), class_names=tuple(class_names))

    @staticmethod
    def _parse(data: bytes) -> tuple[list[str], list[str], str | None]:
        """(strings, class names, problem) of one DEX; whatever can't be read comes back empty."""
        header = DexHeader.parse(data)
        if header is None:
            return [], [], "is not a valid DEX file"
        try:
            strings = DexStrings.read_all(data, header.string_ids_size, header.string_ids_off)
        except (struct.error, IndexError):
            return [], [], "could not be read (corrupt string table)"

        try:
            type_to_string = struct.unpack_from(f"<{header.type_ids_size}I", data, header.type_ids_off)
            class_words = struct.unpack_from(
                f"<{header.class_defs_size * _CLASS_DEF_WORDS}I", data, header.class_defs_off
            )
            class_names = [strings[type_to_string[idx]] for idx in class_words[::_CLASS_DEF_WORDS]]
        except (struct.error, IndexError):
            return strings, [], "has unreadable class tables"
        return strings, class_names, None
