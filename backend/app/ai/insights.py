"""AI Performance Insights & attrition risk — AI feature #4.

Turns an employee's raw signals (goals, attendance, tenure, rating history)
into a written review summary, highlights and an attrition-risk flag. Gemini
writes the narrative; a rules-based engine is the fallback and also computes the
attrition score that the prompt is seeded with.
"""
from __future__ import annotations

from app.ai.gemini_client import generate_json, is_available

_PROMPT = """\
You are an HR analytics assistant. Given an employee's performance signals,
write a fair, specific review.

SIGNALS:
{signals}

Return STRICTLY valid JSON:
  "summary"         3-4 sentence performance review
  "highlights"      array of 2-4 short bullet strings
  "rating"          number 1-5
  "attrition_risk"  one of "low" | "medium" | "high"
"""


def compute_attrition_risk(signals: dict) -> str:
    """Simple, explainable risk model used standalone and to seed the prompt."""
    score = 0
    if signals.get("avg_goal_progress", 100) < 40:
        score += 2
    if signals.get("attendance_rate", 1.0) < 0.85:
        score += 2
    if signals.get("recent_rating", 5) < 2.5:
        score += 2
    if signals.get("tenure_months", 24) < 6:
        score += 1
    if signals.get("leave_balance", 24) <= 2:
        score += 1
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _heuristic(signals: dict, risk: str) -> dict:
    progress = signals.get("avg_goal_progress", 0)
    rating = round(min(5.0, 2.0 + progress / 33 + signals.get("attendance_rate", 0) * 1.5), 1)
    highlights = []
    if progress >= 70:
        highlights.append(f"Strong goal delivery ({progress:.0f}% average progress)")
    if signals.get("attendance_rate", 0) >= 0.9:
        highlights.append("Excellent, consistent attendance")
    if risk == "high":
        highlights.append("⚠ Elevated attrition risk — recommend a 1:1 check-in")
    if not highlights:
        highlights.append("Steady performer; set stretch goals next cycle")
    return {
        "summary": (
            f"{signals.get('name', 'The employee')} shows {progress:.0f}% average goal "
            f"progress with a {signals.get('attendance_rate', 0):.0%} attendance rate over "
            f"{signals.get('tenure_months', 0)} months. Attrition risk is assessed as {risk}. "
            "Recommend continued goal-setting and regular feedback."
        ),
        "highlights": highlights,
        "rating": rating,
        "attrition_risk": risk,
        "ai_powered": False,
    }


async def generate_insight(signals: dict) -> dict:
    risk = compute_attrition_risk(signals)
    if is_available():
        seeded = {**signals, "computed_attrition_risk": risk}
        lines = "\n".join(f"- {k}: {v}" for k, v in seeded.items())
        data = await generate_json(_PROMPT.format(signals=lines))
        if data and "summary" in data:
            data.setdefault("highlights", [])
            data.setdefault("rating", 3.0)
            data.setdefault("attrition_risk", risk)
            data["ai_powered"] = True
            return data
    return _heuristic(signals, risk)
