@echo off
title Web Services Generator - Launcher
chcp 65001 >nul

echo.
echo  ==========================================
echo    Web Services Generator - Launcher
echo  ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] 找不到 Python，請先安裝 Python 3.10+
    echo         下載網址：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [OK] Python %PY_VER%

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] 找不到 Node.js，請先安裝 Node.js 18+
    echo         下載網址：https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
echo  [OK] Node.js %NODE_VER%
echo.

:: ── Backend 相依套件偵測 ──────────────────────────────────────────
echo  [1/4] 檢查後端套件...
cd /d "%~dp0backend"

:: 偵測關鍵套件是否存在（fastapi + uvicorn 都在才算裝好）
pip show fastapi >nul 2>&1
set FASTAPI_MISSING=%errorlevel%
pip show uvicorn >nul 2>&1
set UVICORN_MISSING=%errorlevel%

if %FASTAPI_MISSING% neq 0 (
    set NEED_PIP=1
) else if %UVICORN_MISSING% neq 0 (
    set NEED_PIP=1
) else (
    set NEED_PIP=0
)

if %NEED_PIP% equ 1 (
    echo  [INFO] 偵測到後端套件尚未安裝，正在安裝中（首次約需 1-2 分鐘）...
    pip install -r requirements.txt -q --disable-pip-version-check
    if errorlevel 1 (
        echo  [ERROR] 後端套件安裝失敗，請確認 pip 與網路連線正常。
        pause
        exit /b 1
    )
    echo  [OK] 後端套件安裝完成
) else (
    echo  [OK] 後端套件已就緒，跳過安裝
)

:: ── Frontend 相依套件偵測 ─────────────────────────────────────────
echo  [2/4] 檢查前端套件...
cd /d "%~dp0frontend"

:: 偵測 node_modules 是否存在且含有 vite（避免空資料夾誤判）
if not exist "node_modules\vite" (
    echo  [INFO] 偵測到前端套件尚未安裝，正在安裝中（首次約需 1-2 分鐘）...
    call npm install
    if errorlevel 1 (
        echo  [ERROR] 前端套件安裝失敗，請確認 npm 與網路連線正常。
        pause
        exit /b 1
    )
    echo  [OK] 前端套件安裝完成
) else (
    echo  [OK] 前端套件已就緒，跳過安裝
)

echo.

:: Start backend in new window
echo  [3/4] 啟動後端（http://localhost:8000）...
start "WS-Generator Backend" "%~dp0_run_backend.bat"

timeout /t 4 /nobreak >nul

:: Start frontend in new window
echo  [4/4] 啟動前端（http://localhost:5173）...
start "WS-Generator Frontend" "%~dp0_run_frontend.bat"

timeout /t 5 /nobreak >nul

:: Open browser
echo.
echo  開啟瀏覽器...
start "" "http://localhost:5173"

echo.
echo  ==========================================
echo    啟動成功！
echo  ------------------------------------------
echo    前端介面 : http://localhost:5173
echo    後端 API : http://localhost:8000
echo    API 文件 : http://localhost:8000/docs
echo  ------------------------------------------
echo    執行 stop.bat 可停止所有服務
echo  ==========================================
echo.
echo  可以關閉此視窗，服務仍會在背景繼續執行。
echo.
pause
