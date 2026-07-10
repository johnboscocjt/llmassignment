@echo off
setlocal
cd /d "%~dp0"

call .venv\Scripts\activate.bat

rem If port 11434 is in use, try to free it by stopping the owning process (useful if a previous Ollama instance hung)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = Get-NetTCPConnection -State Listen -LocalPort 11434 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; if ($p) { Write-Output \"Port 11434 in use by PID: $p - attempting to stop process\"; Stop-Process -Id $p -Force -ErrorAction SilentlyContinue }; Start-Sleep -Seconds 1"

start "Ollama" cmd /k "ollama serve"

powershell -NoProfile -ExecutionPolicy Bypass -Command "for ($i = 0; $i -lt 30; $i++) { if (Get-NetTCPConnection -State Listen -LocalPort 11434 -ErrorAction SilentlyContinue) { exit 0 }; Start-Sleep -Seconds 1 }; exit 1"
if errorlevel 1 (
    echo Ollama did not start on port 11434.
    exit /b 1
)

start "Backend" cmd /k "call .venv\Scripts\activate.bat && uvicorn backend.main:app --host 127.0.0.1 --port 8000"
start "Frontend" cmd /k "call .venv\Scripts\activate.bat && streamlit run frontend/app.py"

echo Started Ollama, backend, and frontend in separate windows.