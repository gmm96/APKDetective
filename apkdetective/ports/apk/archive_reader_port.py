"""
Port for listing the files stored inside an archive (an APK is a zip).
"""

from abc import ABC, abstractmethod

from apkdetective.domain.entities.archive.archive_entry import ArchiveEntry


class ArchiveReaderPort(ABC):
    @abstractmethod
    def list_entries(self, archive_path: str) -> list[ArchiveEntry]:
        """Return every file (not folder) stored in the archive."""
        raise NotImplementedError
