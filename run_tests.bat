@echo off
REM Run all API tests
cd /d "%~dp0"
call .venv\Scripts\activate.bat
pytest tests/ -v
pause
