import httpx
import pytest

from backend import llm_client
from backend.llm_client import (
    ModelNotRunningError,
    ModelResponseError,
    ModelTimeoutError,
    ask_llm,
    ask_llm_stream,
)


def _install_transport(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def client_factory(**kwargs):
        kwargs["transport"] = transport
        return real_client(**kwargs)

    monkeypatch.setattr(llm_client.httpx, "Client", client_factory)


def test_ask_llm_maps_connect_error(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("refused")

    _install_transport(monkeypatch, handler)
    with pytest.raises(ModelNotRunningError):
        ask_llm(question="hi")


def test_ask_llm_maps_timeout(monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout("slow")

    _install_transport(monkeypatch, handler)
    with pytest.raises(ModelTimeoutError):
        ask_llm(question="hi")


def test_ask_llm_maps_http_status_error(monkeypatch):
    def handler(request):
        return httpx.Response(500, json={"error": "model not found"})

    _install_transport(monkeypatch, handler)
    with pytest.raises(ModelNotRunningError):
        ask_llm(question="hi")


def test_ask_llm_returns_stripped_content(monkeypatch):
    def handler(request):
        return httpx.Response(200, json={"message": {"content": "  Answer.  "}})

    _install_transport(monkeypatch, handler)
    assert ask_llm(question="hi") == "Answer."


def test_ask_llm_stream_yields_chunks_until_done(monkeypatch):
    def handler(request):
        content = (
            b'{"message": {"content": "Hel"}}\n'
            b'{"message": {"content": "lo"}, "done": true}\n'
        )
        return httpx.Response(200, content=content)

    _install_transport(monkeypatch, handler)
    assert list(ask_llm_stream(question="hi")) == ["Hel", "lo"]


def test_ask_llm_stream_maps_connect_error(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("refused")

    _install_transport(monkeypatch, handler)
    with pytest.raises(ModelNotRunningError):
        list(ask_llm_stream(question="hi"))


def test_ask_llm_raises_on_error_payload(monkeypatch):
    def handler(request):
        return httpx.Response(
            200, json={"error": "model runner has unexpectedly stopped"}
        )

    _install_transport(monkeypatch, handler)
    with pytest.raises(ModelResponseError) as excinfo:
        ask_llm(question="hi")
    assert "model runner has unexpectedly stopped" in str(excinfo.value)


def test_ask_llm_raises_on_empty_answer(monkeypatch):
    def handler(request):
        return httpx.Response(200, json={"message": {"content": "   "}})

    _install_transport(monkeypatch, handler)
    with pytest.raises(ModelResponseError):
        ask_llm(question="hi")


def test_ask_llm_stream_raises_on_mid_stream_error(monkeypatch):
    def handler(request):
        content = (
            b'{"message": {"content": "Hel"}}\n'
            b'{"error": "runner died"}\n'
        )
        return httpx.Response(200, content=content)

    _install_transport(monkeypatch, handler)
    gen = ask_llm_stream(question="hi")
    assert next(gen) == "Hel"
    with pytest.raises(ModelResponseError):
        next(gen)


def test_build_messages_includes_context_and_history():
    messages = llm_client.build_messages(
        "Q", context="CTX", history=[{"role": "user", "content": "prev"}]
    )
    assert messages[0]["role"] == "system"
    assert messages[1] == {"role": "user", "content": "prev"}
    assert "CTX" in messages[-1]["content"]
    assert "Q" in messages[-1]["content"]
