"""Launch the NSS portal locally and open its home page in a browser."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
LOCAL_PACKAGES = PROJECT_DIR / ".local_packages"
PORTAL_URL = "http://127.0.0.1:5000/"


def ensure_flask() -> None:
    """Use an existing Flask install, or install requirements locally."""
    if LOCAL_PACKAGES.exists():
        sys.path.insert(0, str(LOCAL_PACKAGES))

    try:
        import flask  # noqa: F401
    except ModuleNotFoundError:
        print("Flask is not installed yet. Installing the project requirement...")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--target",
                str(LOCAL_PACKAGES),
                "-r",
                str(PROJECT_DIR / "requirements.txt"),
            ],
            check=True,
            cwd=PROJECT_DIR,
        )
        sys.path.insert(0, str(LOCAL_PACKAGES))

        import flask  # noqa: F401


def main() -> None:
    os.chdir(PROJECT_DIR)
    ensure_flask()

    from app import app

    print(f"NSS Event & Camp Management Portal is starting at {PORTAL_URL}")
    print("Keep this window open while you use the portal. Press Ctrl+C to stop it.")
    threading.Timer(1.5, webbrowser.open_new_tab, args=(PORTAL_URL,)).start()
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
