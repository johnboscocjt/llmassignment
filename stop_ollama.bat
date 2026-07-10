@echo off
setlocal
cd /d "%~dp0"

rem Kill Ollama app and any process listening on port 11434
taskkill /IM "ollama app.exe" /F /T >nul 2>nul
taskkill /IM ollama.exe /F /T >nul 2>nul

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -State Listen -LocalPort 11434 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"

echo Stopped Ollama and freed port 11434 (if any process was using it).
