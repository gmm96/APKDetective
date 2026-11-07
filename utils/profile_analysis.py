"""
Shows where the time of an analysis goes, with the real code of the application.

    python utils/profile_analysis.py path/to/app.apk
    python utils/profile_analysis.py path/to/app.apk --dex-in-process   # no worker processes, to compare
    python utils/profile_analysis.py path/to/app.apk --cprofile         # also a function-by-function profile

It runs the same use case the window runs (AnalyzeApk) and puts a stopwatch on each of its steps, without
changing anything in them. The report has four parts:

- the steps of the use case, one after the other: they add up to the total;
- what happens INSIDE those steps (the resource table of Androguard, the end of the DEX analysis, the resolution of
  resource references...): already counted above, shown to see what a step is made of;
- the repeated work: the same call made again with the same argument, which a cache shared by the extractors would save;
- the critical path: when the worker processes had scanned each DEX file and whether the main process had to wait for
  them (if it did not, making the scan faster would not shorten the analysis).

Run it from a plain terminal, not from the debugger: debugpy made the same APK take four times longer, and it also
follows the worker processes. Run it twice too: the first time the operating system (or the antivirus) may still have
to read the file from the disk, and the second it usually has it in memory; the difference is what the disk costs.
With --cprofile the totals are inflated by the profiler itself (look at the shares, not at the seconds) and only this
process is profiled, not the workers.
"""

# pylint: disable=duplicate-code  # standalone script: it shares no module with profile_ui.py on purpose
import argparse
import collections
import cProfile
import inspect
import os
import platform
import pstats
import sys
import threading
import time
from collections.abc import Callable, Hashable
from pathlib import Path
from typing import Any, NamedTuple

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
if __name__ == "__main__":
    # The workers that scan the DEX files are started with "spawn": each one begins by importing the main module of the
    # program. In the application that is main.py, which imports almost nothing; this file imports Androguard and more,
    # so here the workers would start later than in the application. They are told that the main module is main.py.
    sys.modules["__main__"].__file__ = str(ROOT_DIR / "main.py")

# pylint: disable=wrong-import-position,import-error
from androguard.core.apk import APK
from androguard.core.axml import ARSCParser

from apkdetective.application.analysis.analyze_apk import AnalyzeApk
from apkdetective.application.files.file_tree_builder import FileTreeBuilder
from apkdetective.infrastructure.androguard.androguard_apk_inspector import AndroguardApkInspector
from apkdetective.infrastructure.androguard.apk_loader import ApkLoader
from apkdetective.infrastructure.androguard.dex.dex_analysis_starter import DexAnalysisStarter
from apkdetective.infrastructure.androguard.dex.dex_analyzer import DexAnalyzer
from apkdetective.infrastructure.androguard.dex.dex_reader import DexReader
from apkdetective.infrastructure.androguard.dex.parallel_dex_analysis_job import ParallelDexAnalysisJob
from apkdetective.infrastructure.androguard.extractors.dex_metrics_extractor import DexMetricsExtractor
from apkdetective.infrastructure.androguard.extractors.embedded_content_extractor import EmbeddedContentExtractor
from apkdetective.infrastructure.androguard.manifest.resource_reference_resolver import ResourceReferenceResolver
from apkdetective.infrastructure.androguard.paused_garbage_collector import PausedGarbageCollector
from apkdetective.infrastructure.zip.zip_archive_reader import ZipArchiveReader

READ_CHUNK_BYTES = 8 * 1024 * 1024
DEX_IN_PROCESS_VARIABLE = "APKDETECTIVE_DEX_IN_PROCESS"  # the same switch composition_root.py reads
WATCH_INTERVAL_S = 0.02
HIDDEN_DEX_WAIT_S = 0.2  # a wait shorter than this is noise, not a bottleneck

# The inspector guards two steps with the same text; these are the names they get in the report.
GUARDED_NAMES = {
    ("The code (DEX) of the app", 1): "read the DEX files out of the APK",
    ("The code (DEX) of the app", 2): "wait for the DEX analysis (started earlier)",
}
WAIT_FOR_DEX = GUARDED_NAMES[("The code (DEX) of the app", 2)]
DEX_MERGE = "DEX: strings, packages, URLs and totals (DexAnalyzer.analyze, in this process)"


