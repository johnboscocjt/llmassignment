# Start / Stop Instructions

## Quick Start (Simplest Way)

Just use these simple batch scripts:

| What you want | Command |
|---------------|---------|
| Start Ollama | `.\start_ollama.bat` |
| Stop Ollama | `.\stop_ollama.bat` |
| Start everything | `.\run_all.bat` |
| Stop everything | `.\stop_all.bat` |

---

## Detailed Instructions (Optional)

### Start the app manually

| Terminal | Command | URL |
|----------|---------|-----|
| 1 — Ollama | `ollama serve` | port 11434 |
| 2 — Backend | `.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000` | http://127.0.0.1:8000/docs |
| 3 — Frontend | `.\.venv\Scripts\streamlit.exe run frontend/app.py` | http://localhost:8501 |

Run these in separate terminals if you want to start them manually.
These commands work directly in PowerShell. If you prefer shorter commands, activate the venv first with `.\.venv\Scripts\Activate.ps1` and then run `uvicorn` or `streamlit`.

## Free port 11434 (only if needed)

If `ollama serve` fails with "port already in use", first try:

```powershell
.\stop_ollama.bat
```

---

## Advanced / Manual Instructions (Optional)

### Stop processes manually

#### Stop it in the terminal that started it
Click the terminal window and press `Ctrl+C`.

#### If you don't have that terminal open anymore
Use the batch scripts: `.\stop_ollama.bat` or `.\stop_all.bat`

#### Check if processes are stopped

```powershell
# Check one service
Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue

# Check all services
Get-NetTCPConnection -State Listen -LocalPort 8000,8501,11434 -ErrorAction SilentlyContinue
```

If nothing is returned, the service(s) are stopped.
