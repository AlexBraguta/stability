"""Cross-platform stopper for the Token Stability dashboard.

Reads `.streamlit_pid` (written by launch.py) and terminates the
Streamlit server together with its child worker, on Windows, macOS or
Linux. Run it directly:

    python stop.py          (or: py stop.py)

or use the thin wrappers: stop.bat (Windows) / stop.sh (macOS/Linux).
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PID_FILE = ROOT / ".streamlit_pid"
IS_WINDOWS = os.name == "nt"


def main():
    if not PID_FILE.exists():
        print("No .streamlit_pid file - the server does not appear to be running.")
        return 0

    try:
        pid = int(PID_FILE.read_text().strip())
    except ValueError:
        print("Could not read PID file; removing it.")
        PID_FILE.unlink(missing_ok=True)
        return 1

    print(f"Stopping Streamlit (PID {pid}) and its child processes...")
    if IS_WINDOWS:
        # /T kills the whole tree, /F forces it.
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
        )
    else:
        try:
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGTERM)
            time.sleep(2)
            if _alive(pid):
                os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            print("Process already gone.")

    PID_FILE.unlink(missing_ok=True)
    print("Stopped.")
    return 0


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


if __name__ == "__main__":
    sys.exit(main())
