"""
What the DEX files of an APK contain, counted from the compiled code.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DexMetrics:
    dex_files: int = 0
    dex_size: int = 0                    # bytes
    packages: int = 0
    classes: int = 0                     # defined in the DEX files
    methods: int = 0                     # defined, not merely referenced
    methods_with_code: int = 0           # the rest are abstract or native
    native_methods: int = 0
    method_references: int = 0           # defined and called: the number the 64K limit of a DEX is about
    fields: int = 0
    strings: int = 0
    string_characters: int = 0
    instructions: int = 0                # the lines of a smali listing, more or less
    code_size: int = 0                   # bytes of bytecode, data blocks included
    cyclomatic_complexity: int = 0       # the sum over every method; see DexCodeScanner
    max_complexity: int = 0
    most_complex_method: str | None = None
    max_instructions: int = 0
    longest_method: str | None = None

    @property
    def average_complexity(self) -> float:
        """Per method that has code."""
        return self.cyclomatic_complexity / self.methods_with_code if self.methods_with_code else 0.0
