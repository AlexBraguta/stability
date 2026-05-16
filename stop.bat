@echo off
REM Windows stopper - double-click to stop the dashboard.
cd /d "%~dp0"
where py >nul 2>&1 && (py stop.py) || (python stop.py)
pause
