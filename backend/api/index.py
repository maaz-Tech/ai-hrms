"""Vercel serverless entrypoint.

Vercel's Python runtime detects the module-level ASGI ``app`` and serves it.
We add the backend root to sys.path so the ``app`` package imports cleanly.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

# Exposed for the Vercel @vercel/python runtime.
__all__ = ["app"]
