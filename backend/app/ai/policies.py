"""Company HR policy knowledge base, indexed for RAG retrieval.

In a hackathon demo this stands in for an uploaded employee handbook. Each
entry is indexed into the vector store on startup so the chatbot can ground
answers and cite sources.

Policy embeddings are precomputed once into ``policy_embeddings.json`` (see
``build_policy_cache.py``). On startup we load that cache instead of calling the
embedding API — important on serverless, where startup runs on every cold start
and the embedding free-tier quota is small.
"""
import json
import logging
from pathlib import Path

from app.ai import vector_store
from app.config import settings

logger = logging.getLogger(__name__)

_CACHE_PATH = Path(__file__).with_name("policy_embeddings.json")

POLICIES: list[dict] = [
    {
        "title": "Leave Policy",
        "text": (
            "Every full-time employee receives 24 paid leave days per year, "
            "accrued monthly. Casual, sick and earned leave are tracked from the "
            "same balance. Apply via the Attendance page; leaves under 3 days are "
            "auto-approved, longer leaves need manager approval."
        ),
    },
    {
        "title": "Work From Home Policy",
        "text": (
            "Employees may work from home up to 2 days per week with manager "
            "consent. Mark WFH in attendance. Client-facing roles may have "
            "on-site requirements during delivery phases."
        ),
    },
    {
        "title": "Payroll Policy",
        "text": (
            "Salaries are paid on the last working day of each month. Payslips "
            "are available on the Payroll page. Salary comprises Basic, HRA, "
            "Allowances minus statutory Deductions. Annual hikes range 20-40% "
            "based on performance."
        ),
    },
    {
        "title": "Performance Review Policy",
        "text": (
            "Reviews run quarterly. Employees set goals; managers rate on a 1-5 "
            "scale. AI-assisted summaries highlight achievements and growth areas. "
            "Ratings influence the annual hike and ESOP eligibility."
        ),
    },
    {
        "title": "ESOP & Benefits",
        "text": (
            "Employees become eligible for the Employee Stock Ownership Plan "
            "after completing 1 year of service. Benefits include health "
            "insurance and certification reimbursement on completion."
        ),
    },
    {
        "title": "Code of Conduct",
        "text": (
            "Maintain professionalism, protect confidential client data, and "
            "follow the security policy: use OAuth/SSO, never share credentials, "
            "and report incidents to HR immediately."
        ),
    },
]


def _payload(i: int) -> dict:
    p = POLICIES[i]
    return {"title": p["title"], "text": p["text"], "kind": "policy"}


def _load_cache() -> list[list[float]] | None:
    """Return cached policy vectors if present and valid for the active model."""
    if not _CACHE_PATH.exists():
        return None
    try:
        data = json.loads(_CACHE_PATH.read_text())
    except Exception:
        return None
    if (
        data.get("model") != settings.embedding_model_gemini
        or len(data.get("vectors", [])) != len(POLICIES)
    ):
        return None  # stale cache (model changed / policies edited) → re-embed
    return data["vectors"]


def index_policies() -> None:
    """Index the policy KB, using the precomputed embedding cache when valid."""
    cached = _load_cache()
    if cached is not None:
        for i, vec in enumerate(cached):
            vector_store.index_into_memory(1000 + i, vec, _payload(i))
        logger.info("Loaded %d cached policy embeddings (no API calls).", len(cached))
        return
    # No valid cache → embed live (single batched call), then it still works.
    logger.info("No policy embedding cache — embedding live.")
    items = [
        (1000 + i, f"{POLICIES[i]['title']}. {POLICIES[i]['text']}", _payload(i))
        for i in range(len(POLICIES))
    ]
    vector_store.index_documents(items)
