"""
Removes from a resource table (resources.arsc) the translations nobody is going to read.

Androguard builds a Python object for every entry of the table, and in a big app almost all of them (86 % in the
YouTube APK, 96 % in Signal's) are the strings and plurals translated to each language: 270,000 entries that take
about half of the time of the analysis. They are used for one thing only: to know which languages the app has,
and that is told by the configuration of each chunk, not by its entries. The values that are read (the name of the
app, the labels of the manifest...) are the ones of the default configuration.

A chunk of translations is removed only when everything it holds is also in the chunk of the default configuration
(then the default value is the one that is read, with or without it). Chunks are removed whole, and the sizes of
the package and of the table are corrected: nothing else of the file is touched. If the file is not what is
expected, nothing is removed.
"""

import io
import struct

from androguard.core.axml import ARSCHeader, StringBlock

from apkdetective.domain.entities.analysis.trimmed_resource_table import TrimmedResourceTable
from apkdetective.domain.entities.analysis.resources_removed_config import ResourcesRemovedConfig



class ResourceTableTrimmer:
    _RES_STRING_POOL_TYPE = 0x0001
    _RES_TABLE_TYPE = 0x0002
    _RES_TABLE_PACKAGE_TYPE = 0x0200
    _RES_TABLE_TYPE_TYPE = 0x0201
    _NO_ENTRY = 0xFFFFFFFF

    _CHUNK_HEADER = struct.Struct("<HHI")  # type, header size, size
    _PACKAGE_TYPE_STRINGS_OFFSET = 268  # where, in the header of a package, the offset of its pool of type names is
    _TYPE_ID_OFFSET = 8
    _TYPE_FLAGS_OFFSET = 9
    _TYPE_ENTRY_COUNT_OFFSET = 12
    _TYPE_CONFIG_OFFSET = 20
    _CONFIG_LOCALE_OFFSET = 8  # language (2 bytes) and country (2 bytes) inside a configuration
    _NO_LANGUAGE = b"\x00\x00"

    # Types whose translated values are never read: only the default one is.
    TRIMMED_TYPES: frozenset[str] = frozenset({"string", "plurals", "array"})
    MIN_REMOVED_BYTES: int = 256 * 1024  # removing less than this is not worth the work

    def trim(self, data: bytes) -> TrimmedResourceTable | None:
        """The table without its translations, or None if there is nothing worth removing or it can't be followed."""
        try:
            return self._trim(data)
        except (struct.error, ValueError, IndexError):
            return None

    def _trim(self, data: bytes) -> TrimmedResourceTable | None:
        table_type, table_header_size, table_size = self._CHUNK_HEADER.unpack_from(data, 0)
        if table_type != self._RES_TABLE_TYPE or not table_header_size <= table_size <= len(data):
            return None
        packages = [chunk for chunk in self._chunks(data, table_header_size, table_size)
                    if chunk[1] == self._RES_TABLE_PACKAGE_TYPE]
        if not packages:
            return None

        holes: list[tuple[int, int]] = []  # byte ranges to remove, in order
        removed: list[ResourcesRemovedConfig] = []
        removed_in_package: list[int] = []
        for index, (start, _, header_size, size) in enumerate(packages):
            package_holes, package_removed = self._translations(data, index, start, header_size, size)
            holes.extend(package_holes)
            removed.extend(package_removed)
            removed_in_package.append(sum(end - begin for begin, end in package_holes))
        if sum(removed_in_package) < self.MIN_REMOVED_BYTES:
            return None

        trimmed = bytearray()
        cursor = 0
        for begin, end in holes:
            trimmed += data[cursor:begin]
            cursor = end
        trimmed += data[cursor:]

        # the sizes of the table and of every package, which now are smaller
        struct.pack_into("<I", trimmed, 4, table_size - sum(removed_in_package))
        removed_before = 0
        for (start, _, _, size), removed_here in zip(packages, removed_in_package):
            struct.pack_into("<I", trimmed, start - removed_before + 4, size - removed_here)
            removed_before += removed_here
        return TrimmedResourceTable(bytes(trimmed), tuple(removed))

    @staticmethod
    def _chunks(data: bytes, start: int, end: int) -> list[tuple[int, int, int, int]]:
        """(position, type, header size, size) of the chunks that follow one another from start to end."""
        chunks = []
        position = start
        while position < end:
            chunk_type, header_size, size = ResourceTableTrimmer._CHUNK_HEADER.unpack_from(data, position)
            if size < header_size or position + size > end:
                raise ValueError("a chunk does not fit")
            chunks.append((position, chunk_type, header_size, size))
            position += size
        return chunks

    def _translations(
        self, data: bytes, package_index: int, start: int, header_size: int, size: int
    ) -> tuple[list[tuple[int, int]], list[ResourcesRemovedConfig]]:
        type_names = self._type_names(data, start)
        trimmed_ids = {number + 1 for number, name in enumerate(type_names) if name in self.TRIMMED_TYPES}
        chunks = [chunk for chunk in self._chunks(data, start + header_size, start + size)
                  if chunk[1] == self._RES_TABLE_TYPE_TYPE and data[chunk[0] + self._TYPE_ID_OFFSET] in trimmed_ids]

        defaults: dict[int, set[int]] = {}  # per type: the entries that the default configuration has
        candidates = []
        for position, _, header, chunk_size in chunks:
            type_id = data[position + self._TYPE_ID_OFFSET]
            config = self._config(data, position)
            if data[position + self._TYPE_FLAGS_OFFSET] != 0:  # sparse or compact offsets: left as they are
                continue
            if not any(config[4:]):
                defaults.setdefault(type_id, set()).update(self._present_entries(data, position, header))
            elif config[self._CONFIG_LOCALE_OFFSET:self._CONFIG_LOCALE_OFFSET + 2] != self._NO_LANGUAGE:
                candidates.append((position, header, chunk_size, type_id, config))

        holes = []
        removed = []
        for position, header, chunk_size, type_id, config in candidates:
            if self._present_entries(data, position, header) <= defaults.get(type_id, set()):
                holes.append((position, position + chunk_size))
                removed.append(ResourcesRemovedConfig(package_index, type_names[type_id - 1], config))
        return holes, removed

    @staticmethod
    def _config(data: bytes, chunk_position: int) -> bytes:
        config_start = chunk_position + ResourceTableTrimmer._TYPE_CONFIG_OFFSET
        (config_size,) = struct.unpack_from("<I", data, config_start)
        if not 12 <= config_size <= 128:
            raise ValueError("unexpected size of configuration")
        return data[config_start:config_start + config_size]

    @staticmethod
    def _present_entries(data: bytes, chunk_position: int, header_size: int) -> set[int]:
        (count,) = struct.unpack_from("<I", data, chunk_position + ResourceTableTrimmer._TYPE_ENTRY_COUNT_OFFSET)
        offsets = struct.unpack_from(f"<{count}I", data, chunk_position + header_size)
        return {index for index, offset in enumerate(offsets) if offset != ResourceTableTrimmer._NO_ENTRY}

    @staticmethod
    def _type_names(data: bytes, package_start: int) -> list[str]:
        (offset,) = struct.unpack_from("<I", data, package_start + ResourceTableTrimmer._PACKAGE_TYPE_STRINGS_OFFSET)
        buffer = io.BufferedReader(io.BytesIO(data))  # type: ignore
        #buffer = io.BytesIO(data)
        buffer.seek(package_start + offset)
        header = ARSCHeader(buffer, ResourceTableTrimmer._RES_STRING_POOL_TYPE)
        pool = StringBlock(buffer, header)
        return [pool.getString(number) for number in range(len(pool))]
