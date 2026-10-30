"""
Shows where the time goes when the WINDOW loads an APK. profile_analysis.py only measures the use case
(AnalyzeApk); here the real application is started, the APK is loaded as `python main.py app.apk` does, and
everything is measured inside it:

    python utils/profile_ui.py path/to/app.apk
    python utils/profile_ui.py path/to/app.apk --no-loading-bar    # without the animated bar, to compare

It reports
- how long the analysis takes in its worker thread, in the window, and how long drawing each tab takes;
- what each thread was doing (sampled 10 times a second): the functions where the time goes, whatever they are;
- how long the Tk event loop took to answer (a long delay means the window was frozen).

Nothing in the application is changed: only stopwatches are put around some of its methods. The window closes by
itself when the analysis is shown.
"""

import argparse
import collections
import sys
import threading
import time
import os
from pathlib import Path
import __main__
__main__.__file__ = sys.argv[0]  # Engaña a los módulos que localizan el root usando el entry point

# --- FIX DEFINITIVO ---
root_dir = Path(__file__).resolve().parent.parent
os.chdir(root_dir)
sys.argv[0] = str(root_dir / "main.py")
sys.path[0] = str(root_dir)  # Sobrescribe 'utils' por la raíz del proyecto en el path de Python


#sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# pylint: disable=wrong-import-position,import-error
import ttkbootstrap as ttkb
import ttkbootstrap.localization

from apkdetective.composition_root import build_app

ttkbootstrap.localization.initialize_localities = bool  # as main.py does

SAMPLE_INTERVAL_S = 0.1
LAG_TICK_MS = 100
STALL_S = 0.5
PANELS = ("info_panel", "security_panel", "permissions_panel", "components_panel", "intents_panel",
          "manifest_panel", "files_panel")


class StackSampler(threading.Thread):
    """Looks, ten times a second, at the function every other thread is in, and counts."""

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self._stop_event = threading.Event()
        self.samples: collections.Counter[str] = collections.Counter()
        self.innermost: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
        self.in_app: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.wait(SAMPLE_INTERVAL_S):
            names = {thread.ident: thread.name for thread in threading.enumerate()}
            for ident, frame in sys._current_frames().items():  # pylint: disable=protected-access
                if ident == self.ident:
                    continue
                name = names.get(ident, str(ident))
                self.samples[name] += 1
                self.innermost[name][self._label(frame)] += 1
                app_frame = self._innermost_app_frame(frame)
                if app_frame is not None:
                    self.in_app[name][self._label(app_frame)] += 1

    @staticmethod
    def _label(frame) -> str:
        path = Path(frame.f_code.co_filename)
        parts = path.parts
        shown = "/".join(parts[parts.index("apkdetective"):]) if "apkdetective" in parts else \
            "/".join(parts[-2:])
        return f"{shown}:{frame.f_code.co_name}:{frame.f_lineno}"

    @staticmethod
    def _innermost_app_frame(frame):
        while frame is not None:
            if "apkdetective" in Path(frame.f_code.co_filename).parts:
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
        self.panel_seconds: dict[str, float] = {}

    def mark(self, name: str) -> None:
        self.marks[name] = time.perf_counter()

    def around(self, owner, method: str, label: str, store_as_panel: bool = False) -> None:
        original = getattr(owner, method)

        def timed(*args, **kwargs):
            started = time.perf_counter()
            try:
                return original(*args, **kwargs)
            finally:
                if store_as_panel:
                    self.panel_seconds[label] = self.panel_seconds.get(label, 0.0) + time.perf_counter() - started

        setattr(owner, method, timed)


def report(timeline: Timeline, sampler: StackSampler, lag: LoopLagMonitor) -> None:
    marks = timeline.marks
    since = marks["click"]
    print("\n=== Timeline (seconds since the click) ===")
    print(f"  analysis, in the worker thread : {marks['analysis_start'] - since:6.1f} -> {marks['analysis_end'] - since:6.1f}"
          f"   ({marks['analysis_end'] - marks['analysis_start']:.1f} s)")
    if "render_start" in marks:
        print(f"  waiting for the window to draw : {marks['analysis_end'] - since:6.1f} -> {marks['render_start'] - since:6.1f}"
              f"   ({marks['render_start'] - marks['analysis_end']:.1f} s)")
        print(f"  drawing the tabs (main thread) : {marks['render_start'] - since:6.1f} -> {marks['render_end'] - since:6.1f}"
              f"   ({marks['render_end'] - marks['render_start']:.1f} s)")
        for label, seconds in sorted(timeline.panel_seconds.items(), key=lambda item: -item[1]):
            print(f"        {seconds:6.2f} s  {label}")
    print(f"  window ready                   : {marks['ready'] - since:6.1f} s")

    worst = max(lag.delays, default=0.0)
    stalls = [delay for delay in lag.delays if delay > STALL_S]
    print("\n=== Tk event loop (asked to answer every 100 ms) ===")
    print(f"  worst delay: {worst:.2f} s | answers later than {STALL_S} s: {len(stalls)} | total delay: {sum(lag.delays):.1f} s")

    for name, count in sampler.samples.most_common():
        print(f"\n=== {name}: {count} samples ({count * SAMPLE_INTERVAL_S:.0f} s) ===")
        print("  inside the code of the application (where the time goes):")
        for label, hits in sampler.in_app[name].most_common(8):
            print(f"    {hits / count * 100:5.1f}%  {label}")
        print("  function it was executing at that moment:")
        for label, hits in sampler.innermost[name].most_common(8):
            print(f"    {hits / count * 100:5.1f}%  {label}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Where does the time of the window go?")
    parser.add_argument("apk", type=Path)
    parser.add_argument("--no-loading-bar", action="store_true", help="do not animate the progress bar")
    arguments = parser.parse_args()
    if not arguments.apk.is_file():
        sys.exit(f"{arguments.apk} is not a file")

    root: ttkb.App = ttkb.App()
    app = build_app(root)
    timeline = Timeline()
    lag = LoopLagMonitor(root)
    sampler = StackSampler()

    # pylint: disable=protected-access
    original_execute = app._analyze_apk.execute

    def execute(*args, **kwargs):
        timeline.mark("analysis_start")
        try:
            return original_execute(*args, **kwargs)
        finally:
            timeline.mark("analysis_end")

    app._analyze_apk.execute = execute  # type: ignore[method-assign]
    original_render = app._render_result

    def render(result):
        timeline.mark("render_start")
        try:
            original_render(result)
        finally:
            timeline.mark("render_end")

    app._render_result = render  # type: ignore[method-assign]
    for panel_name in PANELS:
        timeline.around(getattr(app, panel_name), "render", panel_name.replace("_panel", ""), store_as_panel=True)
    original_set_loading = app._set_loading

    def set_loading(loading: bool) -> None:
        original_set_loading(loading)
        if not loading:
            timeline.mark("ready")
            root.after(200, root.quit)

    app._set_loading = set_loading  # type: ignore[method-assign]
    if arguments.no_loading_bar:
        app.loading_bar.start = lambda: None  # type: ignore[method-assign]

    def go() -> None:
        timeline.mark("click")
        sampler.start()
        lag.start()
        app.start_analysis(str(arguments.apk))

    root.after(300, go)
    root.mainloop()
    sampler.stop()
    report(timeline, sampler, lag)


if __name__ == "__main__":
    main()
