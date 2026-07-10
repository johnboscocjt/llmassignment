# Screenshot Evidence — UDSM Student Support LLM

**IS 365 | University of Dar es Salaam | June 2026**

Charles J Tungaraza, Stella Thomas Kahungo, Godbless Kaaya, Baraka Jimmy Maengesho, Frank Elikana Wallace, Kelvin George Msuya

This document shows all **16 screenshots** captured during setup, testing, and demonstration of our local LLM chatbot. Each image is embedded with a short explanation of what it proves.

PNG files are stored in `docs/screenshots/`.

---

## 01 — Virtual environment activated

Python virtual environment (`.venv`) is active before installing project packages.

![01 — Virtual environment activated](screenshots/01-venv-activated.png)

---

## 02 — Dependencies installed

`pip install -r requirements.txt` completed successfully (FastAPI, Streamlit, httpx, pytest, and related packages).

![02 — pip install success](screenshots/02-pip-install.png)

---

## 03 — Ollama model pulled

`llama3.2:1b` appears in `ollama list` after download — the local model used for answers.

![03 — ollama pull llama3.2:1b](screenshots/03-ollama-pull.png)

---

## 04 — Ollama test run

Direct terminal test confirms Ollama generates text from the model before the API is used.

![04 — ollama run test response](screenshots/04-ollama-run.png)

---

## 05 — FastAPI backend running

Uvicorn serves the FastAPI app on `http://127.0.0.1:8000`.

![05 — uvicorn running on port 8000](screenshots/05-fastapi-running.png)

---

## 06 — Swagger API documentation

Interactive OpenAPI docs at `/docs` for testing `/health`, `/ask`, and other endpoints.

![06 — Swagger UI](screenshots/06-swagger-docs.png)

---

## 07 — Health check response

`GET /health` returns JSON with `status: ok` and `ollama_reachable: true` when backend and Ollama are up.

![07 — GET /health JSON](screenshots/07-health-response.png)

---

## 08 — POST /ask response

Swagger shows a successful `POST /ask` with a UDSM registration answer in the response body.

![08 — POST /ask 200 response](screenshots/08-ask-response.png)

---

## 09 — Streamlit chat home

Streamlit UI loaded with chat area and sidebar options (RAG, history, streaming, prompt version).

![09 — Streamlit frontend home](screenshots/09-frontend-home.png)

---

## 10 — Completed question and answer

Student asks about GePG fees; answer appears in chat with Good / Average / Poor rating buttons.

![10 — Frontend Q&A with ratings](screenshots/10-frontend-qa.png)

---

## 11 — pytest results

Automated API tests: `pytest tests/ -v` — **10 passed**.

![11 — pytest 10 passed](screenshots/11-pytest-results.png)

---

## 12 — Prompt comparison (Task 6)

Same hostel question with **original** vs **improved** UDSM prompt; improved + RAG gives a specific FAQ-based answer.

![12 — Original vs improved prompt](screenshots/12-prompt-comparison.png)

---

## 13 — Error handling (Task 7)

Streamlit shows a clear connection error when the FastAPI backend is not reachable.

![13 — Backend connection error](screenshots/13-error-handling.png)

---

## 14 — Application log file

`backend/logs/app.log` records the question, Ollama request, and generated answer lines.

![14 — app.log sample](screenshots/14-log-file.png)

---

## 15 — Streaming response (Bonus D)

Answer tokens appear gradually in Streamlit when **Stream response** is enabled in the sidebar.

![15 — Streaming demo](screenshots/15-streaming-demo.png)

---

## 16 — Conversation history (Bonus A)

Two-turn chat: registration question followed by a follow-up; history is sent to the API.

![16 — Multi-turn chat history](screenshots/16-chat-history.png)

---

## Summary

| # | Topic |
|---|--------|
| 01–02 | Development environment |
| 03–04 | Local LLM (Ollama) |
| 05–08 | FastAPI backend and API tests |
| 09–10 | Streamlit frontend and end-to-end Q&A |
| 11 | Automated pytest |
| 12 | Task 6 — prompt comparison |
| 13–14 | Task 7 — errors and logging |
| 15–16 | Bonus — streaming and chat history |

---

## Related documents

| Document | Use |
|----------|-----|
| [README.md](README.md) | Full docs index |
| [learning_outcomes.md](learning_outcomes.md) | Outcome mapping with screenshots |
| [testing.md](testing.md) | Screenshots 05–08, 11 |
| [error_handling.md](error_handling.md) | Screenshots 13–15 |
| [prompt_comparison.md](prompt_comparison.md) | Screenshot 12 |
| [bonuses.md](bonuses.md) | Screenshots 15–16 |
| [submit_report.md](submit_report.md) | Section 9.3 — verification table |
