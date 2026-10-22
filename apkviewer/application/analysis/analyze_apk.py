"""
Use case: analyze an APK and return everything a front end needs to show it.
"""

from apkviewer.application.files.file_tree_builder import FileTreeBuilder
from apkviewer.domain.entities.analysis.analysis_result import AnalysisResult
from apkviewer.ports.apk.apk_inspector_port import ApkInspectorPort
from apkviewer.ports.apk.archive_reader_port import ArchiveReaderPort


class AnalyzeApk:
    def __init__(
        self,
        inspector: ApkInspectorPort,
        archive_reader: ArchiveReaderPort,
        tree_builder: FileTreeBuilder | None = None,
    ) -> None:
        self._inspector: ApkInspectorPort = inspector
        self._archive_reader: ArchiveReaderPort = archive_reader
        self._tree_builder: FileTreeBuilder = tree_builder or FileTreeBuilder()

    def execute(self, apk_path: str) -> AnalysisResult:
        inspection = self._inspector.inspect(apk_path)
        file_tree = self._tree_builder.build(self._archive_reader.list_entries(apk_path))
        return AnalysisResult(apk_path=apk_path, inspection=inspection, file_tree=file_tree)
