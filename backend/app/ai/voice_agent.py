"""AI Voice Screening Agent — AI feature #2.

Drives a spoken screening interview turn-by-turn. The client handles speech
(Web Speech API STT/TTS); this service decides the next question, scores the
candidate's last answer, and produces a final scorecard. Gemini powers adaptive
questioning; a scripted competency bank is the fallback.
"""
from __future__ import annotations

from app.ai.gemini_client import generate_json, is_available

_FALLBACK_QUESTIONS = [
    "Tell me briefly about your most relevant experience for this role.",
    "Describe a challenging problem you solved and how you approached it.",
    "How do you keep your technical skills current?",
    "Why are you interested in this position?",
]

_MAX_QUESTIONS = 4

_TURN_PROMPT = """\
You are an AI recruiter conducting a short voice screening for "{job_title}".
You have asked {asked} of {max_q} questions.

Conversation so far:
{convo}

The candidate just said:
"{transcript}"

Return STRICTLY valid JSON:
  "answer_score"  integer 0-10 scoring the candidate's last answer (0 if no answer yet)
  "question"      the next question to ask (concise, conversational)
  "finished"      boolean — true if you have asked enough questions
  "summary"       one-sentence assessment (only when finished, else "")
"""


def _heuristic_score(transcript: str) -> int:
    words = len((transcript or "").split())
    if words == 0:
        return 0
    return max(2, min(10, 3 + words // 12))


async def next_turn(job_title: str, transcript: str, history: list[dict]) -> dict:
    asked = sum(1 for h in history if h.get("role") == "assistant")

    if is_available():
        convo = "\n".join(
            f"{h.get('role', 'user').upper()}: {h.get('content', '')}" for h in history
        )
        prompt = _TURN_PROMPT.format(
            job_title=job_title, asked=asked, max_q=_MAX_QUESTIONS,
            convo=convo or "(interview just starting)", transcript=transcript or "(no answer yet)",
        )
        data = await generate_json(prompt)
        if data and "question" in data:
            finished = bool(data.get("finished")) or asked >= _MAX_QUESTIONS
            return {
                "question": "" if finished else data["question"],
                "follow_up": asked > 0,
                "answer_score": data.get("answer_score") if asked > 0 else None,
                "finished": finished,
                "scorecard": _scorecard(history, transcript, data.get("answer_score"))
                if finished else None,
                "summary": data.get("summary", ""),
                "ai_powered": True,
            }

    # Fallback scripted interview
    score = _heuristic_score(transcript) if asked > 0 else None
    finished = asked >= _MAX_QUESTIONS
    question = "" if finished else _FALLBACK_QUESTIONS[min(asked, len(_FALLBACK_QUESTIONS) - 1)]
    return {
        "question": question,
        "follow_up": asked > 0,
        "answer_score": score,
        "finished": finished,
        "scorecard": _scorecard(history, transcript, score) if finished else None,
        "ai_powered": False,
    }


def _scorecard(history: list[dict], last_transcript: str, last_score) -> dict:
    answers = [h for h in history if h.get("role") == "user"]
    scores = [h.get("score") for h in answers if h.get("score") is not None]
    if last_score is not None:
        scores.append(last_score)
    avg = round(sum(scores) / len(scores), 1) if scores else 0.0
    return {
        "overall_score": avg,
        "answers_given": len(answers) + (1 if last_transcript else 0),
        "recommendation": "PROCEED" if avg >= 6 else "HOLD",
    }
