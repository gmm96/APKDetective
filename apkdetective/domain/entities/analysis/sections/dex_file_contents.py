"""
What one DEX file contains that the analysis cares about, already boiled down to what is needed afterwards: the
strings themselves are not kept, only what the analysis takes from them. It is what a worker process sends back, so it
is kept small, and it can be added to the ones of the other files in any order.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DexFileContents:
    number: int  # the position of the file among the DEX files of the APK, from 1
    class_names: tuple[str, ...] = ()  # type descriptors, e.g. "Lcom/example/Main;"
    string_characters: int = 0
    urls: tuple[str, ...] = ()  # HTTP/HTTPS URLs written in its strings, without repeats
    problem: str | None = None  # what could not be read from the file, as the end of a sentence about it
