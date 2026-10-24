"""
Raised by an analysis that stopped because the user asked it to.
"""


class AnalysisCancelledError(Exception):
    """Not a failure: the analysis was interrupted on purpose and has no result."""

    def __init__(self) -> None:
        super().__init__("The analysis was cancelled.")
