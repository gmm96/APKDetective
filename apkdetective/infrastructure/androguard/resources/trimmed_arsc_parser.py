"""
Androguard's parser of the resource table, for a table whose translations were removed (ResourceTableTrimmer).

Everything it answers is what the full table would answer, except the languages and the screens of the removed
chunks, which it adds back from the configurations that were kept aside.
"""

import io

from androguard.core.axml import ARSCParser, ARSCResTableConfig

from apkdetective.domain.entities.analysis.trimmed_resource_table import TrimmedResourceTable


class TrimmedArscParser(ARSCParser):
    def __init__(self, table: TrimmedResourceTable) -> None:
        super().__init__(table.data)
        self._removed = table.removed

    def get_locales(self, package_name: str) -> list[str]:
        locales = super().get_locales(package_name)
        known = set(locales)
        for config in self._removed_configs(package_name):
            locale = config.get_language_and_region()
            if locale not in known:
                known.add(locale)
                locales.append(locale)
        return locales

    def get_type_configs(self, package_name, type_name=None):
        if package_name is None:
            package_name = self.get_packages_names()[0]
        result = super().get_type_configs(package_name, type_name)
        package_index = self.get_packages_names().index(package_name)
        for removed in self._removed:
            if removed.package_index == package_index and type_name in (None, removed.type_name):
                result[removed.type_name].append(self._config(removed.config))
        return result

    @staticmethod
    def _config(raw: bytes) -> ARSCResTableConfig:
        return ARSCResTableConfig(io.BufferedReader(io.BytesIO(raw))) # type: ignore
        #return ARSCResTableConfig(io.BytesIO(raw))

    def _removed_configs(self, package_name: str) -> list[ARSCResTableConfig]:
        package_index = self.get_packages_names().index(package_name)
        return [self._config(removed.config)
                for removed in self._removed if removed.package_index == package_index]
