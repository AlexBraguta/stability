"""Cross-platform launcher for the Token Stability dashboard.

Detects the OS, installs dependencies, starts the Streamlit server
(which opens the browser automatically) and records the process id in
`.streamlit_pid` so `stop.py` can shut it down later.

Works on Windows, macOS and Linux. Run it directly:

    python launch.py        (or: py launch.py)

or use the thin wrappers: launch.bat (Windows) / launch.sh (macOS/Linux).
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PID_FILE = ROOT / ".streamlit_pid"
IS_WINDOWS = os.name == "nt"


def _pid_alive(pid):
    try:
        if IS_WINDOWS:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True,
            )
            return str(pid) in out.stdout
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def main():
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
        except ValueError:
            old_pid = None
        if old_pid and _pid_alive(old_pid):
            print(f"Server already running (PID {old_pid}). Run stop first.")
            return 1
        PID_FILE.unlink(missing_ok=True)

    print("Installing / checking dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
        cwd=ROOT, check=True,
    )

    print("Starting Streamlit dashboard (a browser tab will open)...")
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
    if IS_WINDOWS:
        proc = subprocess.Popen(
            cmd, cwd=ROOT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    else:
        # New session => its own process group, so stop.py can kill the
        # whole tree (streamlit spawns a worker child).
        proc = subprocess.Popen(cmd, cwd=ROOT, start_new_session=True)

    PID_FILE.write_text(str(proc.pid))
    print(f"Dashboard started (PID {proc.pid}).")
    print("Run stop.py (or stop.bat / stop.sh) to shut it down.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
