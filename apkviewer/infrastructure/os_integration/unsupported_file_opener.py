"""
Fallback OsFileOpener for platforms with no native "open" integration.
"""

import sys

from apkviewer.ports.system.os_file_opener_port import OsFileOpenerPort


class UnsupportedFileOpener(OsFileOpenerPort):
    def open(self, path: str) -> None:
        raise RuntimeError(f"Opening files is not supported on platform: {sys.platform}")

    def open_with(self, path: str) -> None:
        raise RuntimeError(f"Open With is not supported on platform: {sys.platform}")
