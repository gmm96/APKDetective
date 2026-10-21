"""
What the scanner needs to know about the Dalvik instruction set: how many 16-bit
code units each instruction takes, which ones are conditional jumps, and the
markers of the data blocks that sit among the instructions.
"""

# (first opcode, last opcode, length in code units). Whatever is not listed takes one unit.
_LENGTH_RANGES: tuple[tuple[int, int, int], ...] = (
    (0x02, 0x02, 2), (0x03, 0x03, 3),                  # move/from16, move/16
    (0x05, 0x05, 2), (0x06, 0x06, 3),                  # move-wide/from16, move-wide/16
    (0x08, 0x08, 2), (0x09, 0x09, 3),                  # move-object/from16, move-object/16
    (0x13, 0x13, 2), (0x14, 0x14, 3), (0x15, 0x16, 2),  # const/16, const, const/high16, const-wide/16
    (0x17, 0x17, 3), (0x18, 0x18, 5), (0x19, 0x1A, 2),  # const-wide/32, const-wide, const-wide/high16, const-string
    (0x1B, 0x1B, 3), (0x1C, 0x1C, 2),                  # const-string/jumbo, const-class
    (0x1F, 0x20, 2), (0x22, 0x23, 2),                  # check-cast, instance-of, new-instance, new-array
    (0x24, 0x26, 3),                                   # filled-new-array(/range), fill-array-data
    (0x29, 0x29, 2), (0x2A, 0x2C, 3),                  # goto/16, goto/32, packed-switch, sparse-switch
    (0x2D, 0x3D, 2),                                   # cmp*, if-test, if-testz
    (0x44, 0x6D, 2),                                   # aget*, aput*, iget*, iput*, sget*, sput*
    (0x6E, 0x72, 3), (0x74, 0x78, 3),                  # invoke-kind, invoke-kind/range
    (0x90, 0xAF, 2),                                   # binary operations
    (0xD0, 0xE2, 2),                                   # binary operations with a literal
    (0xFA, 0xFB, 4), (0xFC, 0xFD, 3), (0xFE, 0xFF, 2),  # invoke-polymorphic, invoke-custom, const-method-*
)


def _build_lengths() -> tuple[int, ...]:
    lengths = [1] * 256
    for first, last, length in _LENGTH_RANGES:
        for opcode in range(first, last + 1):
            lengths[opcode] = length
    return tuple(lengths)


class DalvikOpcodes:
    LENGTHS: tuple[int, ...] = _build_lengths()  # indexed by opcode

    FIRST_IF: int = 0x32  # if-eq ... if-lez are the conditional jumps
    LAST_IF: int = 0x3D

    # The first code unit of the data blocks; their opcode byte is 0 (a nop), their high byte tells which.
    PACKED_SWITCH_PAYLOAD: int = 0x0100
    SPARSE_SWITCH_PAYLOAD: int = 0x0200
    FILL_ARRAY_PAYLOAD: int = 0x0300
