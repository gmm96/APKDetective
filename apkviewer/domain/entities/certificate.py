"""
A signing certificate of an APK.
"""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Certificate:
    """Every field is None when it could not be read."""
    issuer: str | None
    subject: str | None
    serial_number: str | None = None
    md5: str | None = None
    sha1: str | None = None
    sha256: str | None = None
    signature_algorithm: str | None = None  # e.g. "SHA256withRSA"
    public_key: str | None = None           # e.g. "RSA 2048-bit"
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    @property
    def is_readable(self) -> bool:
        return self.issuer is not None or self.subject is not None

    def is_expired(self, now: datetime) -> bool:
        return self.valid_until is not None and self._as_utc(self.valid_until) < self._as_utc(now)

    def valid_from_text(self) -> str | None:
        return self._utc_text(self.valid_from) if self.valid_from else None

    def valid_until_text(self) -> str | None:
        return self._utc_text(self.valid_until) if self.valid_until else None

    def as_text(self) -> str:
        """All the readable fields, one 'Label: value' per line."""
        if not self.is_readable:
            return "Unknown / Encrypted Certificate"
        fields = (
            ("Subject", self.subject),
            ("Issuer", self.issuer),
            ("Serial number", self.serial_number),
            ("Valid from", self.valid_from_text()),
            ("Valid until", self.valid_until_text()),
            ("Public key", self.public_key),
            ("Signature algorithm", self.signature_algorithm),
            ("SHA-256", self.sha256),
            ("SHA-1", self.sha1),
            ("MD5", self.md5),
        )
        return "\n".join(f"{label}: {value}" for label, value in fields if value)

    @staticmethod
    def _as_utc(moment: datetime) -> datetime:
        """Naive datetimes are taken as UTC, so aware and naive ones can be compared."""
        if moment.tzinfo is None:
            return moment.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc)

    @classmethod
    def _utc_text(cls, moment: datetime) -> str:
        return cls._as_utc(moment).strftime("%Y-%m-%d %H:%M:%S UTC")
