"""
Everything the analysis takes from one DEX file. The files do not depend on each other, so each one can be analyzed
in any process, in any order, and the results added up afterwards.
"""

from dataclasses import dataclass

from apkdetective.domain.entities.analysis.sections.dex_file_contents import DexFileContents
from apkdetective.domain.entities.analysis.sections.dex_file_scan import DexFileScan


@dataclass(frozen=True)
class DexFileAnalysis:
    scan: DexFileScan
    contents: DexFileContents
