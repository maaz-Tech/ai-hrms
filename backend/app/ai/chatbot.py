"""AI HR Assistant chatbot — AI feature #3 (RAG).

Retrieves relevant policy chunks from the vector store and lets Gemini answer
grounded in them, plus the employee's own live data (leave balance, latest
payslip) passed in as context. Falls back to an extractive answer from the
retrieved policy text when Gemini is unavailable.
"""
from __future__ import annotations

from app.ai import vector_store
from app.ai.gemini_client import generate_text, is_available

_SYSTEM = """\
You are the FWC HR Assistant. Answer the employee's question using ONLY the
policy context and their personal data provided. Be concise and friendly. If
the answer isn't in the context, say you'll route them to HR. Do not invent
numbers.
"""


def _retrieve(query: str, limit: int = 3) -> list[dict]:
    hits = [h for h in vector_store.search(query, limit=limit) if h.get("kind") == "policy"]
    return hits


async def answer(message: str, personal_context: str = "", history: list[dict] | None = None) -> dict:
    hits = _retrieve(message)
    sources = [h["title"] for h in hits]
    policy_block = "\n\n".join(f"[{h['title']}]\n{h['text']}" for h in hits)

    if is_available():
        convo = ""
        for turn in (history or [])[-6:]:
            convo += f"{turn.get('role', 'user').upper()}: {turn.get('content', '')}\n"
        prompt = (
            f"{_SYSTEM}\n\nPOLICY CONTEXT:\n{policy_block or '(none)'}\n\n"
            f"EMPLOYEE DATA:\n{personal_context or '(none)'}\n\n"
            f"CONVERSATION:\n{convo}USER: {message}\nASSISTANT:"
        )
        reply = await generate_text(prompt)
        if reply:
            return {"reply": reply, "sources": sources, "ai_powered": True}

    # Heuristic fallback: surface the most relevant policy + personal data.
    if hits:
        reply = hits[0]["text"]
        if personal_context:
            reply += f"\n\nYour details: {personal_context}"
    elif personal_context:
        reply = personal_context
    else:
        reply = "I couldn't find that in the handbook — I'll route you to HR."
    return {"reply": reply, "sources": sources, "ai_powered": False}