class Step(NamedTuple):
    label: str
    offset: float   # seconds since the analysis began
    seconds: float


def find_tracers() -> list[str]:
    """Whatever is watching every line this process runs (a debugger, a coverage tool...): it slows Python down a lot."""
    # pylint: disable=no-member  # the stubs of sys.monitoring that pylint knows lack get_tool
    found: list[str] = [name for name in ("debugpy", "pydevd", "pydevd_pycharm", "coverage") if name in sys.modules]
    if sys.gettrace() is not None:
        found.append("a sys.settrace hook")
    if sys.getprofile() is not None:
        found.append("a sys.setprofile hook")
    monitoring: Any = getattr(sys, "monitoring", None)  # Python 3.12+
    if monitoring is not None:
        found.extend(f"sys.monitoring tool '{monitoring.get_tool(tool_id)}'" for tool_id in range(6)
                     if monitoring.get_tool(tool_id))
    return found


class DexScanWatcher(threading.Thread):
    """Notes when the worker process of each DEX file has finished scanning it."""

    def __init__(self, scans: list, origin: float) -> None:
        super().__init__(daemon=True)
        self._scans = scans
        self._origin = origin
        self._stop_event = threading.Event()
        self.finished: dict[int, float] = {}  # DEX file number -> seconds since the analysis began

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while len(self.finished) < len(self._scans) and not self._stop_event.wait(WATCH_INTERVAL_S):
            for number, scan in enumerate(self._scans, start=1):
                if number not in self.finished and scan.ready():
                    self.finished[number] = time.perf_counter() - self._origin


class StepTimer:
    """Wraps methods so that the time each call takes is recorded under a name."""

    def __init__(self) -> None:
        self.origin = 0.0
        self.steps: list[Step] = []    # one after the other: they add up to the use case
        self.inside: list[Step] = []   # inside those steps: shown, never added up
        self.repeats: dict[str, list[tuple[Hashable, float]]] = collections.defaultdict(list)
        self.watchers: list[DexScanWatcher] = []
        self._occurrences: collections.Counter[str] = collections.Counter()

    def begin(self) -> None:
        self.origin = time.perf_counter()

    def around(
        self, owner: type, method_name: str, label: str, nested: bool = False,
        key: Callable[..., Hashable] | None = None,
    ) -> None:
        """`key` (optional) says what a call was about, to tell afterwards which calls repeated the work of another."""
        try:
            original = inspect.getattr_static(owner, method_name)
        except AttributeError:
            print(f"(cannot time {owner.__name__}.{method_name}: it does not exist any more)", file=sys.stderr)
            return
        function = original.__func__ if isinstance(original, staticmethod) else original
        target = self.inside if nested else self.steps

        def timed(*args, **kwargs):
            started = time.perf_counter()
            try:
                return function(*args, **kwargs)
            finally:
                seconds = time.perf_counter() - started
                target.append(Step(label, started - self.origin, seconds))
                if key is not None:
                    self.repeats[label].append((key(*args, **kwargs), seconds))

        setattr(owner, method_name, staticmethod(timed) if isinstance(original, staticmethod) else timed)

    def around_guarded_steps(self) -> None:
        """The inspector runs each of its steps through _guarded(warnings, cancellation, what, ...)."""
        original = inspect.getattr_static(AndroguardApkInspector, "_guarded").__func__

        def timed(warnings, cancellation, what, sections, read: Callable, default):  # pylint: disable=too-many-arguments,too-many-positional-arguments
            self._occurrences[what] += 1
            label = GUARDED_NAMES.get((what, self._occurrences[what]), what)
            started = time.perf_counter()
            try:
                return original(warnings, cancellation, what, sections, read, default)
            finally:
                self.steps.append(Step(label, started - self.origin, time.perf_counter() - started))

        AndroguardApkInspector._guarded = staticmethod(timed)  # type: ignore[assignment]  # pylint: disable=protected-access

    def watch_dex_workers(self) -> None:
        """When the DEX analysis runs in worker processes, watches them: the report says when each file was done."""
        original = ParallelDexAnalysisJob.__init__

        def init(job: ParallelDexAnalysisJob, *args, **kwargs) -> None:
            original(job, *args, **kwargs)
            watcher = DexScanWatcher(job._scans, self.origin)  # pylint: disable=protected-access
            self.watchers.append(watcher)
            watcher.start()

        ParallelDexAnalysisJob.__init__ = init  # type: ignore[method-assign,assignment]

    def stop_watching(self) -> None:
        for watcher in self.watchers:
            watcher.stop()

    def dex_mode(self) -> str:
        if not self.watchers:
            return "in this process (no worker processes)"
        return f"{len(self.watchers[0].finished) or 'several'} DEX file(s) scanned in worker processes ({os.cpu_count()} CPUs)"


