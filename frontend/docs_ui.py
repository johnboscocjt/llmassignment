import streamlit as st


def render_docs() -> None:
    st.title("Help & Documentation")
    st.caption("UDSM Student Support Assistant")

    st.markdown("""
Welcome! This assistant answers questions about **University of Dar es Salaam (UDSM)**
student services using a local AI model and an FAQ knowledge base.
""")

    st.header("Features")

    st.markdown("""
| Feature | What it does |
|---------|----------------|
| **UDSM student support chat** | Ask questions in plain language about campus services and get AI-generated answers |
| **Local AI** | Runs on your machine via Ollama — no external API keys; your questions stay on the local system |
| **FAQ-powered answers** | Searches the UDSM FAQ document before answering so replies use known university information |
| **Multi-turn conversations** | Remembers your last few messages so you can ask follow-up questions (e.g. *"And what documents do I need?"*) |
| **Streaming responses** | Optional mode that shows the answer word-by-word as it is generated |
| **UDSM-tuned responses** | Improved prompt focuses only on UDSM student services; you can compare with a generic prompt in settings |
| **Answer ratings** | After each reply, rate **Good**, **Average**, or **Poor** to record answer quality |
| **Feedback overview** | Sidebar shows how many answers were rated Good, Average, or Poor |
| **Chat history** | See your full conversation in the chat window during the session |
| **Clear chat** | Start a fresh conversation with one click |
| **Sample questions** | Sidebar lists example questions you can try |
| **Helpful error messages** | Clear notices if the server is down, the AI is not running, or you send an empty question |
| **Loading indicator** | Spinner or streaming view while the AI prepares your answer (may take up to 60 seconds) |
""")

    st.header("What topics can I ask about?")

    st.markdown("""
Ask questions in plain language about:

| Topic | Examples |
|-------|----------|
| **Course registration** | How do I register on ARIS? When is the registration window? |
| **Examinations** | What are the exam rules? What items are not allowed? |
| **Library** | Opening hours, borrowing books, OPAC |
| **ICT support** | Student email, Wi-Fi, portal login help |
| **Hostel** | How to apply for accommodation |
| **Fees** | Paying through GePG, NMB, or CRDB |
| **Academic calendar** | Semester dates, registration week |
| **Student conduct** | Regulations and discipline |
""")

    st.header("How to use the chat")

    st.markdown("""
1. Click **Chat** under **Navigation** in the sidebar.
2. Type your question in the box at the bottom and press Enter.
3. Wait for the answer — it may take **up to 60 seconds** while the AI generates a response.
4. Read the reply. You can ask **follow-up questions** in the same conversation (keep **Use conversation history** on).
5. Optionally enable **Stream response** to see text appear gradually.
6. Rate the answer with **Good**, **Average**, or **Poor** to help improve the system.
7. Use **Clear chat** in the sidebar to start a new conversation.
""")

    st.header("Sidebar settings")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
**Use FAQ (RAG)** — *Recommended: ON*  
Searches the UDSM FAQ before answering so replies stay grounded in known information.

**Use conversation history** — *Default: ON*  
Lets the assistant remember your last few messages for follow-up questions.

**Stream response** — *Optional*  
Shows the answer word-by-word as it is generated instead of waiting for the full text.
""")

    with col2:
        st.markdown("""
**Prompt version**  
- *Improved (UDSM)* — tailored for UDSM student services *(recommended)*  
- *Original (generic)* — basic assistant without UDSM-specific rules

**Backend URL**  
Leave as `http://127.0.0.1:8000` unless your instructor says otherwise.
""")

    st.header("Tips for better answers")

    st.markdown("""
- Be **specific** — e.g. *"How do I pay fees through GePG?"* instead of *"fees"*
- Keep **FAQ (RAG) enabled** for registration, library, hostel, and fee questions
- For follow-ups, leave **conversation history** on — e.g. *"And what documents do I need?"*
- If the answer seems wrong, contact the **relevant UDSM office** directly
""")

    st.header("What this assistant cannot do")

    st.markdown("""
- Replace **official UDSM announcements**, fee notices, or verified policy documents
- Access your **ARIS account**, GePG payments, or personal student records
- Guarantee **100% accurate** answers — AI can sometimes make mistakes
- Work if the **backend or AI model** is not running (you may see an error message)
""")

    st.header("If something goes wrong")

    st.markdown("""
| Problem | What to do |
|---------|------------|
| *Cannot connect to backend* | Start the API server on port 8000 |
| *Model not running* (503 error) | Start Ollama and the AI model |
| Blank question warning | Type a question before sending |
| Very long wait | Wait up to 60 seconds or enable streaming |
| Wrong answer | Rate **Poor** and check with the official UDSM office |
""")

    st.divider()

    st.markdown("""
**Note:** FAQ content in this demo is for learning purposes. For real decisions,
always confirm with UDSM ICT, the library, Dean of Students, or other official offices.
""")
