import json

import requests
import streamlit as st

from docs_ui import render_docs

st.set_page_config(
    page_title="UDSM Student Support Assistant",
    page_icon="🎓",
    layout="wide",
)

DEFAULT_BACKEND = "http://127.0.0.1:8000"

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_qa" not in st.session_state:
    st.session_state.last_qa = None
if "page" not in st.session_state:
    st.session_state.page = "chat"


def build_history_payload() -> list[dict[str, str]]:
    """Prior turns only (exclude the latest user message)."""
    prior = st.session_state.messages[:-1] if st.session_state.messages else []
    prior = prior[-6:]
    return [
        {"role": m["role"], "content": m["content"]}
        for m in prior
        if m["role"] in ("user", "assistant") and m.get("content")
    ]


def ask_payload(question: str, use_history: bool) -> dict:
    payload = {
        "question": question,
        "use_rag": use_rag,
        "prompt_version": prompt_version,
        "history": build_history_payload() if use_history else [],
    }
    return payload


def stream_answer(question: str, use_history: bool):
    url = f"{backend_url.rstrip('/')}/ask/stream"
    with requests.post(
        url,
        json=ask_payload(question, use_history),
        stream=True,
        timeout=120,
    ) as response:
        if response.status_code != 200:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except Exception:
                pass
            raise RuntimeError(f"Backend error ({response.status_code}): {detail}")

        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break
            data = json.loads(data_str)
            if "error" in data:
                raise RuntimeError(data["error"])
            token = data.get("token", "")
            if token:
                yield token


with st.sidebar:
    st.markdown("### Navigation")
    if st.button(
        "Chat",
        use_container_width=True,
        type="primary" if st.session_state.page == "chat" else "secondary",
    ):
        st.session_state.page = "chat"
        st.rerun()

    if st.button(
        "Help & Documentation",
        use_container_width=True,
        type="primary" if st.session_state.page == "docs" else "secondary",
    ):
        st.session_state.page = "docs"
        st.rerun()

    st.markdown("---")

    if st.session_state.page == "chat":
        st.header("Settings")
        backend_url = st.text_input("Backend URL", value=DEFAULT_BACKEND)
        use_rag = st.checkbox("Use FAQ (RAG)", value=True)
        use_history = st.checkbox("Use conversation history", value=True)
        use_stream = st.checkbox("Stream response", value=False)
        prompt_version = st.selectbox(
            "Prompt version",
            options=["improved", "original"],
            format_func=lambda x: "Improved (UDSM)" if x == "improved" else "Original (generic)",
        )

        if st.button("Clear chat"):
            st.session_state.messages = []
            st.session_state.last_qa = None
            st.rerun()

        try:
            summary = requests.get(
                f"{backend_url.rstrip('/')}/feedback/summary", timeout=5
            )
            if summary.status_code == 200:
                s = summary.json()
                st.caption(
                    f"Feedback: {s.get('Good', 0)} Good · "
                    f"{s.get('Average', 0)} Average · "
                    f"{s.get('Poor', 0)} Poor"
                )
        except requests.exceptions.RequestException:
            pass

        st.markdown("---")
        st.markdown("**Sample questions**")
        st.markdown("- How do I register for courses at UDSM?")
        st.markdown("- What are the library opening hours?")
        st.markdown("- How do I pay fees through GePG?")
        st.markdown("- How do I apply for UDSM hostel?")
    else:
        backend_url = DEFAULT_BACKEND
        use_rag = True
        use_history = True
        use_stream = False
        prompt_version = "improved"

if st.session_state.page == "docs":
    render_docs()
    st.stop()

st.title("UDSM Student Support Assistant")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask about UDSM student services...")

if question is not None:
    question = question.strip()
    if not question:
        st.warning("Please enter a question.")
    else:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            try:
                if use_stream:
                    received_chunks: list[str] = []

                    def _tracked_stream():
                        for token in stream_answer(question, use_history):
                            received_chunks.append(token)
                            yield token

                    try:
                        answer = st.write_stream(_tracked_stream())
                    except RuntimeError as exc:
                        partial = "".join(received_chunks)
                        if not partial:
                            raise
                        answer = partial
                        st.warning(f"Response interrupted: {exc}")
                else:
                    with st.spinner("Thinking... this may take up to 60 seconds"):
                        response = requests.post(
                            f"{backend_url.rstrip('/')}/ask",
                            json=ask_payload(question, use_history),
                            timeout=120,
                        )
                        if response.status_code == 200:
                            data = response.json()
                            answer = data.get("answer", "No answer returned.")
                            st.markdown(answer)
                        else:
                            detail = response.json().get("detail", response.text)
                            raise RuntimeError(
                                f"Backend error ({response.status_code}): {detail}"
                            )

                if answer:
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer}
                    )
                    st.session_state.last_qa = {
                        "question": question,
                        "answer": answer,
                    }
            except requests.exceptions.ConnectionError:
                error_msg = (
                    "Cannot connect to backend. Is FastAPI running on port 8000?"
                )
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
            except requests.exceptions.Timeout:
                error_msg = (
                    "Request timed out. The model may still be loading. "
                    "Please try again."
                )
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
            except RuntimeError as exc:
                error_msg = str(exc)
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )

if st.session_state.last_qa:
    st.markdown("---")
    st.subheader("Rate this answer")
    col1, col2, col3 = st.columns(3)
    qa = st.session_state.last_qa

    def send_feedback(rating: str):
        try:
            requests.post(
                f"{backend_url.rstrip('/')}/feedback",
                json={
                    "question": qa["question"],
                    "answer": qa["answer"],
                    "rating": rating,
                },
                timeout=10,
            )
            st.success(f"Thank you! Rated: {rating}")
        except requests.exceptions.ConnectionError:
            st.error("Cannot save feedback — backend not reachable.")

    with col1:
        if st.button("Good"):
            send_feedback("Good")
    with col2:
        if st.button("Average"):
            send_feedback("Average")
    with col3:
        if st.button("Poor"):
            send_feedback("Poor")