def time_reading(path: Path) -> float:
    started = time.perf_counter()
    with open(path, "rb", buffering=0) as source:
        while source.read(READ_CHUNK_BYTES):
            pass
    return time.perf_counter() - started


def totals_by_label(steps: list[Step]) -> list[tuple[str, int, float]]:
    """(label, calls, seconds) of every label, the slowest first."""
    calls: dict[str, int] = collections.defaultdict(int)
    seconds: dict[str, float] = collections.defaultdict(float)
    for step in steps:
        calls[step.label] += 1
        seconds[step.label] += step.seconds
    return sorted(((label, calls[label], seconds[label]) for label in calls), key=lambda row: -row[2])


def print_steps(timer: StepTimer, total: float) -> None:
    print("Steps of the use case, one after the other (they add up to the total):")
    print(f"{'seconds':>8} {'%':>6}  step")
    for label, _, seconds in totals_by_label(timer.steps):
        print(f"{seconds:8.2f} {seconds / total * 100:5.1f}%  {label}")
    accounted = sum(step.seconds for step in timer.steps)
    print(f"{total - accounted:8.2f} {(total - accounted) / total * 100:5.1f}%  (anything else in the use case)")
    print(f"{total:8.2f} 100.0%  TOTAL of AnalyzeApk.execute")


def print_inside(timer: StepTimer, total: float) -> None:
    if not timer.inside:
        return
    print("\nInside those steps (already counted above, so they do not add up):")
    print(f"{'seconds':>8} {'%':>6} {'calls':>6}  what")
    for label, calls, seconds in totals_by_label(timer.inside):
        print(f"{seconds:8.2f} {seconds / total * 100:5.1f}% {calls:6d}  {label}")


def print_repeats(timer: StepTimer) -> None:
    rows = []
    for label, made in timer.repeats.items():
        seen: set[Hashable] = set()
        repeated = 0.0
        for key, seconds in made:
            if key in seen:
                repeated += seconds
            seen.add(key)
        if len(seen) < len(made):
            rows.append((repeated, label, len(made), len(seen)))
    if not rows:
        return
    print("\nRepeated work (the same call with the same argument, made again):")
    for repeated, label, calls, distinct in sorted(rows, reverse=True):
        print(f"  {repeated:6.2f} s  {label}: {calls} calls for {distinct} different arguments")


def print_critical_path(timer: StepTimer) -> None:
    wait = next((step for step in timer.steps if step.label == WAIT_FOR_DEX), None)
    if wait is None or not timer.watchers:
        return
    merge = sum(step.seconds for step in timer.inside if step.label == DEX_MERGE)
    waited = max(0.0, wait.seconds - merge)  # the wait for the workers and, once they are done, the merge
    print("\nCritical path (seconds since the analysis began):")
    for number, finished in sorted(timer.watchers[0].finished.items()):
        print(f"  DEX file #{number} scanned by its worker at {finished:6.2f}")
    print(f"  the main process got to the DEX at {wait.offset:6.2f} and then waited {waited:.2f} s for the workers")
    if waited < HIDDEN_DEX_WAIT_S:
        print("  -> the scan of the DEX files is hidden behind the rest: making it faster would not shorten the analysis")
    else:
        print(f"  -> the main process was idle for {waited:.2f} s: a faster scan, or starting it earlier, "
              f"would shorten the analysis by up to that")
    print(f"  after the scans, {merge:.2f} s more of work in this process (strings, packages, URLs): "
          f"always on the critical path")


