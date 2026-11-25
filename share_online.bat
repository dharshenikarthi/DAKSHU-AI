@echo off
title DAKSHU AI - Instant Public Sharing Link
color 0b
cd /d "%~dp0"

echo ======================================================
echo   DAKSHU AI: Instant Public Sharing (Zero API Key)
echo ======================================================
echo.
echo [*] This will generate a secure public HTTPS link
echo     so your friends, phone, or classmates can access
echo     DAKSHU AI and your local Ollama model from anywhere!
echo.
echo [*] Make sure your backend is running on port 8000
echo     (or double-click to start).
echo.
echo [*] Launching public tunnel via localtunnel...
echo.

npx localtunnel --port 8000 --subdomain dakshu-ai

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Subdomain in use, launching with randomized public link...
    npx localtunnel --port 8000
)

pause

