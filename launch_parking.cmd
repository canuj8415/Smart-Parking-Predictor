@echo off
setlocal
cd /d "%~dp0"
if defined SMART_PARKING_PYTHON (
  "%SMART_PARKING_PYTHON%" run_app.py
) else if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" run_app.py
) else if exist "..\.venv\Scripts\python.exe" (
  "..\.venv\Scripts\python.exe" run_app.py
) else (
  python run_app.py
)
if errorlevel 1 pause
