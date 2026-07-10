import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)
FEEDBACK_FILE = Path(__file__).resolve().parent.parent / "data" / "feedback.jsonl"


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model" in data
    assert "ollama_reachable" in data


def test_ask_empty_question_returns_422():
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 422


def test_ask_oversized_question_returns_422():
    response = client.post("/ask", json={"question": "x" * 2001})
    assert response.status_code == 422


def test_ask_question_at_limit_accepted_by_validation(monkeypatch):
    monkeypatch.setattr("backend.main.ask_llm", lambda **kwargs: "ok")
    response = client.post("/ask", json={"question": "x" * 2000})
    assert response.status_code == 200


def test_ask_oversized_history_returns_422():
    response = client.post(
        "/ask",
        json={
            "question": "hi",
            "history": [{"role": "user", "content": "m"}] * 41,
        },
    )
    assert response.status_code == 422


def test_feedback_oversized_answer_returns_422():
    response = client.post(
        "/feedback",
        json={"question": "q", "answer": "x" * 8001, "rating": "Good"},
    )
    assert response.status_code == 422


def test_feedback_empty_question_returns_422():
    response = client.post(
        "/feedback",
        json={"question": "", "answer": "a", "rating": "Good"},
    )
    assert response.status_code == 422


def test_prompts_endpoint():
    response = client.get("/prompts")
    assert response.status_code == 200
    data = response.json()
    assert "original" in data
    assert "improved" in data
    assert "UDSM" in data["improved"]


def test_feedback_saved(tmp_path, monkeypatch):
    feedback_path = tmp_path / "feedback.jsonl"
    monkeypatch.setattr("backend.main.FEEDBACK_FILE", feedback_path)

    response = client.post(
        "/feedback",
        json={
            "question": "Test question?",
            "answer": "Test answer.",
            "rating": "Good",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "saved"
    assert feedback_path.exists()
    line = feedback_path.read_text(encoding="utf-8").strip()
    entry = json.loads(line)
    assert entry["rating"] == "Good"


def test_feedback_summary(tmp_path, monkeypatch):
    feedback_path = tmp_path / "feedback.jsonl"
    feedback_path.write_text(
        '{"rating": "Good"}\n{"rating": "Poor"}\n{"rating": "Average"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("backend.main.FEEDBACK_FILE", feedback_path)

    response = client.get("/feedback/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["Good"] == 1
    assert data["Average"] == 1
    assert data["Poor"] == 1


def test_ask_invalid_history_role_returns_422():
    response = client.post(
        "/ask",
        json={
            "question": "Hello",
            "history": [{"role": "system", "content": "not allowed"}],
        },
    )
    assert response.status_code == 422


def test_trim_history_caps_turns():
    from backend.llm_client import trim_history

    history = [{"role": "user", "content": f"msg {i}"} for i in range(10)]
    trimmed = trim_history(history)
    assert len(trimmed) == 6


@pytest.mark.skipif(
    not __import__("backend.llm_client", fromlist=["check_ollama"]).check_ollama(),
    reason="Ollama/model not running",
)
def test_ask_valid_question():
    response = client.post(
        "/ask",
        json={
            "question": "How do I register for courses at UDSM?",
            "use_rag": True,
            "prompt_version": "improved",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["question"]
    assert data["answer"]
    assert data["used_rag"] is True
    assert "history_used" in data


@pytest.mark.skipif(
    not __import__("backend.llm_client", fromlist=["check_ollama"]).check_ollama(),
    reason="Ollama/model not running",
)
def test_ask_with_history():
    response = client.post(
        "/ask",
        json={
            "question": "And what about fees?",
            "use_rag": True,
            "prompt_version": "improved",
            "history": [
                {"role": "user", "content": "How do I register at UDSM?"},
                {"role": "assistant", "content": "Use the ARIS student portal."},
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["history_used"] is True
    assert data["answer"]


@pytest.mark.skipif(
    not __import__("backend.llm_client", fromlist=["check_ollama"]).check_ollama(),
    reason="Ollama/model not running",
)
def test_stream_endpoint():
    response = client.post(
        "/ask/stream",
        json={
            "question": "What are UDSM library hours?",
            "use_rag": True,
            "prompt_version": "improved",
        },
    )
    assert response.status_code == 200
    body = response.text
    assert "data:" in body
