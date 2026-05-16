#!/usr/bin/env bash
# macOS / Linux stopper - run: ./stop.sh
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
    exec python3 stop.py
else
    exec python stop.py
fi
