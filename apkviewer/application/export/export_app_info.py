"""
Use case: save the analysis as a plain text report.
"""

from apkviewer.application.export.app_info_serializer import AppInfoSerializer
from apkviewer.domain.entities.analysis.analysis_result import AnalysisResult
from apkviewer.ports.filesystem.file_writer_port import FileWriterPort


class ExportAppInfo:
    def __init__(self, writer: FileWriterPort, serializer: AppInfoSerializer | None = None) -> None:
        self._writer: FileWriterPort = writer
        self._serializer: AppInfoSerializer = serializer or AppInfoSerializer()

    def execute(self, result: AnalysisResult, dest_path: str) -> None:
        self._writer.write_text(dest_path, self._serializer.format(result))
