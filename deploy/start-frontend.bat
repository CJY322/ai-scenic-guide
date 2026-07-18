@echo off
setlocal
chcp 65001 >nul

set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "WEB_DIR=%ROOT%\apps\visitor-web"
set "PORT_PID="

echo [AI Scenic Guide] Starting frontend...

where npm.cmd >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm.cmd was not found. Please install Node.js first.
  echo.
  pause
  exit /b 1
)

if not exist "%WEB_DIR%\node_modules" (
  echo [ERROR] Frontend dependencies not found:
  echo %WEB_DIR%\node_modules
  echo.
  echo Please install frontend dependencies first:
  echo cd /d "%WEB_DIR%"
  echo npm install
  echo.
  pause
  exit /b 1
)

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":5173 .*LISTENING"') do set "PORT_PID=%%P"
if defined PORT_PID (
  echo [INFO] Port 5173 is already in use. PID: %PORT_PID%
  echo Frontend may already be running:
  echo http://127.0.0.1:5173
  echo.
  pause
  exit /b 0
)

cd /d "%WEB_DIR%"
npm.cmd run dev -- --host 127.0.0.1 --port 5173

echo.
echo [INFO] Frontend stopped.
pause
