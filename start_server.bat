@echo off
title DAKSHU AI - Local Web Server
color 0a
cd /d "%~dp0"

echo ======================================================
echo   DAKSHU AI: Starting Local Server
echo ======================================================
echo.
echo [*] Local web app will be available at: http://127.0.0.1:8000
echo [*] Powered by Local Ollama Model (Dakshu)
echo.

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
if %ERRORLEVEL% NEQ 0 (
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
)

pause

