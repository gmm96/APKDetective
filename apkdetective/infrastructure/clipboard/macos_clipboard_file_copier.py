"""
macOS implementation of ClipboardFileCopier: puts the files on the general pasteboard as file URLs, the
same way Finder's "Copy" does, so they can be pasted into Finder, Mail, Messages...

It is done with a small JavaScript for Automation script run by `osascript`, which ships with macOS: the
pasteboard is only reachable through AppKit, and this avoids a Python dependency (PyObjC) for one call.
"""

import subprocess
from pathlib import Path

from apkdetective.ports.system.clipboard_file_copier_port import ClipboardFileCopierPort


class MacClipboardFileCopier(ClipboardFileCopierPort):
    # The paths arrive as the arguments of the script, never inside its text, so no name can break out of it.
    _SCRIPT: str = (
        'ObjC.import("AppKit");'
        "function run(paths) {"
        "  var urls = $.NSMutableArray.alloc.init;"
        "  for (var i = 0; i < paths.length; i++) { urls.addObject($.NSURL.fileURLWithPath(paths[i])); }"
        "  var pasteboard = $.NSPasteboard.generalPasteboard;"
        "  pasteboard.clearContents;"
        '  if (!pasteboard.writeObjects(urls)) { throw new Error("the pasteboard rejected the files"); }'
        "}"
    )
    _TIMEOUT_SECONDS: int = 10

    def copy(self, file_paths: list[str]) -> bool:
        if not file_paths:
            return False
        absolute_paths = [str(Path(path).absolute()) for path in file_paths]
        command = ["osascript", "-l", "JavaScript", "-e", self._SCRIPT, *absolute_paths]
        try:
            subprocess.run(
                command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=self._TIMEOUT_SECONDS
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return True