def print_report(apk_path: Path, total: float, timer: StepTimer, read_seconds: float, tracers: list[str]) -> None:
    size_mb = apk_path.stat().st_size / 1e6
    print(f"\nFile:   {apk_path.name} ({size_mb:.1f} MB)")
    print(f"System: {platform.platform()} | Python {platform.python_version()} | {os.cpu_count()} CPUs")
    print(f"DEX analysis: {timer.dex_mode()}")
    print(f"Reading the whole file once, sequentially: {read_seconds:.2f} s ({size_mb / read_seconds:.0f} MB/s)")
    if tracers:
        print(f"\n!! {', '.join(tracers)} is attached to this process: the times below are NOT what the application takes.")
        print("!! Run this from a plain terminal (python utils/profile_analysis.py ...), not from the debugger.")
    print()
    print_steps(timer, total)
    print_inside(timer, total)
    print_repeats(timer)
    print_critical_path(timer)


def main() -> None:  # pylint: disable=too-many-locals
    parser = argparse.ArgumentParser(description="Where does the time of an analysis go?")
    parser.add_argument("apk", type=Path)
    parser.add_argument("--cprofile", action="store_true", help="also profile every function (slower)")
    parser.add_argument("--dex-in-process", action="store_true", help="analyze the DEX files in this process, as with "
                        f"{DEX_IN_PROCESS_VARIABLE}=1, to compare")
    arguments = parser.parse_args()
    if not arguments.apk.is_file():
        sys.exit(f"{arguments.apk} is not a file")

    tracers = find_tracers()  # before the profiler of --cprofile is on, which would show up as one
    read_seconds = time_reading(arguments.apk)  # before the analysis, so the disk is measured and not the cache of it

    timer = StepTimer()
    # one after the other: they add up to the use case
    timer.around(ApkLoader, "load", "open the APK (Androguard)")
    timer.around_guarded_steps()
    timer.around(PausedGarbageCollector, "__exit__", "gc.collect() when the analysis ends (PausedGarbageCollector)")
    timer.around(ZipArchiveReader, "list_entries", "list the files of the APK (Files tab)")
    timer.around(FileTreeBuilder, "build", "build the tree of files (Files tab)")
    # inside them
    timer.around(APK, "get_android_resources", "Androguard: get_android_resources (the first call builds the ARSCParser)", nested=True)
    timer.around(ARSCParser, "__init__", "Androguard: ARSCParser, parse of resources.arsc", nested=True)
    timer.around(ARSCParser, "_analyse", "Androguard: ARSCParser._analyse, index of every value (done on first use)", nested=True)
    timer.around(APK, "get_app_name", "Androguard: APK.get_app_name (resolves the label in the table)", nested=True)
    timer.around(ResourceReferenceResolver, "_read", "resource references of the manifest (ResourceReferenceResolver)",
                 nested=True, key=lambda _resolver, reference: reference)
    timer.around(DexAnalysisStarter, "start", "start of the DEX analysis (worker processes are started)", nested=True)
    timer.around(DexAnalyzer, "analyze", DEX_MERGE, nested=True)
    timer.around(DexReader, "read", "DEX: read every string and class name (DexReader)", nested=True)
    timer.around(DexMetricsExtractor, "extract", "DEX: scan every file here (DexMetricsExtractor.extract)", nested=True)
    timer.around(DexMetricsExtractor, "combine", "DEX: add the scans up (DexMetricsExtractor.combine)", nested=True)
    timer.around(EmbeddedContentExtractor, "extract", "DEX: embedded URLs (EmbeddedContentExtractor)", nested=True)
    timer.watch_dex_workers()

    parallel = not (arguments.dex_in_process or os.environ.get(DEX_IN_PROCESS_VARIABLE) == "1")
    inspector = AndroguardApkInspector(dex_analysis_starter=DexAnalysisStarter(parallel=parallel))
    use_case = AnalyzeApk(inspector, ZipArchiveReader())
    profiler = cProfile.Profile() if arguments.cprofile else None
    timer.begin()
    if profiler:
        profiler.enable()
    result = use_case.execute(str(arguments.apk))
    if profiler:
        profiler.disable()
    total = time.perf_counter() - timer.origin
    timer.stop_watching()

    print_report(arguments.apk, total, timer, read_seconds, tracers)
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
