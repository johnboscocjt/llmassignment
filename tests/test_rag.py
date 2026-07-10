import os

from backend.rag import _tokenize, load_faq_chunks, retrieve_context

FAQ_TEXT = """# UDSM FAQ

## Course Registration
Register on the ARIS portal during registration week.

## Library Services
The library opens at 8am. Borrow books with your student ID.

## Fee Payment
Pay fees through GePG control numbers.
"""


def test_tokenize_lowercases_and_drops_short_words():
    tokens = _tokenize("The ARIS portal, at 8am!")
    assert "aris" in tokens
    assert "portal" in tokens
    assert "8am" in tokens
    assert "at" not in tokens


def test_tokenize_drops_common_stopwords():
    tokens = _tokenize("What is the capital of France?")
    assert "capital" in tokens
    assert "france" in tokens
    assert "the" not in tokens
    assert "what" not in tokens


def test_retrieve_context_off_topic_question_returns_empty(tmp_path, monkeypatch):
    path = tmp_path / "faq.md"
    path.write_text(FAQ_TEXT, encoding="utf-8")
    monkeypatch.setattr("backend.rag.FAQ_PATH", path)

    assert retrieve_context("What is the capital of France?") == ""


def test_load_faq_chunks_splits_on_h2(tmp_path):
    path = tmp_path / "faq.md"
    path.write_text(FAQ_TEXT, encoding="utf-8")
    chunks = load_faq_chunks(path)
    assert len(chunks) == 3
    assert chunks[0]["title"] == "Course Registration"
    assert all("# UDSM FAQ" not in c["content"] for c in chunks)


def test_load_faq_chunks_missing_file_returns_empty(tmp_path):
    assert load_faq_chunks(tmp_path / "nope.md") == []


def test_retrieve_context_returns_best_matches(tmp_path, monkeypatch):
    path = tmp_path / "faq.md"
    path.write_text(FAQ_TEXT, encoding="utf-8")
    monkeypatch.setattr("backend.rag.FAQ_PATH", path)

    result = retrieve_context("How do I register on ARIS?")
    assert "ARIS" in result
    assert result != ""


def test_retrieve_context_no_overlap_returns_empty(tmp_path, monkeypatch):
    path = tmp_path / "faq.md"
    path.write_text(FAQ_TEXT, encoding="utf-8")
    monkeypatch.setattr("backend.rag.FAQ_PATH", path)

    assert retrieve_context("zzz qqq") == ""


def test_retrieve_context_empty_question_returns_empty(tmp_path, monkeypatch):
    path = tmp_path / "faq.md"
    path.write_text(FAQ_TEXT, encoding="utf-8")
    monkeypatch.setattr("backend.rag.FAQ_PATH", path)

    assert retrieve_context("!!!") == ""


def test_load_faq_chunks_uses_cache(tmp_path):
    path = tmp_path / "faq.md"
    path.write_text(FAQ_TEXT, encoding="utf-8")
    first = load_faq_chunks(path)

    st = path.stat()
    path.write_text("## Something Else\nNew content.\n", encoding="utf-8")
    os.utime(path, (st.st_atime, st.st_mtime))

    second = load_faq_chunks(path)
    assert second == first


def test_load_faq_chunks_invalidates_on_mtime_change(tmp_path):
    path = tmp_path / "faq.md"
    path.write_text(FAQ_TEXT, encoding="utf-8")
    first = load_faq_chunks(path)

    st = path.stat()
    path.write_text("## Something Else\nNew content.\n", encoding="utf-8")
    os.utime(path, (st.st_atime, st.st_mtime + 10))

    second = load_faq_chunks(path)
    assert second != first
    assert second[0]["title"] == "Something Else"


def test_retrieve_context_reflects_faq_edit(tmp_path, monkeypatch):
    path = tmp_path / "faq.md"
    path.write_text("## Course Registration\nRegister on ARIS.\n", encoding="utf-8")
    monkeypatch.setattr("backend.rag.FAQ_PATH", path)

    retrieve_context("How do I register on ARIS?")

    st = path.stat()
    path.write_text("## Hostel Application\nApply for hostel rooms early.\n", encoding="utf-8")
    os.utime(path, (st.st_atime, st.st_mtime + 10))

    result = retrieve_context("How do I apply for a hostel room?")
    assert "Hostel Application" in result
