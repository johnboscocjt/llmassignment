@echo off
setlocal
cd /d "%~dp0"

rem Free port 11434 if occupied, then run ollama in the current terminal
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -State Listen -LocalPort 11434 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"

echo Starting Ollama (foreground). Press Ctrl+C to stop.
ollama serve
