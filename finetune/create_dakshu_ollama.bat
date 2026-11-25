@echo off
title DAKSHU AI - Local Model Compiler
echo ======================================================
echo   DAKSHU AI: Local Model Setup ^& Ollama Compiler
echo ======================================================

set "OLLAMA_EXE=ollama"
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    if exist "%LOCALAPPDATA%\Programs\Ollama\ollama.exe" (
        set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
    ) else (
        echo.
        echo [!] Ollama is not installed on your computer yet.
        echo     Ollama is the local AI engine that runs the model on your laptop.
        echo.
        echo Opening the official download page for you...
        start https://ollama.com/download/OllamaSetup.exe
        echo.
        echo Please:
        echo 1. Run the downloaded "OllamaSetup.exe" to install Ollama.
        echo 2. Once installed, double-click this script again!
        echo.
        pause
        exit /b
    )
)

echo.
echo [1/2] Pulling Google Gemma 2 2B base model (approx 1.6 GB)...
"%OLLAMA_EXE%" pull gemma2:2b

echo.
echo [2/2] Compiling fine-tuned Dakshu model from Modelfile...
"%OLLAMA_EXE%" create dakshu -f "%~dp0Modelfile"

echo.
echo ======================================================
echo   [✓] Dakshu local model created successfully!
echo ======================================================
echo You can test it anytime in terminal with: ollama run dakshu
pause
