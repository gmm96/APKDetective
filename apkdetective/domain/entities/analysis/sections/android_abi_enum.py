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
