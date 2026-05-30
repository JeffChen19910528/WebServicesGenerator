@echo off
title WS-Generator Backend
cd /d "%~dp0backend"
call uvicorn main:app --reload --port 8000
exit 0
