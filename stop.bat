@echo off
title Web Services Generator - Stop

echo.
echo  ==========================================
echo    Web Services Generator - Stop Services
echo  ==========================================
echo.

:: Stop backend window
taskkill /fi "WINDOWTITLE eq WS-Generator Backend" /f >nul 2>&1
if not errorlevel 1 echo  [OK] Backend stopped

:: Stop frontend window
taskkill /fi "WINDOWTITLE eq WS-Generator Frontend" /f >nul 2>&1
if not errorlevel 1 echo  [OK] Frontend stopped

:: Kill leftover uvicorn process
taskkill /im uvicorn.exe /f >nul 2>&1
if not errorlevel 1 echo  [OK] uvicorn process terminated

:: Kill process on port 5173
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":5173 "') do (
    if not "%%p"=="0" (
        taskkill /pid %%p /f >nul 2>&1
        echo  [OK] Port 5173 process terminated
    )
)

echo.
echo  Done. All services stopped.
echo.
pause
