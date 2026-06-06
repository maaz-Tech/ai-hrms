"""Thin async wrapper around the Google Gemini API.

Uses the async ``client.aio.models.generate_content`` API, with
``response_mime_type="application/json"`` for the structured-output calls.

The wrapper is import-safe and key-safe: if ``google-genai`` isn't installed
or ``GEMINI_API_KEY`` isn't set, ``is_available()`` returns False and callers
fall back to deterministic heuristics. This keeps the whole app runnable for a
demo with zero external dependencies.
"""
from __future__ import annotations

import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)

_client = None
_init_attempted = False


def _get_client():
    global _client, _init_attempted
    if _init_attempted:
        return _client
    _init_attempted = True
    if not settings.gemini_api_key:
        logger.info("GEMINI_API_KEY not set — AI features use heuristic fallbacks.")
        return None
    try:
        from google import genai  # noqa: PLC0415

        _client = genai.Client(api_key=settings.gemini_api_key)
    except Exception as exc:  # pragma: no cover - depends on optional dep
        logger.warning("Could not initialise Gemini client: %s", exc)
        _client = None
    return _client


def is_available() -> bool:
    return _get_client() is not None


async def generate_json(prompt: str, temperature: float = 0.0) -> dict | None:
    """Call Gemini and parse a JSON object response. Returns None on failure."""
    client = _get_client()
    if client is None:
        return None
    try:
        from google.genai import types  # noqa: PLC0415

        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=temperature,
            ),
        )
        return json.loads(response.text)
    except Exception as exc:  # pragma: no cover
        logger.warning("Gemini generate_json failed: %s", exc)
        return None


async def generate_text(prompt: str, temperature: float = 0.4) -> str | None:
    """Call Gemini for a free-text response. Returns None on failure."""
    client = _get_client()
    if client is None:
        return None
    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
        return (response.text or "").strip()
    except Exception as exc:  # pragma: no cover
        logger.warning("Gemini generate_text failed: %s", exc)
        return None


def embed(texts: list[str]) -> list[list[float]] | None:
    """Embed one or more texts with Gemini's embedding model (sync, batched).

    Returns a list of vectors (one per input), or None if Gemini is unavailable
    or the call fails so callers can fall back to a local embedder.
    """
    client = _get_client()
    if client is None or not texts:
        return None
    try:
        resp = client.models.embed_content(
            model=settings.embedding_model_gemini,
            contents=texts,
        )
        return [list(e.values) for e in resp.embeddings]
    except Exception as exc:  # pragma: no cover
        logger.warning("Gemini embed failed: %s", exc)
        return None
