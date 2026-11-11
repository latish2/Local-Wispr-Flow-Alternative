@echo off
rem Builds a standalone dist\Jarvis\Jarvis.exe (no Python needed on the target machine).
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt || exit /b 1

set "GPU_ARGS="
".venv\Scripts\python.exe" -c "import nvidia.cublas, nvidia.cudnn" >nul 2>nul
if %errorlevel%==0 set "GPU_ARGS=--collect-binaries nvidia.cublas --collect-binaries nvidia.cudnn"

".venv\Scripts\pyinstaller.exe" --noconfirm --windowed --name Jarvis --icon assets\jarvis.ico ^
  --add-data "assets;assets" --collect-all faster_whisper --collect-binaries ctranslate2 %GPU_ARGS% ^
  run_jarvis.py || exit /b 1
echo Built dist\Jarvis\Jarvis.exe
