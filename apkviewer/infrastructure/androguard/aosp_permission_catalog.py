"""
What Android itself says about a permission (protection level, label,
description), from the AOSP permission database bundled with androguard.

The most complete (newest) database is used instead of the one matching
the app's targetSdk: an app that targets an old release still runs on
current Android, where permissions such as MANAGE_EXTERNAL_STORAGE exist.
"""

from typing import Any

from androguard.core import androconf

# Asking androguard for a level above the newest one returns the newest database.
# (Not androconf.CONF["DEFAULT_API"]: that is 16, where INTERNET is "dangerous".)
_NEWEST_API: int = 10_000


class AospPermissionCatalog:
    def __init__(self) -> None:
        self._entries: dict[str, Any] | None = None

    def lookup(self, name: str) -> dict[str, Any] | None:
        """The AOSP entry of `name`, or None if the database doesn't define it."""
        return self._load().get(name)

    def _load(self) -> dict[str, Any]:
        if self._entries is None:
            try:
                self._entries = dict(
                    androconf.load_api_specific_resource_module("aosp_permissions", _NEWEST_API)
                )
            except Exception:  # pylint: disable=broad-except
                self._entries = {}
        return self._entries
