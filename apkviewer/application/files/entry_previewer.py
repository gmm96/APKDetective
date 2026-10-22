"""
Use case: work with APK entries "in place" - extract them into a scratch
workspace so they can be opened with the OS or copied to the clipboard.
"""

import os
from collections.abc import Sequence

from apkviewer.ports.apk.apk_extractor_port import ApkExtractorPort
from apkviewer.ports.system.clipboard_file_copier_port import ClipboardFileCopierPort
from apkviewer.ports.system.os_file_opener_port import OsFileOpenerPort
from apkviewer.ports.filesystem.temporary_workspace_port import TemporaryWorkspacePort


class EntryPreviewer:
    def __init__(
        self,
        extractor: ApkExtractorPort,
        workspace: TemporaryWorkspacePort,
        file_opener: OsFileOpenerPort,
        clipboard_copier: ClipboardFileCopierPort,
    ) -> None:
        self._extractor: ApkExtractorPort = extractor
        self._workspace: TemporaryWorkspacePort = workspace
        self._file_opener: OsFileOpenerPort = file_opener
        self._clipboard_copier: ClipboardFileCopierPort = clipboard_copier

    def prepare(self, apk_path: str, entry_paths: Sequence[str]) -> list[str]:
        """
        Extract the entries into the workspace and return one on-disk path
        per *requested* entry (a folder yields the folder itself, not each
        file it contains).
        """
        self._extractor.extract(apk_path, entry_paths, self._workspace.path)
        return [
            os.path.abspath(os.path.join(self._workspace.path, *entry.split("/")))
            for entry in entry_paths
        ]

    def open(self, local_path: str) -> None:
        self._file_opener.open(local_path)

    def open_with(self, local_path: str) -> None:
        self._file_opener.open_with(local_path)

    def copy_to_clipboard(self, local_paths: list[str]) -> bool:
        """Put the files on the clipboard; False when the platform cannot do it."""
        return self._clipboard_copier.copy(local_paths)

    def reset(self) -> None:
        """Discard previously extracted files (call whenever a new APK is loaded)."""
        self._workspace.reset()

    def dispose(self) -> None:
        """Release the workspace (call on application shutdown)."""
        self._workspace.dispose()
