"""
Shows where the time of an analysis goes, with the real code of the application.

    python utils/profile_analysis.py path/to/app.apk
    python utils/profile_analysis.py path/to/app.apk --cprofile      # also a function-by-function profile

It runs the same use case the window runs (AnalyzeApk) and puts a stopwatch on each of its steps, without
changing anything in them (with --cprofile the totals are inflated by the profiler itself: look at the shares,
not at the seconds). Run it twice: the first time the operating system (or the antivirus) may still
have to read the file from the disk, and the second it usually has it in memory; the difference is what the
disk costs.
"""

import argparse
import cProfile
import os
import platform
import pstats
import sys
import time
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# pylint: disable=wrong-import-position,import-error
from apkdetective.application.analysis.analyze_apk import AnalyzeApk
from apkdetective.application.files.file_tree_builder import FileTreeBuilder
from apkdetective.infrastructure.androguard.androguard_apk_inspector import AndroguardApkInspector
from apkdetective.infrastructure.androguard.apk_loader import ApkLoader
from apkdetective.infrastructure.zip.zip_archive_reader import ZipArchiveReader

READ_CHUNK_BYTES = 8 * 1024 * 1024


class StepTimer:
    """Wraps methods so that the time each call takes is recorded under a name."""

    def __init__(self) -> None:
        self.steps: list[tuple[str, float]] = []

    def around(self, owner: type, method_name: str, label: str) -> None:
        original = owner.__dict__[method_name]
        function = original.__func__ if isinstance(original, staticmethod) else original

        def timed(*args, **kwargs):
            started = time.perf_counter()
            try:
                return function(*args, **kwargs)
            finally:
                self.steps.append((label, time.perf_counter() - started))

        setattr(owner, method_name, staticmethod(timed) if isinstance(original, staticmethod) else timed)

    def around_guarded_steps(self) -> None:
        """The inspector runs each of its steps through _guarded(warnings, cancellation, what, ...)."""
        original = AndroguardApkInspector.__dict__["_guarded"].__func__

        def timed(warnings, cancellation, what, sections, read: Callable, default):  # pylint: disable=too-many-arguments,too-many-positional-arguments
            started = time.perf_counter()
            try:
                return original(warnings, cancellation, what, sections, read, default)
            finally:
                self.steps.append((what, time.perf_counter() - started))

        AndroguardApkInspector._guarded = staticmethod(timed)  # type: ignore[assignment]  # pylint: disable=protected-access


def time_reading(path: Path) -> float:
    started = time.perf_counter()
    with open(path, "rb", buffering=0) as source:
        while source.read(READ_CHUNK_BYTES):
            pass
    return time.perf_counter() - started


def print_report(apk_path: Path, total: float, steps: list[tuple[str, float]], read_seconds: float) -> None:
    size_mb = apk_path.stat().st_size / 1e6
    print(f"\nFile:   {apk_path.name} ({size_mb:.1f} MB)")
    print(f"System: {platform.platform()} | Python {platform.python_version()} | {os.cpu_count()} CPUs")
    print(f"Reading the whole file once, sequentially: {read_seconds:.2f} s ({size_mb / read_seconds:.0f} MB/s)\n")
    print(f"{'seconds':>8} {'%':>6}  step")
    for label, seconds in sorted(steps, key=lambda step: -step[1]):
        print(f"{seconds:8.2f} {seconds / total * 100:5.1f}%  {label}")
    accounted = sum(seconds for _, seconds in steps)
    print(f"{total - accounted:8.2f} {(total - accounted) / total * 100:5.1f}%  (anything else in the use case)")
    print(f"{total:8.2f} 100.0%  TOTAL of AnalyzeApk.execute")


def main() -> None:
    parser = argparse.ArgumentParser(description="Where does the time of an analysis go?")
    parser.add_argument("apk", type=Path)
    parser.add_argument("--cprofile", action="store_true", help="also profile every function (slower)")
    arguments = parser.parse_args()
    if not arguments.apk.is_file():
        sys.exit(f"{arguments.apk} is not a file")

    read_seconds = time_reading(arguments.apk)  # before the analysis, so the disk is measured and not the cache of it

    timer = StepTimer()
    timer.around(ApkLoader, "load", "open the APK (Androguard)")
    timer.around_guarded_steps()
    timer.around(ZipArchiveReader, "list_entries", "list the files of the APK (Files tab)")
    timer.around(FileTreeBuilder, "build", "build the tree of files (Files tab)")

    use_case = AnalyzeApk(AndroguardApkInspector(), ZipArchiveReader())
    profiler = cProfile.Profile() if arguments.cprofile else None
    started = time.perf_counter()
    if profiler:
        profiler.enable()
    result = use_case.execute(str(arguments.apk))
    if profiler:
        profiler.disable()
    total = time.perf_counter() - started

    print_report(arguments.apk, total, timer.steps, read_seconds)
    warnings = result.inspection.warnings
    if warnings:
        print(f"\nThe analysis produced {len(warnings)} warning(s), such as:")
        for warning in list(warnings)[:5]:
            print(f"  - {warning}")
    if profiler:
        output = Path("profile_analysis.prof")
        profiler.dump_stats(str(output))
        print(f"\nTop functions by cumulative time (saved in {output}):")
        pstats.Stats(profiler).sort_stats("cumulative").print_stats(30)


if __name__ == "__main__":
    main()
