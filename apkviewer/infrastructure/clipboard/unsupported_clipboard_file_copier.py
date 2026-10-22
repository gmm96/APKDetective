"""
Fallback for platforms with no native file-clipboard integration.
"""

from apkviewer.ports.system.clipboard_file_copier_port import ClipboardFileCopierPort


class UnsupportedClipboardFileCopier(ClipboardFileCopierPort):
    def copy(self, file_paths: list[str]) -> bool:
        return False
