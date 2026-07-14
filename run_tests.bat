@echo off
REM Run all API tests
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m pytest tests/ -v
pause
