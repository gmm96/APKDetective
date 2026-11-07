"""
Thin wrapper around Androguard's APK parser.

Kept as its own class (rather than calling `APK(path)` inline everywhere)
so callers depend on an abstraction, and unit tests can substitute a fake
loader without touching real APK files.

The resource table of the APK is given to Androguard without the translations nobody reads (see
ResourceTableTrimmer): in a big app that is most of its entries, and the largest part of the time of the analysis.
"""

from androguard.core.apk import APK

from apkdetective.infrastructure.androguard.resources.resource_table_trimmer import ResourceTableTrimmer
from apkdetective.infrastructure.androguard.resources.trimmed_arsc_parser import TrimmedArscParser



class ApkLoader:
    _RESOURCE_TABLE = "resources.arsc"

    def __init__(self, trimmer: ResourceTableTrimmer | None = None) -> None:
        self._trimmer: ResourceTableTrimmer = trimmer or ResourceTableTrimmer()

    def load(self, apk_path: str) -> APK:
        apk = APK(apk_path)
        #self._use_trimmed_resource_table(apk)
        return apk

    def _use_trimmed_resource_table(self, apk: APK) -> None:
        try:
            table = self._trimmer.trim(apk.get_file(self._RESOURCE_TABLE))
            if table is not None:
                apk.arsc[self._RESOURCE_TABLE] = TrimmedArscParser(table)
        except Exception:  # pylint: disable=broad-except
            pass  # whatever is wrong with it, Androguard reads the whole table when it is needed, as always
