"""
The header of a DEX file: where its tables are and how many entries each one has.
"""

import struct
from dataclasses import dataclass


@dataclass(frozen=True)
class DexHeader:
    string_ids_size: int
    string_ids_off: int
    type_ids_size: int
    type_ids_off: int
    proto_ids_size: int
    proto_ids_off: int
    field_ids_size: int
    field_ids_off: int
    method_ids_size: int
    method_ids_off: int
    class_defs_size: int
    class_defs_off: int

    SIZE = 0x70            # the size of the whole header
    _TABLES_OFFSET = 56    # where the (size, offset) pairs of the tables start inside it

    @classmethod
    def parse(cls, data: bytes) -> "DexHeader | None":
        """The header of `data`, or None when it is not a DEX file."""
        if len(data) < cls.SIZE or not data.startswith(b"dex\n"):
            return None
        return cls(*struct.unpack_from("<12I", data, cls._TABLES_OFFSET))

    def fits_in(self, file_size: int) -> bool:
        """Whether every table the header declares lies inside a file of that size."""
        tables = (  # (offset, entry count, bytes per entry)
            (self.string_ids_off, self.string_ids_size, 4),
            (self.type_ids_off, self.type_ids_size, 4),
            (self.proto_ids_off, self.proto_ids_size, 12),
            (self.field_ids_off, self.field_ids_size, 8),
            (self.method_ids_off, self.method_ids_size, 8),
            (self.class_defs_off, self.class_defs_size, 32),
        )
        return all(offset + count * entry_size <= file_size for offset, count, entry_size in tables)
