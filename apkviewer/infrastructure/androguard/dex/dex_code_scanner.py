"""
Walks the classes and methods of a DEX file and counts what its code contains.

The cyclomatic complexity of a method is read from its bytecode as 1 plus its
decision points: every conditional jump, every case of a switch and every
catch clause. It is a measure of the compiled code, not of the source.

The DEX files of malware are often malformed on purpose, so the work is limited by
what a valid file always satisfies: the members of all the classes cannot outnumber the
identifiers in the header, and the code and the catch handlers cannot add up to more
than the file holds (the code, a few times over, in case methods share a code block).
A file that breaks a limit is read as far as it respects it, never longer.
"""

import struct

from apkviewer.domain.entities.analysis.cancellation_token import CancellationToken
from apkviewer.infrastructure.androguard.dex.dalvik_opcodes import DalvikOpcodes
from apkviewer.infrastructure.androguard.dex.dex_code_stats import DexCodeStats
from apkviewer.infrastructure.androguard.dex.dex_header import DexHeader

_ACC_NATIVE: int = 0x100
_CLASS_DEF_WORDS: int = 8   # a class_def_item is 8 uint32; the 7th is the offset of its class data
_CLASS_DATA_WORD: int = 6
_CODE_HEADER: struct.Struct = struct.Struct("<HHHHII")  # registers, ins, outs, tries, debug info, size
_CODE_HEADER_SIZE: int = 16
_SHARED_CODE_FACTOR: int = 4  # how many times the code may exceed the file, if methods share code blocks
_CANCEL_CHECK_MASK: int = 0x3F  # the token is checked once every 64 classes: a class takes ~0.1 ms, and the check is free


def _uleb(data: bytes, pos: int) -> tuple[int, int]:
    """(value, next position) of the unsigned LEB128 at `pos`."""
    result = 0
    shift = 0
    while True:
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        if byte < 0x80:
            return result, pos
        shift += 7


def _sleb(data: bytes, pos: int) -> tuple[int, int]:
    """(value, next position) of the signed LEB128 at `pos`."""
    result = 0
    shift = 0
    while True:
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            if byte & 0x40:
                result -= 1 << shift
            return result, pos


