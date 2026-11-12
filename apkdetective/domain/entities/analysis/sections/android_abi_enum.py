"""
The CPU architectures (ABIs) an Android app can ship native code for, in the order the UI lists them.
Each value is the name of the folder under lib/ that holds the native libraries of that ABI.
"""

from enum import Enum


class AndroidAbiEnum(Enum):
    ARM64_V8A = "arm64-v8a"
    ARMEABI_V7A = "armeabi-v7a"
    X86_64 = "x86_64"
    X86 = "x86"
    RISCV64 = "riscv64"
    ARMEABI = "armeabi"
    MIPS = "mips"
    MIPS64 = "mips64"
    ARMEABI_V7A_HARD = "armeabi-v7a-hard"

    @property
    def description(self) -> str:
        """What this architecture is and where it is found."""
        return _DESCRIPTIONS[self]

    @classmethod
    def describe(cls, name: str) -> str | None:
        """The description of the ABI called `name`, or None when it is not a known ABI."""
        try:
            return cls(name).description
        except ValueError:
            return None


_DESCRIPTIONS: dict[AndroidAbiEnum, str] = {
    AndroidAbiEnum.ARM64_V8A: "64-bit ARM. The current standard architecture for modern Android devices.",
    AndroidAbiEnum.ARMEABI_V7A: "32-bit ARM. Widely supported by older and budget devices.",
    AndroidAbiEnum.X86_64: "64-bit x86. Used primarily for Android emulators and Chromebooks.",
    AndroidAbiEnum.X86: "32-bit x86. Used for older emulators and legacy Intel-based devices.",
    AndroidAbiEnum.RISCV64: "64-bit RISC-V. An emerging open-standard architecture recently supported by Android.",
    AndroidAbiEnum.ARMEABI: "Legacy 32-bit ARM (ARMv5). Deprecated and no longer supported by modern NDKs.",
    AndroidAbiEnum.MIPS: "32-bit MIPS. Deprecated and removed from the Android NDK.",
    AndroidAbiEnum.MIPS64: "64-bit MIPS. Deprecated and removed from the Android NDK.",
    AndroidAbiEnum.ARMEABI_V7A_HARD: "32-bit ARM with hardware floating-point. Obsolete in modern Android.",
}
