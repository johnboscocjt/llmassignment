import json
from collections.abc import Iterator
from typing import Any

import httpx

from backend.config import (
    MAX_HISTORY_TURNS,
    MODEL_NAME,
    OLLAMA_BASE_URL,
    OLLAMA_OPTIONS,
    PROMPTS,
    REQUEST_TIMEOUT,
)


class ModelNotRunningError(Exception):
    pass


class ModelTimeoutError(Exception):
    pass


class ModelResponseError(Exception):
    pass


def check_ollama() -> bool:
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            return any(MODEL_NAME in name for name in models)
    except (httpx.HTTPError, httpx.ConnectError):
        return False


def trim_history(history: list[dict[str, str]] | None) -> list[dict[str, str]]:
    if not history:
        return []

    max_messages = MAX_HISTORY_TURNS * 2
    trimmed: list[dict[str, str]] = []
    for item in history[-max_messages:]:
        role = item.get("role", "")
        content = (item.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            trimmed.append({"role": role, "content": content})
    return trimmed


def build_messages(
    question: str,
    context: str = "",
    prompt_version: str = "improved",
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    system_prompt = PROMPTS.get(prompt_version, PROMPTS["improved"])

    user_content = question
    if context:
        user_content = f"FAQ Context:\n{context}\n\nStudent Question:\n{question}"
    elif prompt_version == "improved":
        # The improved prompt branches on whether FAQ context exists, so an
        # empty retrieval must be visible to the model, not just omitted.
        user_content = f"FAQ Context:\n(no relevant FAQ entries found)\n\nStudent Question:\n{question}"

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    messages.extend(trim_history(history))
    messages.append({"role": "user", "content": user_content})
    return messages


def _chat_payload(messages: list[dict[str, str]], stream: bool) -> dict[str, Any]:
    return {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": stream,
        "options": OLLAMA_OPTIONS,
    }


def ask_llm(
    question: str,
    context: str = "",
    prompt_version: str = "improved",
    history: list[dict[str, str]] | None = None,
) -> str:
    messages = build_messages(question, context, prompt_version, history)
    payload = _chat_payload(messages, stream=False)

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            if data.get("error"):
                raise ModelResponseError(f"The model returned an error: {data['error']}")
            answer = data.get("message", {}).get("content", "").strip()
            if not answer:
                raise ModelResponseError("The model returned an empty answer. Try again.")
            return answer
    except httpx.ConnectError as exc:
        raise ModelNotRunningError(
            f"Local LLM is not running. Start Ollama and pull {MODEL_NAME}."
        ) from exc
    except httpx.TimeoutException as exc:
        raise ModelTimeoutError(
            "The model took too long to respond. Try a shorter question or wait and retry."
        ) from exc
    except httpx.HTTPError as exc:
        raise ModelNotRunningError(
            f"Could not reach Ollama at {OLLAMA_BASE_URL}. Error: {exc}"
        ) from exc


def ask_llm_stream(
    question: str,
    context: str = "",
    prompt_version: str = "improved",
    history: list[dict[str, str]] | None = None,
) -> Iterator[str]:
    messages = build_messages(question, context, prompt_version, history)
    payload = _chat_payload(messages, stream=True)

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            with client.stream(
                "POST", f"{OLLAMA_BASE_URL}/api/chat", json=payload
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    if data.get("error"):
                        raise ModelResponseError(f"The model returned an error: {data['error']}")
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
                    if data.get("done"):
                        break
    except httpx.ConnectError as exc:
        raise ModelNotRunningError(
            f"Local LLM is not running. Start Ollama and pull {MODEL_NAME}."
        ) from exc
    except httpx.TimeoutException as exc:
        raise ModelTimeoutError(
            "The model took too long to respond. Try a shorter question or wait and retry."
        ) from exc
    except httpx.HTTPError as exc:
        raise ModelNotRunningError(
            f"Could not reach Ollama at {OLLAMA_BASE_URL}. Error: {exc}"
        ) from exc
