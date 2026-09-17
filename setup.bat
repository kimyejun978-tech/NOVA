@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo [NOVA] Python launcher not found.
  echo Install Python 3.11-3.14 x64, then run this file again.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [NOVA] Creating virtual environment...
  py -3.11 -m venv .venv 2>nul
  if errorlevel 1 py -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo [NOVA] Package installation failed.
  pause
  exit /b 1
)

echo.
echo [NOVA] Setup complete.
echo Run run.bat to start.
pause
