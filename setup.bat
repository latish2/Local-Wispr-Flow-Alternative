@echo off
setlocal
cd /d "%~dp0"

rem Prefer Python 3.12; newer versions may lack wheels for some dependencies.
set "PY=python"
py -3.12 --version >nul 2>nul
if %errorlevel%==0 (
  set "PY=py -3.12"
) else (
  py -3 --version >nul 2>nul
  if not errorlevel 1 set "PY=py -3"
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  %PY% -m venv .venv || goto :fail
)

".venv\Scripts\python.exe" -m pip install --upgrade pip || goto :fail
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :fail

where nvidia-smi >nul 2>nul
if %errorlevel%==0 (
  echo NVIDIA GPU detected - installing CUDA runtime libraries for GPU speed...
  ".venv\Scripts\python.exe" -m pip install -r requirements-gpu.txt || echo GPU libraries failed to install; Jarvis will fall back to CPU.
)

echo.
echo Setup complete. Double-click run.bat to start Jarvis.
exit /b 0

:fail
echo.
echo Setup failed. Make sure Python 3.10-3.12 is installed from python.org (tick "Add to PATH").
exit /b 1
