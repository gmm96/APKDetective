"""
Use case: save the launcher icon of an analyzed APK as a PNG file.
"""

from apkviewer.domain.entities.analysis.analysis_result import AnalysisResult
from apkviewer.ports.filesystem.file_writer_port import FileWriterPort


class ExportIcon:
    def __init__(self, writer: FileWriterPort) -> None:
        self._writer: FileWriterPort = writer

    def execute(self, result: AnalysisResult, dest_path: str) -> None:
        if result.icon_png is None:
            raise ValueError("The analyzed APK has no raster icon to export.")
        self._writer.write_bytes(dest_path, result.icon_png)
