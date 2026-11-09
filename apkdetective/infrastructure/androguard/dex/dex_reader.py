"""
Reads the strings and class names of a DEX file.
The analysis of every file does it once, in the process that analyzes it.

DEX files are read directly from their string / type / class tables
instead of through androguard's DEX object, which builds the whole
class/method model (about 20 s for a 7-DEX app) when only these two lists
are needed. It also keeps working with DEX versions the library can't parse.
"""

import struct

from apkdetective.domain.entities.analysis.sections.dex_header import DexHeader
from apkdetective.infrastructure.androguard.dex.dex_strings import DexStrings



class DexReader:
    _CLASS_DEF_WORDS: int = 8  # a class_def_item is 8 uint32 (32 bytes); the first is the class type

    @staticmethod
    def read(data: bytes) -> tuple[list[str], list[str], str | None]:
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
                f"<{header.class_defs_size * DexReader._CLASS_DEF_WORDS}I", data, header.class_defs_off
            )
            class_names = [strings[type_to_string[idx]] for idx in class_words[::DexReader._CLASS_DEF_WORDS]]
        except (struct.error, IndexError):
            return strings, [], "has unreadable class tables"
        return strings, class_names, None
