import json
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.config import (
    CORS_ALLOWED_ORIGINS,
    FEEDBACK_FILE,
    LOG_DIR,
    LOG_FILE,
    MAX_ANSWER_CHARS,
    MAX_HISTORY_MESSAGES,
    MAX_QUESTION_CHARS,
    MODEL_NAME,
    PROMPTS,
)
from backend.llm_client import (
    ModelNotRunningError,
    ModelResponseError,
    ModelTimeoutError,
    ask_llm,
    ask_llm_stream,
    check_ollama,
    trim_history,
)
from backend.rag import retrieve_context

LOG_DIR.mkdir(parents=True, exist_ok=True)
FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("udsm_assistant")

app = FastAPI(
    title="UDSM Student Support Assistant API",
    description="IS 365 - Self-hosted LLM backend for University of Dar es Salaam",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=MAX_ANSWER_CHARS)


class AskRequest(BaseModel):
    question: str = Field(
        ..., min_length=1, max_length=MAX_QUESTION_CHARS, description="Student question"
    )
    use_rag: bool = True
    prompt_version: str = "improved"
    history: list[ChatMessage] = Field(
        default_factory=list, max_length=MAX_HISTORY_MESSAGES
    )


class AskResponse(BaseModel):
    question: str
    answer: str
    prompt_version: str
    used_rag: bool
    context_used: bool
    history_used: bool
    timestamp: str


class FeedbackRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=MAX_QUESTION_CHARS)
    answer: str = Field(..., min_length=1, max_length=MAX_ANSWER_CHARS)
    rating: str = Field(..., pattern="^(Good|Average|Poor)$")


def _prepare_ask(payload: AskRequest) -> tuple[str, str, list[dict[str, str]]]:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question cannot be empty.")

    context = ""
    if payload.use_rag:
        context = retrieve_context(question)

    history = trim_history([m.model_dump() for m in payload.history])
    return question, context, history


@app.get("/health")
def health_check():
    ollama_ok = check_ollama()
    return {
        "status": "ok" if ollama_ok else "degraded",
        "model": MODEL_NAME,
        "ollama_reachable": ollama_ok,
        "message": "Backend is running" if ollama_ok else "Backend running but Ollama/model not available",
    }


@app.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest):
    question, context, history = _prepare_ask(payload)

    logger.info(
        "Received question: %s | RAG=%s | prompt=%s | history_msgs=%d",
        question,
        payload.use_rag,
        payload.prompt_version,
        len(history),
    )

    try:
        answer = ask_llm(
            question=question,
            context=context,
            prompt_version=payload.prompt_version,
            history=history,
        )
    except ModelNotRunningError as exc:
        logger.error("Model not running: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ModelTimeoutError as exc:
        logger.error("Model timeout: %s", exc)
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except ModelResponseError as exc:
        logger.error("Model response error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during /ask")
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}") from exc

    timestamp = datetime.now(timezone.utc).isoformat()
    logger.info("Generated answer for '%s': %s", question, answer[:200])

    return AskResponse(
        question=question,
        answer=answer,
        prompt_version=payload.prompt_version,
        used_rag=payload.use_rag,
        context_used=bool(context),
        history_used=bool(history),
        timestamp=timestamp,
    )


@app.post("/ask/stream")
def ask_question_stream(payload: AskRequest):
    question, context, history = _prepare_ask(payload)

    logger.info(
        "Stream question: %s | RAG=%s | prompt=%s | history_msgs=%d",
        question,
        payload.use_rag,
        payload.prompt_version,
        len(history),
    )

    def event_stream():
        try:
            for chunk in ask_llm_stream(
                question=question,
                context=context,
                prompt_version=payload.prompt_version,
                history=history,
            ):
                yield f"data: {json.dumps({'token': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except ModelNotRunningError as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        except ModelTimeoutError as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        except ModelResponseError as exc:
            logger.error("Model response error during stream: %s", exc)
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        except Exception as exc:
            logger.exception("Unexpected error during /ask/stream")
            yield f"data: {json.dumps({'error': f'Internal server error: {exc}'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/feedback")
def submit_feedback(payload: FeedbackRequest):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": payload.question,
        "answer": payload.answer,
        "rating": payload.rating,
    }
    with Path(FEEDBACK_FILE).open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.info("Feedback saved: %s for question '%s'", payload.rating, payload.question[:80])
    return {"status": "saved", "rating": payload.rating}


@app.get("/feedback/summary")
def feedback_summary():
    counts: Counter[str] = Counter()
    if Path(FEEDBACK_FILE).exists():
        with Path(FEEDBACK_FILE).open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    rating = entry.get("rating", "")
                    if rating in ("Good", "Average", "Poor"):
                        counts[rating] += 1
                except json.JSONDecodeError:
                    continue

    good = counts["Good"]
    average = counts["Average"]
    poor = counts["Poor"]
    return {
        "total": good + average + poor,
        "Good": good,
        "Average": average,
        "Poor": poor,
    }


@app.get("/prompts")
def get_prompts():
    return {
        "original": PROMPTS["original"],
        "improved": PROMPTS["improved"],
    }
