@echo off
title WS-Generator Frontend
cd /d "%~dp0frontend"
echo [Frontend] Starting on http://localhost:5173 ...
npm run dev
pause
