"""
Port for "look inside an APK and describe it". The concrete library used
to parse APKs is an implementation detail of the infrastructure layer.
"""

from abc import ABC, abstractmethod

from apkviewer.domain.entities.analysis.apk_inspection import ApkInspection
from apkviewer.domain.entities.analysis.cancellation_token import CancellationToken


class ApkInspectorPort(ABC):
    @abstractmethod
    def inspect(self, apk_path: str, cancellation: CancellationToken) -> ApkInspection:
        """
        Describes the APK. Checks `cancellation` at safe points and raises AnalysisCancelledError
        as soon as it is cancelled, so the work stops at the next one rather than instantly.
        """
        raise NotImplementedError