class DexCodeScanner:
    def scan(self, data: bytes, header: DexHeader, cancellation: CancellationToken | None = None) -> DexCodeStats:
        """
        Count the code of `data`. Raises struct.error when its class table is unreadable; a
        class with damaged data is skipped and counted in `damaged_classes`. Raises
        AnalysisCancelledError, when a `cancellation` is given and cancelled, in the middle of the file.
        """
        stats = DexCodeStats()
        words = struct.unpack_from(f"<{header.class_defs_size * _CLASS_DEF_WORDS}I", data, header.class_defs_off)
        for index, class_data_off in enumerate(words[_CLASS_DATA_WORD::_CLASS_DEF_WORDS]):
            if cancellation is not None and not index & _CANCEL_CHECK_MASK:
                cancellation.raise_if_cancelled()
            if class_data_off == 0:
                continue  # an interface of constants, a marker class...
            try:
                self._scan_class(data, header, class_data_off, stats)
            except (struct.error, IndexError, ValueError):
                stats.damaged_classes += 1
        return stats

    def _scan_class(self, data: bytes, header: DexHeader, pos: int, stats: DexCodeStats) -> None:
        static_fields, pos = _uleb(data, pos)
        instance_fields, pos = _uleb(data, pos)
        direct_methods, pos = _uleb(data, pos)
        virtual_methods, pos = _uleb(data, pos)
        fields = static_fields + instance_fields
        methods = direct_methods + virtual_methods
        if stats.fields + fields > header.field_ids_size or stats.methods + methods > header.method_ids_size:
            raise ValueError("the class declares more members than the DEX has identifiers for")
        stats.fields += fields
        stats.methods += methods
        for _ in range(fields * 2):  # (index difference, access flags) of each field
            _, pos = _uleb(data, pos)
        for method_count in (direct_methods, virtual_methods):
            method_index = 0  # the first index of each list is absolute, the rest are differences
            for _ in range(method_count):
                index_difference, pos = _uleb(data, pos)
                access_flags, pos = _uleb(data, pos)
                code_offset, pos = _uleb(data, pos)
                method_index += index_difference
                if access_flags & _ACC_NATIVE:
                    stats.native_methods += 1
                if code_offset:
                    self._scan_code(data, header, code_offset, method_index, stats)

    def _scan_code(
        self, data: bytes, header: DexHeader, code_offset: int, method_index: int, stats: DexCodeStats
    ) -> None:
        _, _, _, tries, _, size = _CODE_HEADER.unpack_from(data, code_offset)
        if stats.code_units + size > _SHARED_CODE_FACTOR * len(data) // 2:
            raise ValueError("the code adds up to more than the file can hold")
        units = struct.unpack_from(f"<{size}H", data, code_offset + _CODE_HEADER_SIZE)
        instructions, decisions = self._decode(units)
        if tries:
            decisions += self._catch_clauses(
                data, header, code_offset + _CODE_HEADER_SIZE + 2 * size, size, tries, stats
            )
        complexity = 1 + decisions

        stats.methods_with_code += 1
        stats.instructions += instructions
        stats.code_units += size
        stats.complexity += complexity
        if complexity > stats.max_complexity:
            stats.max_complexity = complexity
            stats.most_complex_method = method_index
        if instructions > stats.max_instructions:
            stats.max_instructions = instructions
            stats.longest_method = method_index

    @staticmethod
    def _decode(units: tuple[int, ...]) -> tuple[int, int]:
        """(number of instructions, number of decision points) of a method's code units."""
        lengths = DalvikOpcodes.LENGTHS
        first_if, last_if = DalvikOpcodes.FIRST_IF, DalvikOpcodes.LAST_IF
        packed, sparse, fill = (
            DalvikOpcodes.PACKED_SWITCH_PAYLOAD,
            DalvikOpcodes.SPARSE_SWITCH_PAYLOAD,
            DalvikOpcodes.FILL_ARRAY_PAYLOAD,
        )
        instructions = decisions = 0
        position = 0
        end = len(units)
        while position < end:
            unit = units[position]
            opcode = unit & 0xFF
            if opcode == 0 and unit:  # a data block: not an instruction
                if unit == packed:
                    cases = units[position + 1]
                    decisions += cases
                    position += cases * 2 + 4
                elif unit == sparse:
                    cases = units[position + 1]
                    decisions += cases
                    position += cases * 4 + 2
                elif unit == fill:
                    width = units[position + 1]
                    count = units[position + 2] | (units[position + 3] << 16)
                    position += (count * width + 1) // 2 + 4
                else:
                    position += 1
                continue
            instructions += 1
            if first_if <= opcode <= last_if:
                decisions += 1
            position += lengths[opcode]
        return instructions, decisions

    @staticmethod
    def _catch_clauses(
        data: bytes, header: DexHeader, code_end: int, size: int, tries: int, stats: DexCodeStats
    ) -> int:
        """The number of catch clauses (typed ones and catch-all) of a method with `tries` try blocks."""
        allowed = len(data) - stats.catch_bytes   # what the file still has room for
        if allowed <= 0:
            raise ValueError("the catch handlers add up to more than the file can hold")
        pos = code_end + (2 if size % 2 else 0)  # two bytes of padding keep the try items aligned
        pos += tries * 8                          # skip the try items: the handlers follow them
        start = pos
        handler_count, pos = _uleb(data, pos)
        if handler_count > tries:                 # every handler serves at least one try block
            raise ValueError("more catch handlers than try blocks")
        clauses = 0
        for _ in range(handler_count):
            handler_size, pos = _sleb(data, pos)  # negative: the typed catches are followed by a catch-all
            typed = abs(handler_size)
            if typed > header.type_ids_size or pos - start > allowed:
                raise ValueError("catch handlers that no valid file can hold")
            for _ in range(typed * 2):            # a (type, address) pair for each typed catch
                _, pos = _uleb(data, pos)
            clauses += typed
            if handler_size <= 0:
                _, pos = _uleb(data, pos)         # the catch-all address
                clauses += 1
        stats.catch_bytes += pos - start
        return clauses
