"""
Counts what the DEX files of an APK contain: classes, methods, fields, strings,
instructions and the cyclomatic complexity of the code.

The numbers that are in the header of each DEX file cost nothing; the ones that
need the code are counted by DexCodeScanner (about a second for 50 MB of DEX).
A DEX file that can't be read completely never stops the others from counting:
what is missing is reported as a warning.
"""

import struct
from collections.abc import Sequence

from apkviewer.domain.entities.analysis_section import AnalysisSection
from apkviewer.domain.entities.dex_metrics import DexMetrics
from apkviewer.infrastructure.androguard.analysis_warnings import AnalysisWarningCollector
from apkviewer.infrastructure.androguard.dex_code_scanner import DexCodeScanner
from apkviewer.infrastructure.androguard.dex_contents import DexContents
from apkviewer.infrastructure.androguard.dex_header import DexHeader
from apkviewer.infrastructure.androguard.dex_strings import DexStrings


class DexMetricsExtractor:
    def __init__(self, scanner: DexCodeScanner | None = None) -> None:
        self._scanner: DexCodeScanner = scanner or DexCodeScanner()

    def extract(
        self,
        dex_files: Sequence[bytes],
        contents: DexContents,
        warnings: AnalysisWarningCollector | None = None,
    ) -> DexMetrics:
        """`contents`: the strings and class names already read from the same files."""
        classes = method_references = strings = 0
        methods = methods_with_code = native_methods = fields = 0
        instructions = code_units = complexity = 0
        most_complex: tuple[int, str | None] = (0, None)  # (complexity, name of the method)
        longest: tuple[int, str | None] = (0, None)       # (instructions, name of the method)

        for number, data in enumerate(dex_files, start=1):
            header = DexHeader.parse(data)
            if header is None:
                self._warn(warnings, f"DEX file #{number} is not a valid DEX file: its metrics are missing.")
                continue
            if not header.fits_in(len(data)):
                self._warn(
                    warnings,
                    f"The header of DEX file #{number} declares tables that do not fit in the file: "
                    "its metrics are missing.",
                )
                continue
            classes += header.class_defs_size
            method_references += header.method_ids_size
            strings += header.string_ids_size
            try:
                stats = self._scanner.scan(data, header)
            except (struct.error, IndexError, ValueError):
                self._warn(
                    warnings,
                    f"The class table of DEX file #{number} could not be read: its code metrics are missing.",
                )
                continue
            if stats.damaged_classes:
                self._warn(
                    warnings,
                    f"{stats.damaged_classes} class(es) of DEX file #{number} could not be read to the end: "
                    "the DEX metrics may be incomplete.",
                )
            methods += stats.methods
            methods_with_code += stats.methods_with_code
            native_methods += stats.native_methods
            fields += stats.fields
            instructions += stats.instructions
            code_units += stats.code_units
            complexity += stats.complexity
            if stats.max_complexity > most_complex[0]:
                most_complex = (stats.max_complexity, self._method_name(data, header, stats.most_complex_method))
            if stats.max_instructions > longest[0]:
                longest = (stats.max_instructions, self._method_name(data, header, stats.longest_method))

        return DexMetrics(
            dex_files=len(dex_files),
            dex_size=sum(len(data) for data in dex_files),
            packages=len({name.rpartition("/")[0] for name in contents.class_names}),
            classes=classes,
            methods=methods,
            methods_with_code=methods_with_code,
            native_methods=native_methods,
            method_references=method_references,
            fields=fields,
            strings=strings,
            string_characters=sum(map(len, contents.strings)),
            instructions=instructions,
            code_size=code_units * 2,
            cyclomatic_complexity=complexity,
            max_complexity=most_complex[0],
            most_complex_method=most_complex[1],
            max_instructions=longest[0],
            longest_method=longest[1],
        )

    @staticmethod
    def _warn(warnings: AnalysisWarningCollector | None, message: str) -> None:
        if warnings is not None:
            warnings.add(message, AnalysisSection.DEX_METRICS)

    @staticmethod
    def _method_name(data: bytes, header: DexHeader, method_index: int) -> str:
        """'com.example.Main.run' for the method at that index of the method table."""
        try:
            class_index, _, name_index = struct.unpack_from("<HHI", data, header.method_ids_off + 8 * method_index)
            (descriptor_index,) = struct.unpack_from("<I", data, header.type_ids_off + 4 * class_index)
            descriptor = DexStrings.read_one(data, header.string_ids_off, descriptor_index)
            name = DexStrings.read_one(data, header.string_ids_off, name_index)
        except (struct.error, IndexError):
            return f"method #{method_index}"
        class_name = descriptor[1:-1] if descriptor.startswith("L") and descriptor.endswith(";") else descriptor
        return f"{class_name.replace('/', '.')}.{name}"
