"""Autonomous resume screening — AI feature #1.

Scores a resume against a job with NO human intervention:

1. Gemini structured-JSON scoring against the job requirements.
2. Semantic similarity between resume and job (``vector_store``) blended in.
3. Deterministic heuristic fallback when Gemini is unavailable, so screening
   always produces a usable, explainable score.
"""
from __future__ import annotations

import re

from app.ai import vector_store
from app.ai.gemini_client import generate_json, is_available

_SCORING_PROMPT = """\
Role: Senior Technical Recruiter for an HR Management System.

Task: Evaluate the candidate RESUME against the JOB and decide how strong a
match they are. Be objective and penalise missing must-have skills.

Scoring guide:
- 8-10: Strong match, meets all/most requirements.
- 5-7: Partial match, meets some requirements.
- 1-4: Weak match, missing key qualifications.

Return STRICTLY valid JSON with these keys:
  "overall_score"     integer 1-10
  "role_match_score"  integer 1-10
  "experience_years"  number
  "key_skills_found"  array of strings (max 10)
  "missing_skills"    array of strings (max 8)
  "recommendation"    one of "STRONG_YES" | "YES" | "MAYBE" | "NO"
  "reasoning"         string, max 60 words

JOB TITLE: {title}
JOB REQUIREMENTS:
{requirements}

RESUME:
{resume}
"""


_SKILL_STOPWORDS = {"years", "year", "yrs", "experience", "plus", "and", "with"}


def _extract_skills(requirements: str) -> list[str]:
    tokens = re.split(r"[,/;\n•\-]+", requirements.lower())
    skills = []
    for t in tokens:
        t = t.strip()
        if re.fullmatch(r"\d+\+?\s*(years|yrs)?", t):  # drop "5+ years" style tokens
            continue
        if 2 <= len(t) <= 30 and t not in _SKILL_STOPWORDS:
            skills.append(t)
    return skills


def _skill_present(skill: str, resume_l: str) -> bool:
    """A skill counts as present if it appears, or all its significant words do."""
    if skill in resume_l:
        return True
    words = [w for w in re.split(r"\s+", skill) if w not in _SKILL_STOPWORDS]
    return bool(words) and all(w in resume_l for w in words)


def _heuristic_screen(resume: str, title: str, requirements: str) -> dict:
    """Deterministic fallback: keyword coverage + semantic similarity."""
    resume_l = resume.lower()
    required = _extract_skills(requirements)
    found = [s for s in required if _skill_present(s, resume_l)]
    missing = [s for s in required if not _skill_present(s, resume_l)]
    coverage = (len(found) / len(required)) if required else 0.5

    sem = vector_store.similarity(resume, f"{title}. {requirements}")
    # Coverage dominates; map onto a realistic 2.5-10 band so partial matches
    # are distinguishable and strong matches can clear the shortlist bar.
    blended = 0.7 * coverage + 0.3 * sem  # 0..1
    overall = round(2.5 + blended * 7.5, 1)

    m = re.search(r"(\d+)\+?\s*(?:years|yrs)", resume_l)
    years = float(m.group(1)) if m else 0.0

    if overall >= 8:
        rec = "STRONG_YES"
    elif overall >= 6.5:
        rec = "YES"
    elif overall >= 4.5:
        rec = "MAYBE"
    else:
        rec = "NO"

    return {
        "overall_score": overall,
        "role_match_score": round(sem * 10, 1),
        "experience_years": years,
        "key_skills_found": found[:10],
        "missing_skills": missing[:8],
        "recommendation": rec,
        "reasoning": (
            f"Matched {len(found)}/{len(required) or 0} listed requirements; "
            f"semantic fit {sem:.0%}. Heuristic screen (Gemini disabled)."
        ),
        "ai_powered": False,
    }


async def screen_resume(resume_text: str, title: str, requirements: str) -> dict:
    """Screen a single resume. Always returns a normalised result dict."""
    if is_available():
        prompt = _SCORING_PROMPT.format(
            title=title, requirements=requirements, resume=resume_text[:12000]
        )
        data = await generate_json(prompt)
        if data and "overall_score" in data:
            data.setdefault("role_match_score", data["overall_score"])
            data.setdefault("experience_years", 0)
            data.setdefault("key_skills_found", [])
            data.setdefault("missing_skills", [])
            data.setdefault("recommendation", "MAYBE")
            data.setdefault("reasoning", "")
            data["ai_powered"] = True
            return data
    return _heuristic_screen(resume_text, title, requirements)
