"""
FileWriter implementation backed by the local file system.
"""

from apkviewer.ports.filesystem.file_writer_port import FileWriterPort


class LocalFileWriter(FileWriterPort):
    def write_text(self, path: str, content: str) -> None:
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)

    def write_bytes(self, path: str, data: bytes) -> None:
        with open(path, "wb") as file:
            file.write(data)
