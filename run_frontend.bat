@echo off
REM UDSM Student Support LLM - run frontend
cd /d "%~dp0"
call .venv\Scripts\activate.bat
streamlit run frontend/app.py
