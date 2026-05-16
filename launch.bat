@echo off
REM Windows launcher - double-click to start the dashboard.
cd /d "%~dp0"
where py >nul 2>&1 && (py launch.py) || (python launch.py)
pause
