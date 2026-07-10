# Error Handling — Task 7 Evidence

**IS 365 | University of Dar es Salaam | June 2026**

How our UDSM Student Support LLM handles the error situations required by the assignment.

---

## Required situations and expected behaviour

| Situation | Expected behaviour | Layer | HTTP code (if API) |
|-----------|-------------------|-------|-------------------|
| Backend is not running | Frontend shows **connection error** | Frontend | — |
| Model is not running | Backend returns **clear error** | Backend | **503** |
| Empty question | Frontend asks user to **enter a question** | Frontend (+ API) | **422** (API only) |
| Slow response | Frontend shows **loading / spinner** (or streaming) | Frontend | — |

---

## 1. Backend is not running

### Expected behaviour

The Streamlit app cannot reach FastAPI. The user sees a red error message — not a crash.

**Message shown:**

> Cannot connect to backend. Is FastAPI running on port 8000?

### Where in code

`frontend/app.py` catches `requests.exceptions.ConnectionError` when `POST /ask` or stream fails.

### How to demonstrate

1. **Stop** the backend (`uvicorn`) — leave Streamlit running
2. Open `http://localhost:8501`
3. Type any question and submit

![Connection error when FastAPI is not running](screenshots/13-error-handling.png)

---

## 2. Model is not running

### Expected behaviour

FastAPI is up but Ollama is stopped or `llama3.2:1b` is not pulled. The API returns **HTTP 503** with a JSON `detail` explaining that the local LLM is not available.

**Example response:**

```json
{
  "detail": "Local LLM is not running. Start Ollama and pull llama3.2:1b."
}
```

### Where in code

- `backend/llm_client.py` — raises `ModelNotRunningError` on connection failure
- `backend/main.py` — catches it and returns `HTTPException(status_code=503, ...)`

```122:124:backend/main.py
    except ModelNotRunningError as exc:
        logger.error("Model not running: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
```

### How to demonstrate

1. Keep backend running; **quit Ollama** (or stop `ollama serve`)
2. Open `http://127.0.0.1:8000/docs`
3. Try **POST /ask** with a sample question — response is **503**

```powershell
curl -X POST http://127.0.0.1:8000/ask ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"Test?\",\"use_rag\":true}"
```

---

## 3. Empty question

### Expected behaviour

**Frontend:** If the user submits only whitespace, Streamlit shows:

> Please enter a question.

**Backend:** If an empty string is sent to the API, Pydantic validation returns **HTTP 422 Unprocessable Entity**.

### Where in code

- Frontend: `st.warning("Please enter a question.")` when `question.strip()` is empty
- Backend: `AskRequest` with `question: str = Field(..., min_length=1)`

### How to demonstrate

1. Open Streamlit
2. Try to submit a blank message (or spaces only)

**Automated test:** `pytest tests/test_api.py::test_ask_empty_question_returns_422`

---

## 4. Slow response

### Expected behaviour

Local CPU inference can take **30–90 seconds**. The user should see feedback that the system is working — not a frozen screen.

**Non-streaming message:**

> Thinking... this may take up to 60 seconds on local CPU

**Streaming:** tokens appear gradually via `st.write_stream()` when **Stream response** is enabled in the sidebar.

### Where in code

- `st.spinner(...)` around blocking `requests.post` to `/ask`
- `st.write_stream()` when streaming is on
- Backend: `REQUEST_TIMEOUT = 120` in `backend/config.py`; timeout → HTTP **504**

### How to demonstrate

1. Ensure Ollama and backend are running
2. Ask a UDSM question (e.g. library hours)
3. Screenshot the **spinner** visible before the answer appears, or enable streaming:

![Streaming response while the model generates tokens](screenshots/15-streaming-demo.png)

---

## Additional errors

| Situation | Behaviour | Code |
|-----------|-----------|------|
| Request exceeds 120 s | HTTP **504** timeout | `ModelTimeoutError` in `main.py` |
| Invalid history role | HTTP **422** | Pydantic `ChatMessage` pattern |
| Frontend request timeout | Error message in chat | `requests.exceptions.Timeout` in `frontend/app.py` |

---

## Logging evidence

`backend/logs/app.log` records questions, Ollama requests, and generated answers.

![app.log showing logged questions and responses](screenshots/14-log-file.png)

---

## Related documents

- [learning_outcomes.md](learning_outcomes.md) — Outcome 7
- [submit_report.md](submit_report.md) — Section 10
- [testing.md](testing.md) — Automated tests
- [architecture.md](architecture.md) — API endpoints
- [README.md](README.md) — Full docs index
