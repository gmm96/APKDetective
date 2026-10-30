"""
Pauses Python's cyclic garbage collector while an APK is analysed.

Androguard builds millions of small objects that stay alive until the analysis ends (the entries of the resource
table, the strings and classes of the code...). The collector keeps walking all of them, looking for cycles that
are not there: about a tenth of the time of the analysis of a big app (2,300 collections of the youngest objects
and 10 full ones in the YouTube APK). Nothing is lost by letting it wait: what the analysis leaves behind is
collected when it is over, in the thread of the analysis and not in the middle of drawing the window.
"""

import gc
from types import TracebackType


class PausedGarbageCollector:
    def __init__(self) -> None:
        self._was_enabled: bool = False

    def __enter__(self) -> "PausedGarbageCollector":
        self._was_enabled = gc.isenabled()
        gc.disable()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._was_enabled:  # if someone else had it off, it stays off
            gc.enable()
            gc.collect()
