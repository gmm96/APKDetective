"""
How one thread asks another one to stop: the analysis runs in a worker and is checked at safe points
(between its steps and every 64 classes of a DEX file), so it stops cleanly instead of being killed.
"""

import threading

from apkdetective.domain.entities.analysis.analysis_cancelled_error import AnalysisCancelledError


class CancellationToken:
    def __init__(self) -> None:
        self._cancelled: threading.Event = threading.Event()

    def cancel(self) -> None:
        """Asks for the work to stop. Safe to call from any thread, more than once."""
        self._cancelled.set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled.is_set()

    def raise_if_cancelled(self) -> None:
        if self._cancelled.is_set():
            raise AnalysisCancelledError()
