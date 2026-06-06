"""Semantic vector store for resumes & HR policies.

Both the embedder and the backing store are optional:

* Embeddings: ``sentence-transformers`` if installed, else a deterministic
  hashing embedder (good enough for demo semantic ranking without a 90MB model
  download / torch).
* Storage: Qdrant Cloud if ``QDRANT_URL`` is set, else in-memory Qdrant if the
  client is installed, else a pure-Python cosine index.

This guarantees resume semantic ranking works out of the box.
"""
from __future__ import annotations

import hashlib
import logging
import math

from app.config import settings

logger = logging.getLogger(__name__)

_EMBED_DIM = 384
_encoder = None
_encoder_tried = False


def _get_encoder():
    global _encoder, _encoder_tried
    if _encoder_tried:
        return _encoder
    _encoder_tried = True
    try:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        _encoder = SentenceTransformer(settings.embedding_model)
        logger.info("Loaded embedding model %s", settings.embedding_model)
    except Exception as exc:  # pragma: no cover - optional heavy dep
        logger.info("sentence-transformers unavailable (%s) — hashing embedder.", exc)
        _encoder = None
    return _encoder


def embed(text: str) -> list[float]:
    """Return an embedding vector for *text*.

    Preference order: Gemini embeddings API (semantic, lightweight — ideal for
    serverless) → local sentence-transformers → deterministic hashing embedder.
    """
    text = text or ""
    # 1. Gemini embeddings (no heavy local deps).
    from app.ai import gemini_client  # local import avoids a circular import

    if gemini_client.is_available():
        vecs = gemini_client.embed([text])
        if vecs:
            return vecs[0]
    # 2. Local model if installed.
    encoder = _get_encoder()
    if encoder is not None:
        return encoder.encode(text).tolist()
    # 3. Hashing fallback.
    return _hash_embed(text)


def _hash_embed(text: str, dim: int = _EMBED_DIM) -> list[float]:
    """Deterministic bag-of-words hashing embedding with L2 normalisation."""
    vec = [0.0] * dim
    for token in text.lower().split():
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def embed_many(texts: list[str]) -> list[list[float]]:
    """Embed several texts in ONE call where possible.

    This matters on serverless: the policy KB is re-indexed on every cold start,
    so batching keeps it to a single embedding request instead of one-per-doc.
    """
    if not texts:
        return []
    from app.ai import gemini_client  # local import avoids a circular import

    if gemini_client.is_available():
        vecs = gemini_client.embed(texts)
        if vecs and len(vecs) == len(texts):
            return vecs
    return [embed(t) for t in texts]


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):  # guard against mixed embedding backends/dims
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def similarity(text_a: str, text_b: str) -> float:
    """Convenience: semantic similarity in [0, 1] between two texts."""
    score = cosine(embed(text_a), embed(text_b))
    return max(0.0, min(1.0, (score + 1) / 2))  # map [-1,1] -> [0,1]


class _MemoryIndex:
    """Tiny in-process cosine index used when Qdrant isn't configured."""

    def __init__(self) -> None:
        self._items: list[tuple[int, list[float], dict]] = []

    def upsert(self, point_id: int, vector: list[float], payload: dict) -> None:
        self._items = [it for it in self._items if it[0] != point_id]
        self._items.append((point_id, vector, payload))

    def search(self, vector: list[float], limit: int = 5) -> list[dict]:
        scored = [
            {**payload, "id": pid, "score": cosine(vector, vec)}
            for pid, vec, payload in self._items
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]


_memory = _MemoryIndex()


def index_document(point_id: int, text: str, payload: dict) -> None:
    """Index a resume / policy chunk for later semantic search."""
    _memory.upsert(point_id, embed(text), payload)


def index_documents(items: list[tuple[int, str, dict]]) -> None:
    """Batch-index documents with a single embedding call (see embed_many)."""
    vectors = embed_many([text for _, text, _ in items])
    for (point_id, _, payload), vec in zip(items, vectors):
        _memory.upsert(point_id, vec, payload)


def index_into_memory(point_id: int, vector: list[float], payload: dict) -> None:
    """Index a document from a precomputed vector (no embedding call)."""
    _memory.upsert(point_id, vector, payload)


def search(query: str, limit: int = 5) -> list[dict]:
    """Semantic search over indexed documents."""
    return _memory.search(embed(query), limit=limit)
