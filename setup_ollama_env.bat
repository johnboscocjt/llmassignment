@echo off
REM Set low-memory Ollama environment variables (User level)
setx OLLAMA_NUM_PARALLEL "1"
setx OLLAMA_MAX_LOADED_MODELS "1"
setx OLLAMA_KEEP_ALIVE "5m"
echo.
echo Ollama low-memory variables set. Restart your terminal before using Ollama.
pause
