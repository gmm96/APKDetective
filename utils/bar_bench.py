"""
Does an animated progress bar slow down a thread that is busy doing Python work?

    python utils/bar_bench.py
    python utils/bar_bench.py --maximized      # with the window as big as the screen

It needs nothing of the application: a window with a ttkbootstrap progress bar (or without it) and a thread that only
adds numbers. For each way of showing the bar it measures how long the thread takes and how much CPU it uses (the
CPU time of a thread does not tick while it waits for the GIL or for a core). Each way runs in a process of its own,
three times, and the median is shown.

How to read it: if the animated bar costs nothing here but it does in the application, the cause is something of the
application (what runs when the window repaints). If it costs here too, the cause is the machine: the graphic
environment (X server, compositor, driver) or the CPU, and no change in the application will remove it.
"""

import argparse
import json
import statistics
import subprocess
import sys
import threading
import time

ITERATIONS = 40_000_000
ROUNDS = 3
START_DELAY_MS = 300
MODES = ("none", "static", "animated15", "animated100")


def run_child(mode: str, maximized: bool) -> None:
    import ttkbootstrap as ttkb  # pylint: disable=import-outside-toplevel,import-error

    root = ttkb.Window()
    if maximized:
        try:
            root.attributes("-zoomed", True)  # Linux
        except Exception:  # pylint: disable=broad-exception-caught
            root.state("zoomed")  # Windows
    if mode != "none":
        progress_bar = ttkb.Progressbar(root, mode="indeterminate", bootstyle="primary")
        progress_bar.pack(fill="x", padx=10, pady=10)
        if mode.startswith("animated"):
            progress_bar.start(int(mode.removeprefix("animated")))
    root.update()
    result: dict[str, float] = {}

    def work() -> None:
        started, cpu_started = time.perf_counter(), time.thread_time()
        total = 0
        for number in range(ITERATIONS):
            total += number * number
        result["wall"] = time.perf_counter() - started
        result["cpu"] = time.thread_time() - cpu_started
        root.after(0, root.quit)

    root.after(START_DELAY_MS, lambda: threading.Thread(target=work).start())
    root.mainloop()
    print(json.dumps(result))


def main() -> None:
    parser = argparse.ArgumentParser(description="Does an animated progress bar slow down a busy thread?")
    parser.add_argument("--maximized", action="store_true")
    parser.add_argument("--child", choices=MODES, help=argparse.SUPPRESS)
    arguments = parser.parse_args()
    if arguments.child:
        run_child(arguments.child, arguments.maximized)
        return

    measures: dict[str, list[dict[str, float]]] = {mode: [] for mode in MODES}
    for _ in range(ROUNDS):
        for mode in MODES:
            command = [sys.executable, __file__, "--child", mode] + (["--maximized"] if arguments.maximized else [])
            output = subprocess.run(command, capture_output=True, text=True, check=True).stdout
            measures[mode].append(json.loads(output.strip().splitlines()[-1]))
    print(f"\n{'mode':<14}{'wall (s)':>10}{'CPU of the thread (s)':>24}")
    for mode, runs in measures.items():
        wall = statistics.median(run["wall"] for run in runs)
        cpu = statistics.median(run["cpu"] for run in runs)
        print(f"{mode:<14}{wall:>10.2f}{cpu:>24.2f}")


if __name__ == "__main__":
    main()
