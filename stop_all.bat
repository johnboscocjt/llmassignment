@echo off
setlocal
cd /d "%~dp0"

taskkill /IM "ollama app.exe" /F /T >nul 2>nul
taskkill /IM ollama.exe /F /T >nul 2>nul

rem Stop any process listening on project ports (8000, 8501, 11434)
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -State Listen -LocalPort 8000,8501,11434 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force }"

echo Stopped backend, frontend, and Ollama (if running) and freed ports 8000, 8501, 11434.