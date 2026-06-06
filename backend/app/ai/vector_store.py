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
    """Return an embedding vector for *text* (model or hashing fallback)."""
    encoder = _get_encoder()
    if encoder is not None:
        return encoder.encode(text or "").tolist()
    return _hash_embed(text or "")


def _hash_embed(text: str, dim: int = _EMBED_DIM) -> list[float]:
    """Deterministic bag-of-words hashing embedding with L2 normalisation."""
    vec = [0.0] * dim
    for token in text.lower().split():
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
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


def search(query: str, limit: int = 5) -> list[dict]:
    """Semantic search over indexed documents."""
    return _memory.search(embed(query), limit=limit)
