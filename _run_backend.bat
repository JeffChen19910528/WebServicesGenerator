@echo off
title WS-Generator Backend
cd /d "%~dp0backend"
echo [Backend] Starting on http://localhost:8000 ...
uvicorn main:app --reload --port 8000
pause
