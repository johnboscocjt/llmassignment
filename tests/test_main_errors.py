import pytest
from fastapi.testclient import TestClient

from backend.llm_client import ModelNotRunningError, ModelResponseError, ModelTimeoutError
from backend.main import app

client = TestClient(app)


def test_ask_503_when_model_not_running(monkeypatch):
    def fake(**kwargs):
        raise ModelNotRunningError("down")

    monkeypatch.setattr("backend.main.ask_llm", fake)
    response = client.post("/ask", json={"question": "Hello"})
    assert response.status_code == 503
    assert "down" in response.json()["detail"]


def test_ask_504_on_timeout(monkeypatch):
    def fake(**kwargs):
        raise ModelTimeoutError("too slow")

    monkeypatch.setattr("backend.main.ask_llm", fake)
    response = client.post("/ask", json={"question": "Hello"})
    assert response.status_code == 504
    assert "too slow" in response.json()["detail"]


def test_ask_500_on_unexpected_error(monkeypatch):
    def fake(**kwargs):
        raise ValueError("boom")

    monkeypatch.setattr("backend.main.ask_llm", fake)
    response = client.post("/ask", json={"question": "Hello"})
    assert response.status_code == 500
    assert "boom" in response.json()["detail"]


def test_ask_502_on_model_response_error(monkeypatch):
    def fake(**kwargs):
        raise ModelResponseError("bad output")

    monkeypatch.setattr("backend.main.ask_llm", fake)
    response = client.post("/ask", json={"question": "Hello"})
    assert response.status_code == 502
    assert "bad output" in response.json()["detail"]


def test_stream_error_event_on_model_response_error(monkeypatch):
    def fake(**kwargs):
        yield "Hel"
        raise ModelResponseError("runner died")

    monkeypatch.setattr("backend.main.ask_llm_stream", fake)
    response = client.post("/ask/stream", json={"question": "Hello"})
    assert response.status_code == 200
    assert 'data: {"token": "Hel"}' in response.text
    assert '"error"' in response.text
    assert "[DONE]" not in response.text


def test_stream_emits_error_event_after_partial_output(monkeypatch):
    def fake(**kwargs):
        yield "Hel"
        raise ModelNotRunningError("down")

    monkeypatch.setattr("backend.main.ask_llm_stream", fake)
    response = client.post("/ask/stream", json={"question": "Hello"})
    assert response.status_code == 200
    assert 'data: {"token": "Hel"}' in response.text
    assert '"error"' in response.text
    assert "[DONE]" not in response.text


def test_stream_happy_path_ends_with_done(monkeypatch):
    def fake(**kwargs):
        yield "a"
        yield "b"

    monkeypatch.setattr("backend.main.ask_llm_stream", fake)
    response = client.post("/ask/stream", json={"question": "Hello"})
    assert response.status_code == 200
    assert 'data: {"token": "a"}' in response.text
    assert 'data: {"token": "b"}' in response.text
    assert "data: [DONE]" in response.text
