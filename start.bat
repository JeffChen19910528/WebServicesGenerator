@echo off
chcp 65001 >nul
title Web Services Generator

:: 預先展開路徑，避免 start 指令內巢狀引號問題
set "ROOT=%~dp0"
set "BACKEND=%~dp0backend"
set "FRONTEND=%~dp0frontend"

echo.
echo  ==========================================
echo    Web Services Generator - 啟動器
echo  ==========================================
echo.

:: ── 檢查 Python ──────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [錯誤] 找不到 Python，請先安裝 Python 3.10 以上版本
    echo         下載：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [OK] Python %PY_VER% 已安裝

:: ── 檢查 Node.js ─────────────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    echo  [錯誤] 找不到 Node.js，請先安裝 Node.js 18 以上版本
    echo         下載：https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
echo  [OK] Node.js %NODE_VER% 已安裝
echo.

:: ── 安裝後端套件 ─────────────────────────────────────────────
echo  [1/4] 檢查後端套件...
cd /d "%BACKEND%"
pip install -r requirements.txt -q --disable-pip-version-check
if errorlevel 1 (
    echo  [錯誤] 後端套件安裝失敗，請確認網路連線後重試
    pause
    exit /b 1
)
echo  [OK] 後端套件已就緒

:: ── 安裝前端套件 ─────────────────────────────────────────────
echo  [2/4] 檢查前端套件...
cd /d "%FRONTEND%"
call npm install --silent 2>nul
if errorlevel 1 (
    echo  [錯誤] 前端套件安裝失敗，請確認網路連線後重試
    pause
    exit /b 1
)
echo  [OK] 前端套件已就緒
echo.

:: ── 啟動後端 ─────────────────────────────────────────────────
echo  [3/4] 啟動後端服務 (http://localhost:8000)...
start "WS-Generator Backend" cmd /k "cd /d %BACKEND% && uvicorn main:app --reload --port 8000"

:: 等待後端初始化
timeout /t 4 /nobreak >nul

:: ── 啟動前端 ─────────────────────────────────────────────────
echo  [4/4] 啟動前端服務 (http://localhost:5173)...
start "WS-Generator Frontend" cmd /k "cd /d %FRONTEND% && npm run dev"

:: 等待前端初始化
timeout /t 4 /nobreak >nul

:: ── 開啟瀏覽器 ───────────────────────────────────────────────
echo.
echo  開啟瀏覽器...
start "" "http://localhost:5173"

:: ── 完成提示 ─────────────────────────────────────────────────
echo.
echo  ==========================================
echo    專案已成功啟動！
echo  ------------------------------------------
echo    前端介面：http://localhost:5173
echo    後端 API： http://localhost:8000
echo    API 文件： http://localhost:8000/docs
echo  ------------------------------------------
echo    執行 stop.bat 可停止所有服務
echo  ==========================================
echo.
echo  此視窗可直接關閉，服務將在背景繼續運行
echo.
pause
