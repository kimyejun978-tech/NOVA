@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q NOVA.spec 2>nul
del /q NOVAUpdater.spec 2>nul

echo [1/3] Building standalone updater...
pyinstaller --noconfirm --clean --onefile --windowed --name NOVAUpdater nova_updater.py
if errorlevel 1 goto :fail

echo [2/3] Building NOVA...
pyinstaller --noconfirm --clean --windowed --name NOVA --collect-all sklearn --collect-all yfinance main.py
if errorlevel 1 goto :fail

copy /y "dist\NOVAUpdater.exe" "dist\NOVA\NOVAUpdater.exe" >nul

echo [3/3] Build complete.
echo EXE folder: %CD%\dist\NOVA\
echo GitHub Actions can package releases automatically.
pause
exit /b 0

:fail
echo Build failed.
pause
exit /b 1
