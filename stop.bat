@echo off
chcp 65001 >nul
title Web Services Generator - 停止服務

echo.
echo  ==========================================
echo    Web Services Generator - 停止服務
echo  ==========================================
echo.

set FOUND=0

:: ── 關閉後端視窗 ─────────────────────────────────────────────
taskkill /fi "WINDOWTITLE eq WS-Generator Backend" /f >nul 2>&1
if not errorlevel 1 (
    echo  [OK] 後端服務已停止
    set FOUND=1
)

:: ── 關閉前端視窗 ─────────────────────────────────────────────
taskkill /fi "WINDOWTITLE eq WS-Generator Frontend" /f >nul 2>&1
if not errorlevel 1 (
    echo  [OK] 前端服務已停止
    set FOUND=1
)

:: ── 結束殘留的 uvicorn 行程 ──────────────────────────────────
tasklist /fi "imagename eq uvicorn.exe" 2>nul | find "uvicorn.exe" >nul
if not errorlevel 1 (
    taskkill /im uvicorn.exe /f >nul 2>&1
    echo  [OK] uvicorn 行程已終止
    set FOUND=1
)

:: ── 結束佔用 port 5173 的行程 ────────────────────────────────
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":5173 "') do (
    if not "%%p"=="0" (
        taskkill /pid %%p /f >nul 2>&1
        echo  [OK] Port 5173 行程 (PID %%p) 已終止
        set FOUND=1
    )
)

echo.
if "%FOUND%"=="1" (
    echo  所有服務已停止。
) else (
    echo  找不到正在執行的服務。
)
echo.
pause
