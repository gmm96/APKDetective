"""
Zip-backed implementation of the ArchiveReader port (an APK is a zip).
"""

import zipfile
from datetime import datetime

from apkviewer.domain.entities.archive.archive_entry import ArchiveEntry
from apkviewer.ports.apk.archive_reader_port import ArchiveReaderPort


class ZipArchiveReader(ArchiveReaderPort):
    def list_entries(self, archive_path: str) -> list[ArchiveEntry]:
        with zipfile.ZipFile(archive_path, "r") as archive:
            return [
                self._to_entry(info)
                for info in archive.infolist()
                if info.filename and not info.is_dir()
            ]

    @classmethod
    def _to_entry(cls, info: zipfile.ZipInfo) -> ArchiveEntry:
        return ArchiveEntry(
            path=info.filename,
            size=info.file_size,
            compressed_size=info.compress_size,
            modified=cls._parse_mtime(info.date_time),
        )

    @staticmethod
    def _parse_mtime(date_time: tuple[int, int, int, int, int, int]) -> datetime | None:
        try:
            return datetime(*date_time)
        except ValueError:
            return None
