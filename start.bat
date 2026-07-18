@echo off
setlocal
chcp 65001 >nul

set "ROOT=%~dp0"
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "SCRIPT_DIR=%ROOT%\deploy"

echo [AI Scenic Guide] One-click startup
echo Project: %ROOT%
echo.

if not exist "%SCRIPT_DIR%\start-backend.bat" (
  echo [ERROR] Missing script: %SCRIPT_DIR%\start-backend.bat
  pause
  exit /b 1
)

if not exist "%SCRIPT_DIR%\start-frontend.bat" (
  echo [ERROR] Missing script: %SCRIPT_DIR%\start-frontend.bat
  pause
  exit /b 1
)

echo [1/3] Opening backend window...
start "AI Scenic Guide API" cmd /k call "%SCRIPT_DIR%\start-backend.bat"

echo [2/3] Waiting for backend startup...
timeout /t 4 /nobreak >nul

echo [3/3] Opening frontend window...
start "AI Scenic Guide Web" cmd /k call "%SCRIPT_DIR%\start-frontend.bat"

echo Opening browser shortly...
timeout /t 6 /nobreak >nul
start "" "http://127.0.0.1:5173"
start "" "http://127.0.0.1:5173/admin"

echo.
echo Startup commands have been sent.
echo Visitor app: http://127.0.0.1:5173
echo Admin panel: http://127.0.0.1:5173/admin
echo Backend health: http://127.0.0.1:8000/api/v1/health
echo.
echo Keep the backend and frontend command windows open while using the system.
pause
