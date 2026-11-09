"""
Shows where the time goes when the WINDOW loads an APK. profile_analysis.py only measures the use case
(AnalyzeApk); here the real application is started, the APK is loaded as `python main.py app.apk` does, and
everything is measured inside it:

    python utils/profile_ui.py path/to/app.apk
    python utils/profile_ui.py path/to/app.apk --no-loading-bar    # without the progress bar, to compare
    python utils/profile_ui.py path/to/app.apk --static-loading-bar  # the bar is shown but does not move
    python utils/profile_ui.py path/to/app.apk --dex-in-process    # no worker processes, to compare
    python utils/profile_ui.py path/to/app.apk --no-sampler        # only the timeline: no sampling, no lag monitor

It reports
- how long the analysis takes in its worker thread (and how much of it is the final garbage collection), in the
  window, and how long drawing each tab takes (every tab of the window is found by itself: a new tab is measured
  without touching this file);
- what each thread was doing (sampled 10 times a second): the functions where it was busy, whatever they are, and
  where it was waiting (sleeping, on a lock or idle in the Tk event loop);
- how long the Tk event loop took to answer (a long delay means the window was frozen).

The code of the DEX files is scanned in other processes, which this sampler cannot see: while they work, the analysis
thread shows as waiting in ParallelDexAnalysisJob._wait_for_scans. profile_analysis.py says when each of them finished.

Nothing in the application is changed: only stopwatches are put around some of its methods (the ones inside the
Files tab are called about 100,000 times, so they add 0.1-0.2 s to it: compare them with each other). The window closes by
itself when the analysis is shown. Run it from a plain terminal, not from the debugger: debugpy made the same APK take
four times longer, and it also follows the worker processes.
"""

# pylint: disable=duplicate-code  # standalone script: it shares no module with profile_analysis.py on purpose
import argparse
import collections
import gc
import linecache
import os
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any
import __main__

ROOT_DIR = Path(__file__).resolve().parent.parent
MAIN_SCRIPT = str(ROOT_DIR / "main.py")
os.chdir(ROOT_DIR)
sys.argv[0] = MAIN_SCRIPT
# Modules that look for the entry point of the program find main.py, and so do the worker processes that scan the DEX
# files: they are started with "spawn" and begin by importing the main module of the program. In the application that
# is main.py, which imports almost nothing; this file imports the whole window, which would make them start later here.
__main__.__file__ = MAIN_SCRIPT
sys.path[0] = str(ROOT_DIR)  # replaces utils/ with the project root

# pylint: disable=wrong-import-position,import-error
import ttkbootstrap as ttkb
import ttkbootstrap.localization

from apkdetective.composition_root import build_app
from apkdetective.infrastructure.androguard.paused_garbage_collector import PausedGarbageCollector

ttkbootstrap.localization.initialize_localities = bool  # as main.py does

DEX_IN_PROCESS_VARIABLE = "APKDETECTIVE_DEX_IN_PROCESS"  # the same switch composition_root.py reads
SAMPLE_INTERVAL_S = 0.1
LAG_TICK_MS = 100
STALL_S = 0.5
TOP_FUNCTIONS = 8
SLOW_COLLECTION_S = 0.01
# What the line a thread is on says when the thread is waiting (a C function such as time.sleep has no frame of its
# own: the frame seen is the one that called it).
WAIT_MARKS = ("wait", "sleep(", "select(", "mainloop(", "acquire(", ".join(", "recv(", "poll(")
ANALYSIS = "analysis"   # groups of the stopwatches of the Timeline
DRAWING = "drawing"
INSIDE = "inside"       # calls made inside the drawing: shown, never added up


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


def tracer_warning(tracers: list[str]) -> str:
    return (f"!! {', '.join(tracers)} is attached to this process: the times are NOT what the application takes.\n"
            "!! Run this from a plain terminal (python utils/profile_ui.py ...), not from the debugger.")


