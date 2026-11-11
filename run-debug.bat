@echo off
rem Runs Jarvis with a console window so you can see logs and errors.
cd /d "%~dp0"
".venv\Scripts\python.exe" "%~dp0run_jarvis.py"
pause
