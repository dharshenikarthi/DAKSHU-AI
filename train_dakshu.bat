@echo off
title DAKSHU AI - Train ^& Build Local Ollama Model
cd /d "%~dp0"
call "%~dp0finetune\create_dakshu_ollama.bat"

