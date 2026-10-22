"""
Reads the strings of a DEX file: MUTF-8 text, each preceded by its length as a ULEB128.
"""

import struct


class DexStrings:
    @staticmethod
    def read_all(data: bytes, count: int, table_offset: int) -> list[str]:
        """Every string of the table, in index order."""
        strings: list[str] = []
        find = data.find
        for offset in struct.unpack_from(f"<{count}I", data, table_offset):
            pos = offset
            while data[pos] & 0x80:  # skip the ULEB128 length prefix
                pos += 1
            pos += 1
            end = find(b"\0", pos)
            raw = data[pos:end if end >= 0 else len(data)]
            if b"\xc0" in raw:  # MUTF-8 stores an embedded NUL as C0 80
                raw = raw.replace(b"\xc0\x80", b"\0")
            strings.append(raw.decode("utf-8", "replace"))
        return strings

    @classmethod
    def read_one(cls, data: bytes, table_offset: int, index: int) -> str:
        """The string at `index`, without reading the others."""
        (offset,) = struct.unpack_from("<I", data, table_offset + 4 * index)
        return cls._decode_at(data, offset)

    @staticmethod
    def _decode_at(data: bytes, offset: int) -> str:
        pos = offset
        while data[pos] & 0x80:
            pos += 1
        pos += 1
        end = data.find(b"\0", pos)
        raw = data[pos:end if end >= 0 else len(data)]
        return raw.replace(b"\xc0\x80", b"\0").decode("utf-8", "replace")