class CollectionRecorder:
    """Records every pass of the cyclic garbage collector: thread, generation, objects freed and seconds."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, int, int, float, int]] = []  # + the objects it had to look at
        self._started = 0.0
        self._tracked = 0

    def __call__(self, phase: str, info: dict[str, int]) -> None:
        if phase == "start":
            # counting the objects takes a while: it is done before the clock starts and only for the full passes
            self._tracked = len(gc.get_objects()) if info["generation"] == 2 else 0
            self._started = time.perf_counter()
        else:
            self.rows.append((threading.current_thread().name, info["generation"], info["collected"],
                              time.perf_counter() - self._started, self._tracked))

    def install(self) -> None:
        gc.callbacks.append(self)

    def print_slow(self) -> None:
        slow = [row for row in self.rows if row[3] >= SLOW_COLLECTION_S]
        print(f"\n=== Garbage collections slower than {SLOW_COLLECTION_S * 1000:.0f} ms "
              f"({len(self.rows)} in total) ===")
        for thread, generation, freed, seconds, tracked in slow:
            print(f"  {seconds:6.2f} s  generation {generation}, {freed:,} objects freed out of {tracked:,} tracked, in {thread}")
        if not slow:
            print("  none")


class StackSampler(threading.Thread):
    """Looks, ten times a second, at the function every other thread is in, and counts: busy or waiting."""

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self._stop_event = threading.Event()
        self._app_prefix = os.path.normcase(str(ROOT_DIR / "apkdetective")) + os.sep
        self.samples: collections.Counter[str] = collections.Counter()
        self.waiting: collections.Counter[str] = collections.Counter()
        self.waiting_at: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
        self.innermost: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
        self.in_app: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.wait(SAMPLE_INTERVAL_S):
            self._sample_once()  # in its own method: the frames it looks at must not outlive the sample

    def _sample_once(self) -> None:
        """A frame keeps every local variable of its function alive: holding on to one of the analysis thread would
        keep the whole APK in memory (1.5 million objects) and make the garbage collector slower, so nothing of the
        frames is kept once the sample is taken."""
        main_ident = threading.main_thread().ident
        names = {thread.ident: thread.name for thread in threading.enumerate()}
        for ident, frame in sys._current_frames().items():  # pylint: disable=protected-access
            if ident == self.ident:
                continue
            name = names.get(ident, str(ident))
            self.samples[name] += 1
            if self._is_waiting(frame, ident == main_ident):
                self.waiting[name] += 1
                self.waiting_at[name][self._label(frame)] += 1
                continue
            self.innermost[name][self._label(frame)] += 1
            app_frame = self._innermost_app_frame(frame)
            if app_frame is not None:
                self.in_app[name][self._label(app_frame)] += 1

    @staticmethod
    def _is_waiting(frame, in_main_thread: bool) -> bool:
        if frame.f_lineno is None:  # a frame that is not running a line right now
            return False
        if f"{os.sep}multiprocessing{os.sep}" in frame.f_code.co_filename:  # its threads only block on pipes and queues
            return True
        line = linecache.getline(frame.f_code.co_filename, frame.f_lineno).lower()
        # a call into Tk from another thread (root.after) blocks until the main thread, if it is busy, answers
        return any(mark in line for mark in WAIT_MARKS) or (not in_main_thread and ".after(" in line)

    def _in_app(self, filename: str) -> bool:
        return os.path.normcase(filename).startswith(self._app_prefix)

    def _label(self, frame) -> str:
        filename = frame.f_code.co_filename
        shown = os.path.relpath(filename, ROOT_DIR) if self._in_app(filename) else "/".join(Path(filename).parts[-2:])
        return f"{shown}:{frame.f_code.co_name}:{frame.f_lineno or 0}"

    def _innermost_app_frame(self, frame):
        while frame is not None:
            if self._in_app(frame.f_code.co_filename):
                return frame
            frame = frame.f_back
        return None


class LoopLagMonitor:  # pylint: disable=too-few-public-methods
    """Asks Tk to run something every 100 ms and records how late it was: the window is frozen meanwhile."""

    def __init__(self, root: ttkb.App) -> None:
        self._root = root
        self.delays: list[float] = []
        self._expected = 0.0

    def start(self) -> None:
        self._expected = time.perf_counter() + LAG_TICK_MS / 1000
        self._root.after(LAG_TICK_MS, self._tick)

    def _tick(self) -> None:
        now = time.perf_counter()
        self.delays.append(max(0.0, now - self._expected))
        self._expected = now + LAG_TICK_MS / 1000
        self._root.after(LAG_TICK_MS, self._tick)


class Timeline:
    def __init__(self) -> None:
        self.marks: dict[str, float] = {}
        self.analysis_cpu: float | None = None  # seconds the analysis thread was really running on a CPU
        self.main_thread_collection: float | None = None  # a full gc.collect() made in the main thread at the end
        self.durations: dict[str, dict[str, float]] = collections.defaultdict(lambda: collections.defaultdict(float))
        self.calls: dict[str, dict[str, int]] = collections.defaultdict(lambda: collections.defaultdict(int))

    def mark(self, name: str) -> None:
        self.marks[name] = time.perf_counter()

    def around(self, owner, method: str, label: str, group: str) -> None:
        """Times every call of `owner.method` (an object or a class) and adds it up under `label` in `group`."""
        try:
            original = getattr(owner, method)
        except AttributeError:
            print(f"(cannot time {label}: {method} does not exist any more)", file=sys.stderr)
            return

        def timed(*args, **kwargs):
            started = time.perf_counter()
            try:
                return original(*args, **kwargs)
            finally:
                self.durations[group][label] += time.perf_counter() - started
                self.calls[group][label] += 1

        setattr(owner, method, timed)


def print_timeline(timeline: Timeline) -> None:
    marks = timeline.marks
    since = marks["click"]
    print("\n=== Timeline (seconds since the click) ===")
    print(f"  analysis, in the worker thread : {marks['analysis_start'] - since:6.1f} -> {marks['analysis_end'] - since:6.1f}"
          f"   ({marks['analysis_end'] - marks['analysis_start']:.1f} s)")
    if timeline.analysis_cpu is not None:
        wall = marks["analysis_end"] - marks["analysis_start"]
        print(f"        {timeline.analysis_cpu:6.2f} s  of those it was running on a CPU; the other {wall - timeline.analysis_cpu:.2f} s "
              f"it was not (waiting for the GIL or for a core)")
    for label, seconds in timeline.durations[ANALYSIS].items():
        print(f"        {seconds:6.2f} s  of which {label}")
    if "render_start" in marks:
        drawing = marks["render_end"] - marks["render_start"]
        print(f"  waiting for the window to draw : {marks['analysis_end'] - since:6.1f} -> {marks['render_start'] - since:6.1f}"
              f"   ({marks['render_start'] - marks['analysis_end']:.1f} s)")
        print(f"  drawing the tabs (main thread) : {marks['render_start'] - since:6.1f} -> {marks['render_end'] - since:6.1f}"
              f"   ({drawing:.1f} s)")
        parts = dict(timeline.durations[DRAWING])
        parts["(the rest of _render_result)"] = max(0.0, drawing - sum(parts.values()))
        for label, seconds in sorted(parts.items(), key=lambda item: -item[1]):
            print(f"        {seconds:6.2f} s  {label}")
        for label, seconds in sorted(timeline.durations[INSIDE].items(), key=lambda item: -item[1]):
            calls = timeline.calls[INSIDE][label]
            print(f"        {seconds:6.2f} s  inside the above: {label}: {calls} calls, {seconds / calls * 1e6:.0f} us each")
    print(f"  window ready                   : {marks['ready'] - since:6.1f} s")
    if timeline.main_thread_collection is not None:
        print(f"  a full gc.collect() made afterwards in the main thread, with nothing left to free: "
              f"{timeline.main_thread_collection:.2f} s")


def print_lag(lag: LoopLagMonitor) -> None:
    worst = max(lag.delays, default=0.0)
    stalls = [delay for delay in lag.delays if delay > STALL_S]
    print("\n=== Tk event loop (asked to answer every 100 ms) ===")
    print(f"  worst delay: {worst:.2f} s | answers later than {STALL_S} s: {len(stalls)} | total delay: {sum(lag.delays):.1f} s")


def print_threads(sampler: StackSampler) -> None:
    quiet = []
    for name, count in sampler.samples.most_common():
        waiting = sampler.waiting[name]
        busy = count - waiting
        if not busy:
            quiet.append(name)
            continue
        print(f"\n=== {name}: busy {busy * SAMPLE_INTERVAL_S:.0f} s, waiting {waiting * SAMPLE_INTERVAL_S:.0f} s "
              f"(of {count * SAMPLE_INTERVAL_S:.0f} s) ===")
        print("  busy, inside the code of the application (where the time goes):")
        print_top(sampler.in_app[name], busy)
        print("  busy, in the function it was executing at that moment:")
        print_top(sampler.innermost[name], busy)
        if waiting:
            print("  waiting at:")
            print_top(sampler.waiting_at[name], waiting, 3)
    if quiet:
        print(f"\n(threads that only waited: {', '.join(quiet)})")


def print_top(counter: collections.Counter[str], total: int, how_many: int = TOP_FUNCTIONS) -> None:
    for label, hits in counter.most_common(how_many):
        print(f"    {hits / total * 100:5.1f}%  {label}")


def report(timeline: Timeline, sampler: StackSampler | None, lag: LoopLagMonitor | None,
           collections_: CollectionRecorder, tracers: list[str]) -> None:
    if tracers:
        print(f"\n{tracer_warning(tracers)}")
    print(f"\nDEX analysis: {dex_mode()}")
    print_timeline(timeline)
    if lag is not None:
        print_lag(lag)
    collections_.print_slow()
    if sampler is not None:
        print_threads(sampler)


def dex_mode() -> str:
    if os.environ.get(DEX_IN_PROCESS_VARIABLE) == "1":
        return f"in this process ({DEX_IN_PROCESS_VARIABLE}=1)"
    return f"in worker processes when there are 2 CPUs or more ({os.cpu_count()} here)"


def files_hot_spots(panel) -> list[tuple[object, str, str]]:
    """What FilesPanel does for every row and every folder: which part of its Python side weighs."""
    spots: list[tuple[object, str, str]] = [
        (panel, "_insert", "files: _insert, the whole row (it contains the Tcl call, the icon, the date and the sizes)"),
        (panel, "_format_modified", "files: date of the row (strftime)"),
        (panel, "_fit_height", "files: _fit_height"),
        (panel, "_after_rebuild", "files: _after_rebuild (counter)"),
        (panel, "_apply_column_layout", "files: _apply_column_layout"),
    ]
    for attribute, method, label in (
        ("_size_formatter", "format", "files: size formatter (two calls per row)"),
        ("_file_icons", "icon_for", "files: icon of the row"),
        ("_sorter", "sorted_children", "files: sorting the children of a folder"),
    ):
        owner = getattr(panel, attribute, None)
        if owner is not None:
            spots.append((owner, method, label))
    return spots


def drawable_panels(app) -> dict[str, Callable]:
    """Every tab of the window: an attribute called *_panel that has a render method."""
    return {name.removesuffix("_panel"): panel for name, panel in vars(app).items()
            if name.endswith("_panel") and callable(getattr(panel, "render", None))}


def main() -> None:  # pylint: disable=too-many-locals,too-many-statements
    parser = argparse.ArgumentParser(description="Where does the time of the window go?")
    parser.add_argument("apk", type=Path)
    parser.add_argument("--no-sampler", action="store_true",
                        help="do not sample the threads nor watch the Tk event loop: only the timeline is measured")
    loading_bar = parser.add_mutually_exclusive_group()
    loading_bar.add_argument("--no-loading-bar", action="store_true", help="do not show the progress bar")
    loading_bar.add_argument("--static-loading-bar", action="store_true",
                     help="show the progress bar but do not animate it: tells whether the cost is the animation or the bar")
    parser.add_argument("--dex-in-process", action="store_true",
                        help=f"analyze the DEX files in this process, as with {DEX_IN_PROCESS_VARIABLE}=1, to compare")
    arguments = parser.parse_args()
    if not arguments.apk.is_file():
        sys.exit(f"{arguments.apk} is not a file")
    if arguments.dex_in_process:
        os.environ[DEX_IN_PROCESS_VARIABLE] = "1"  # read by build_app
    tracers = find_tracers()
    if tracers:
        print(tracer_warning(tracers), file=sys.stderr)

    root: ttkb.App = ttkb.App()
    app = build_app(root)
    timeline = Timeline()
    lag = None if arguments.no_sampler else LoopLagMonitor(root)
    sampler = None if arguments.no_sampler else StackSampler()
    collections_ = CollectionRecorder()

    # pylint: disable=protected-access
    original_execute = app._analyze_apk.execute

    def execute(*args, **kwargs):
        timeline.mark("analysis_start")
        cpu_started = time.thread_time()  # of this thread only: it does not tick while the thread waits
        try:
            return original_execute(*args, **kwargs)
        finally:
            timeline.mark("analysis_end")
            timeline.analysis_cpu = time.thread_time() - cpu_started

    app._analyze_apk.execute = execute  # type: ignore[method-assign]
    original_render = app._render_result

    def render(result):
        timeline.mark("render_start")
        try:
            original_render(result)
        finally:
            timeline.mark("render_end")

    app._render_result = render  # type: ignore[method-assign]
    timeline.around(PausedGarbageCollector, "__exit__", "the final gc.collect() (PausedGarbageCollector)", ANALYSIS)
    timeline.around(app.header, "show_result", "header (show_result)", DRAWING)
    timeline.around(app, "_show_warnings", "warnings of the tabs (_show_warnings)", DRAWING)
    panels = drawable_panels(app)
    for name, panel in panels.items():
        timeline.around(panel, "render", name, DRAWING)
        if hasattr(panel, "tree"):
            timeline.around(panel.tree, "insert", f"{name}: Treeview.insert (the call into Tcl)", INSIDE)
    if "files" in panels:
        for owner, method, label in files_hot_spots(panels["files"]):
            timeline.around(owner, method, label, INSIDE)
    original_set_loading = app._set_loading

    def set_loading(loading: bool) -> None:
        original_set_loading(loading)
        if not loading:
            timeline.mark("ready")
            root.after(200, probe_main_thread_collection)

    def probe_main_thread_collection() -> None:
        """What a full collection costs in the main thread when there is nothing left to free: the price of the heap."""
        started = time.perf_counter()
        gc.collect()
        timeline.main_thread_collection = time.perf_counter() - started
        root.after(100, root.quit)

    app._set_loading = set_loading  # type: ignore[method-assign]
    if arguments.no_loading_bar:
        app.loading_bar.start = lambda: None  # type: ignore[method-assign]
    elif arguments.static_loading_bar:
        app.loading_bar._bar.start = lambda *args, **kwargs: None  # type: ignore[method-assign]

    def go() -> None:
        timeline.mark("click")
        collections_.install()
        if sampler is not None and lag is not None:
            sampler.start()
            lag.start()
        app.start_analysis(str(arguments.apk))

    root.after(300, go)
    root.mainloop()
    if sampler is not None:
        sampler.stop()
    report(timeline, sampler, lag, collections_, tracers)


if __name__ == "__main__":
    main()
