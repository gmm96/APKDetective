"""
What scanning the code of one DEX file counted. It is filled in while the scan runs.
"""

from dataclasses import dataclass


@dataclass
class DexCodeStats:
    methods: int = 0                 # defined in the DEX (not merely referenced)
    methods_with_code: int = 0       # the rest are abstract or native
    native_methods: int = 0
    fields: int = 0
    instructions: int = 0            # without the data blocks that sit among them
    code_units: int = 0              # 16-bit units of code, data blocks included
    complexity: int = 0              # the sum of the cyclomatic complexity of every method
    max_complexity: int = 0
    most_complex_method: int = -1    # its index in the method table
    max_instructions: int = 0
    longest_method: int = -1
    damaged_classes: int = 0         # classes whose data could not be read to the end
    catch_bytes: int = 0             # bytes of catch handlers read; limits the work on damaged files
