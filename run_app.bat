@echo off
setlocal
cd /d "%~dp0"

if not exist "backend\.venv\Scripts\python.exe" (
  echo Backend virtual environment is missing. Create it and install backend\requirements.txt first.
  pause
  exit /b 1
)

if not exist "node_modules\.bin\vite.cmd" (
  echo Frontend dependencies are missing. Run npm.cmd install from this folder first.
  pause
  exit /b 1
)

start "CareerLens API - 127.0.0.1:8001" /D "%~dp0" cmd /k ""%~dp0backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --reload-dir backend\app --app-dir backend --host 127.0.0.1 --port 8001"
start "CareerLens Web - 127.0.0.1:5173" /D "%~dp0" cmd /k "npm.cmd run dev -- --host 127.0.0.1 --port 5173"
