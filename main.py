"""
Entry point for the APKDetective desktop application.

Usage:
    python main.py [path/to/app.apk]
"""

import sys
import ttkbootstrap as ttkb
import ttkbootstrap.localization

from apkdetective.composition_root import build_app

# Bypass ttkbootstrap localization to prevent Nuitka msgcat packaging errors on UNIX
ttkbootstrap.localization.initialize_localities = bool


def main() -> None:
    """Entry point for the APKDetective project"""
    root: ttkb.App = ttkb.App()
    app = build_app(root)

    if len(sys.argv) > 1:
        root.after(100, lambda: app.start_analysis(sys.argv[1]))

    root.mainloop()


if __name__ == "__main__":
    main()
