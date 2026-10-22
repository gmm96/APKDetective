"""
Parsing and wording of Android permission protection levels, written as
'base|flag|flag' (e.g. 'dangerous' or 'signature|privileged').
"""


class ProtectionLevel:
    _BASE_LEVELS: dict[int, str] = {0: "normal", 1: "dangerous", 2: "signature", 3: "signatureOrSystem"}
    _FLAGS: tuple[tuple[int, str], ...] = (
        (0x10, "privileged"), (0x20, "development"), (0x40, "appop"), (0x80, "pre23"),
        (0x100, "installer"), (0x200, "verifier"), (0x400, "preinstalled"), (0x800, "setup"),
        (0x1000, "instant"), (0x2000, "runtime"), (0x4000, "oem"), (0x8000, "vendorPrivileged"),
    )
    _TITLES: dict[str, str] = {
        "normal": "Normal",
        "dangerous": "Dangerous",
        "signature": "Signature",
        "signatureorsystem": "Signature or system",
    }

    @classmethod
    def parse(cls, raw: str | None) -> str | None:
        """
        Normalize a protection level to the 'base|flag|flag' form. Accepts that form
        already, or the number a compiled manifest stores (e.g. '0x00000012' ->
        'signature|privileged'). None if it can't be read.
        """
        if raw is None or not raw.strip():
            return None
        text = raw.strip()
        try:
            value = int(text, 0)
        except ValueError:
            return text  # already names
        base = cls._BASE_LEVELS.get(value & 0xF)
        if base is None:
            return None
        flags = [name for bit, name in cls._FLAGS if value & bit]
        return "|".join([base, *flags])

    @classmethod
    def describe(cls, protection: str | None) -> str:
        """Readable form: 'Dangerous', 'Signature (privileged, appop)', 'Unknown'."""
        if not protection:
            return "Unknown"
        tokens = protection.split("|")
        base = next((token for token in tokens if token.lower() in cls._TITLES), None)
        if base is None:
            return protection
        flags = [token for token in tokens if token != base]
        title = cls._TITLES[base.lower()]
        return f"{title} ({', '.join(flags)})" if flags else title

    @staticmethod
    def includes(protection: str | None, token: str) -> bool:
        """Whether the level (or one of its flags) is `token`, e.g. 'dangerous' or 'appop'."""
        return protection is not None and token in protection.split("|")
