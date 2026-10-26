"""
Use case: analyze an APK and return everything a front end needs to show it.
"""

from apkdetective.application.files.file_tree_builder import FileTreeBuilder
from apkdetective.domain.entities.analysis.analysis_result import AnalysisResult
from apkdetective.domain.entities.analysis.cancellation_token import CancellationToken
from apkdetective.ports.apk.apk_inspector_port import ApkInspectorPort
from apkdetective.ports.apk.archive_reader_port import ArchiveReaderPort


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

    def execute(self, apk_path: str, cancellation: CancellationToken | None = None) -> AnalysisResult:
        """
        Raises AnalysisCancelledError when `cancellation` is cancelled before the result is ready;
        a cancellation that arrives just as the last step ends is honoured too.
        """
        cancellation = cancellation or CancellationToken()
        inspection = self._inspector.inspect(apk_path, cancellation)
        cancellation.raise_if_cancelled()
        entries = self._archive_reader.list_entries(apk_path)
        cancellation.raise_if_cancelled()
        file_tree = self._tree_builder.build(entries)
        cancellation.raise_if_cancelled()
        return AnalysisResult(apk_path=apk_path, inspection=inspection, file_tree=file_tree)
