@echo off
setlocal
chcp 65001 >nul

set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "API_DIR=%ROOT%\services\api-server"
set "PYTHON_EXE=%API_DIR%\.venv\Scripts\python.exe"
set "PORT_PID="

echo [AI Scenic Guide] Starting backend...

if not exist "%PYTHON_EXE%" (
  echo [ERROR] Python virtual environment not found:
  echo %PYTHON_EXE%
  echo.
  echo Please install backend dependencies first:
  echo cd /d "%API_DIR%"
  echo python -m venv .venv
  echo .venv\Scripts\python.exe -m pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do set "PORT_PID=%%P"
if defined PORT_PID (
  echo [INFO] Port 8000 is already in use. PID: %PORT_PID%
  echo Backend may already be running:
  echo http://127.0.0.1:8000/api/v1/health
  echo.
  pause
  exit /b 0
)

cd /d "%API_DIR%"
"%PYTHON_EXE%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo.
echo [INFO] Backend stopped.
pause
