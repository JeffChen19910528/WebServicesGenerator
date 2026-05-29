@echo off
title Web Services Generator - Launcher

echo.
echo  ==========================================
echo    Web Services Generator - Launcher
echo  ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo         Please install Python 3.10+: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [OK] Python %PY_VER%

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Node.js not found.
    echo         Please install Node.js 18+: https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
echo  [OK] Node.js %NODE_VER%
echo.

:: Install backend packages
echo  [1/4] Installing backend packages...
cd /d "%~dp0backend"
pip install -r requirements.txt -q --disable-pip-version-check
if errorlevel 1 (
    echo  [ERROR] Backend package installation failed.
    pause
    exit /b 1
)
echo  [OK] Backend packages ready

:: Install frontend packages
echo  [2/4] Installing frontend packages...
cd /d "%~dp0frontend"
call npm install >nul 2>&1
echo  [OK] Frontend packages ready
echo.

:: Start backend in new window
echo  [3/4] Starting backend (http://localhost:8000)...
start "WS-Generator Backend" "%~dp0_run_backend.bat"

timeout /t 4 /nobreak >nul

:: Start frontend in new window
echo  [4/4] Starting frontend (http://localhost:5173)...
start "WS-Generator Frontend" "%~dp0_run_frontend.bat"

timeout /t 5 /nobreak >nul

:: Open browser
echo.
echo  Opening browser...
start "" "http://localhost:5173"

echo.
echo  ==========================================
echo    Project started successfully!
echo  ------------------------------------------
echo    Frontend : http://localhost:5173
echo    Backend  : http://localhost:8000
echo    API Docs : http://localhost:8000/docs
echo  ------------------------------------------
echo    Run stop.bat to stop all services
echo  ==========================================
echo.
echo  You can close this window. Services will keep running.
echo.
pause
