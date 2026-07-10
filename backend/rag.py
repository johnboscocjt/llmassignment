import re
from pathlib import Path

from backend.config import FAQ_PATH, KB_PATHS

_STOPWORDS = frozenset(
    {
        "the", "and", "for", "are", "but", "not", "you", "your", "can",
        "has", "how", "who", "did", "its", "let", "say", "she", "too",
        "use", "that", "with", "this", "from", "they", "have", "what",
        "when", "where", "which", "about", "would", "could", "should",
        "there", "their", "these", "those", "will", "does", "into",
        "than", "then", "some", "such", "only", "more", "most", "very",
        "just", "been", "being", "over", "also", "again", "after",
        "before", "between", "during", "while", "until", "without",
        "within", "upon", "through", "was", "were", "him", "her", "his",
        "our", "out", "get", "got", "all", "any", "few", "own", "same",
        "why",
    }
)


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {w for w in words if len(w) > 2 and w not in _STOPWORDS}


def _parse_faq(path: Path) -> list[dict[str, str]]:
    content = path.read_text(encoding="utf-8")
    sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)
    chunks: list[dict[str, str]] = []

    for section in sections:
        section = section.strip()
        if not section.startswith("## "):
            continue
        lines = section.splitlines()
        title = lines[0].lstrip("# ").strip()
        body = "\n".join(lines[1:]).strip()
        if body:
            chunks.append({"title": title, "content": body})

    return chunks


# cache: {resolved_path: (mtime, chunks, [token_set per chunk])}
_faq_cache: dict[Path, tuple[float, list[dict[str, str]], list[set[str]]]] = {}


def _load_faq(path: Path) -> tuple[list[dict[str, str]], list[set[str]]]:
    if not path.exists():
        return [], []
    resolved = path.resolve()
    mtime = resolved.stat().st_mtime
    cached = _faq_cache.get(resolved)
    if cached and cached[0] == mtime:
        return cached[1], cached[2]
    chunks = _parse_faq(resolved)
    token_sets = [_tokenize(f"{c['title']} {c['content']}") for c in chunks]
    _faq_cache[resolved] = (mtime, chunks, token_sets)
    return chunks, token_sets


def load_faq_chunks(faq_path: Path | None = None) -> list[dict[str, str]]:
    path = faq_path or FAQ_PATH
    return _load_faq(path)[0]


def _load_knowledge_base() -> tuple[list[dict[str, str]], list[set[str]]]:
    """Load and cache every configured knowledge-base file (FAQ + prospectus)
    into one flat list of chunks with matching token sets."""
    all_chunks: list[dict[str, str]] = []
    all_tokens: list[set[str]] = []
    for path in KB_PATHS:
        chunks, token_sets = _load_faq(path)
        all_chunks.extend(chunks)
        all_tokens.extend(token_sets)
    return all_chunks, all_tokens


def retrieve_context(question: str, top_k: int = 3) -> str:
    chunks, token_sets = _load_knowledge_base()
    if not chunks:
        return ""

    question_tokens = _tokenize(question)
    if not question_tokens:
        return ""

    min_overlap = 2 if len(question_tokens) > 1 else 1

    scored: list[tuple[int, dict[str, str]]] = []
    for chunk, chunk_tokens in zip(chunks, token_sets):
        overlap = len(question_tokens & chunk_tokens)
        if overlap >= min_overlap:
            scored.append((overlap, chunk))

    # Highest keyword overlap first; ties keep knowledge-base order, so the
    # curated FAQ (loaded first) wins over prospectus chunks on equal scores.
    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [chunk for _, chunk in scored[:top_k]]

    if not selected:
        return ""

    parts = []
    for chunk in selected:
        parts.append(f"### {chunk['title']}\n{chunk['content']}")
    return "\n\n".join(parts)
