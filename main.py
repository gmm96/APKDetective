"""
Entry point for the APKViewer desktop application.

Usage:
    python main.py [path/to/app.apk]
"""

import sys
import ttkbootstrap as ttkb

from apkviewer.composition_root import build_app


def main() -> None:
    """Entry point for the APKViewer project"""
    root: ttkb.App = ttkb.App()
    app = build_app(root)

    if len(sys.argv) > 1:
        root.after(100, lambda: app.start_analysis(sys.argv[1]))

    root.mainloop()


if __name__ == "__main__":
    main()
