"""
Linux implementation of ClipboardFileCopier: tries the X11 clipboard
(xclip) first, then falls back to Wayland (wl-copy).
"""

import subprocess
from pathlib import Path

from apkdetective.ports.system.clipboard_file_copier_port import ClipboardFileCopierPort


class LinuxClipboardFileCopier(ClipboardFileCopierPort):
    _COMMANDS: tuple[list[str], list[str]] = (
        ["xclip", "-i", "-selection", "clipboard", "-t", "text/uri-list"],
        ["wl-copy", "-t", "text/uri-list"],
    )

    def copy(self, file_paths: list[str]) -> bool:
        # as_uri() percent-encodes the path: names with spaces or accents are not valid URIs as they are.
        payload = "\n".join(Path(path).absolute().as_uri() for path in file_paths).encode("utf-8")
        return any(self._try_run(command, payload) for command in self._COMMANDS)

    @staticmethod
    def _try_run(command: list[str], payload: bytes) -> bool:
        try:
            subprocess.run(command, input=payload, check=True, stderr=subprocess.DEVNULL)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
