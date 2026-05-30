@echo off
title Web Services Generator - Stop

echo.
echo  ==========================================
echo    Web Services Generator - Stop Services
echo  ==========================================
echo.

:: ── Backend: kill by port 8000 (uvicorn server + reloader parent) ─────
set BACKEND_KILLED=0
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    if not "%%p"=="0" (
        for /f "tokens=2 delims==" %%q in ('wmic process where "ProcessId=%%p" get ParentProcessId /value 2^>nul ^| findstr "ParentProcessId"') do (
            taskkill /pid %%q /t /f >nul 2>&1
        )
        taskkill /pid %%p /t /f >nul 2>&1
        set BACKEND_KILLED=1
    )
)
if %BACKEND_KILLED%==1 (
    echo  [OK] Backend stopped
) else (
    echo  [--] Backend was not running
)

:: ── Frontend: kill by port 5173 (vite + children) ──────────────────────
set FRONTEND_KILLED=0
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":5173 " ^| findstr "LISTENING"') do (
    if not "%%p"=="0" (
        taskkill /pid %%p /t /f >nul 2>&1
        set FRONTEND_KILLED=1
    )
)
if %FRONTEND_KILLED%==1 (
    echo  [OK] Frontend stopped
) else (
    echo  [--] Frontend was not running
)

echo.
echo  All services stopped. This window will close in 3 seconds...
echo.
timeout /t 3 /nobreak >nul
