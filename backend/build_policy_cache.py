"""Precompute embeddings for the policy knowledge base.

Run once (whenever the policies or embedding model change):
    python build_policy_cache.py

Writes app/ai/policy_embeddings.json, which index_policies() loads at startup so
serverless cold starts need zero embedding API calls.
"""
import json
import time
from pathlib import Path

from app.ai import gemini_client
from app.ai.policies import POLICIES, _CACHE_PATH
from app.config import settings


def main() -> None:
    if not gemini_client.is_available():
        raise SystemExit("GEMINI_API_KEY not set — cannot build embedding cache.")

    texts = [f"{p['title']}. {p['text']}" for p in POLICIES]

    vectors = None
    for attempt in range(5):  # free tier can 429; retry with backoff
        vectors = gemini_client.embed(texts)
        if vectors and len(vectors) == len(texts):
            break
        wait = 8 * (attempt + 1)
        print(f"  embedding attempt {attempt + 1} failed; retrying in {wait}s…")
        time.sleep(wait)

    if not vectors or len(vectors) != len(texts):
        raise SystemExit("Failed to embed policies after retries (rate limited?).")

    payload = {
        "model": settings.embedding_model_gemini,
        "dim": len(vectors[0]),
        "vectors": vectors,
    }
    Path(_CACHE_PATH).write_text(json.dumps(payload))
    print(f"✅ Wrote {_CACHE_PATH} — {len(vectors)} vectors, dim {payload['dim']}.")


if __name__ == "__main__":
    main()
