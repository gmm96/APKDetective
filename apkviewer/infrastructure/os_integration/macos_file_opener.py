"""
macOS implementation of OsFileOpener, backed by the `open` command.
"""

import subprocess

from apkviewer.domain.interfaces.os_file_opener import OsFileOpener


class MacFileOpener(OsFileOpener):
    def open(self, path: str) -> None:
        self._launch(["open", path])

    def open_with(self, path: str) -> None:
        self._launch(["open", "-R", path])

    @staticmethod
    def _launch(command: list[str]) -> None:
        # Not waited for: the Tk window must not freeze until the other application is closed.
        subprocess.Popen(  # pylint: disable=consider-using-with
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
        )
