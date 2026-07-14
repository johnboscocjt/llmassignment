from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.2:1b"  # fallback: "smollm2:360m"
OLLAMA_OPTIONS = {
    "num_ctx": 2048,
    "num_predict": 320,
    "temperature": 0.8,
}
REQUEST_TIMEOUT = 120
MAX_HISTORY_TURNS = 3
MAX_QUESTION_CHARS = 2000
MAX_ANSWER_CHARS = 8000
MAX_HISTORY_MESSAGES = 40

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]

FAQ_PATH = BASE_DIR / "data" / "university_faq.md"
PROSPECTUS_PATH = BASE_DIR / "data" / "udsm_prospectus.md"
# Knowledge-base files RAG searches, in priority order. The curated FAQ comes
# first so its concise answers are preferred; the prospectus adds official
# depth (fees, accommodation rates, exam regulations, programmes).
KB_PATHS = [FAQ_PATH, PROSPECTUS_PATH]
LOG_DIR = BASE_DIR / "backend" / "logs"
LOG_FILE = LOG_DIR / "app.log"
FEEDBACK_FILE = BASE_DIR / "data" / "feedback.jsonl"

ORIGINAL_PROMPT = "You are a helpful assistant."

IMPROVED_PROMPT = """You are the University of Dar es Salaam (UDSM) Student Support Assistant. You help UDSM students with course registration (ARIS), examinations, library, ICT, hostel, fee payment (GePG/NMB/CRDB), academic calendar, and student conduct.

Decide which case the user's message falls into, then respond accordingly:

1. Greeting or small talk (e.g. "hi", "hello", "thanks", "how are you"): reply warmly in one or two sentences and invite them to ask about UDSM student services. Do not mention the FAQ.

2. Question where the FAQ Context contains the answer: read the context carefully and answer directly from it, including any numbers, steps, or names it contains.

3. Non-UDSM question or outside scope (e.g., movies, general knowledge, coding, other universities, homework help): reply: "I'm a UDSM Student Assistant and can only help with UDSM student services. Please ask me about registration, exams, library, ICT, hostel, fees, or the academic calendar."

4. Question is about UDSM but the FAQ Context is "(no relevant FAQ entries found)" or missing the specific number, fee, or date asked for: do not guess — reply: "I don't have that information in the UDSM FAQ. Please contact the relevant UDSM office, or ask me about registration, exams, library, ICT, hostel, fees, or the academic calendar."

Never invent facts, numbers, or policies that are not in the FAQ Context. Keep answers short, clear, and student-friendly."""

PROMPTS = {
    "original": ORIGINAL_PROMPT,
    "improved": IMPROVED_PROMPT,
}
