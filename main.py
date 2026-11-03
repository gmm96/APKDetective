"""
Entry point for the APKDetective desktop application.

Usage:
    python main.py [path/to/app.apk]
"""

import multiprocessing
import sys


def main() -> None:
    """Entry point for the APKDetective project"""
    # Imported here and not at the top of the file: the process that analyzes the code of an APK (see
    # DexAnalysisStarter) starts by importing this module, and it has no use for a window toolkit.
    import ttkbootstrap as ttkb  # pylint: disable=import-outside-toplevel
    import ttkbootstrap.localization  # pylint: disable=import-outside-toplevel

    from apkdetective.composition_root import build_app  # pylint: disable=import-outside-toplevel

    # Bypass ttkbootstrap localization to prevent Nuitka msgcat packaging errors on UNIX
    ttkbootstrap.localization.initialize_localities = bool

    root: ttkb.App = ttkb.App()
    app = build_app(root)

    if len(sys.argv) > 1:
        root.after(100, lambda: app.start_analysis(sys.argv[1]))

    root.mainloop()


if __name__ == "__main__":
    multiprocessing.freeze_support()  # needed by the executables built for Windows
    main()
