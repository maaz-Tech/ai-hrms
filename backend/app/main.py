"""FWC AI-Powered HRMS — FastAPI application entrypoint."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai import gemini_client
from app.ai.policies import index_policies
from app.config import settings
from app.database import Base, engine
from app.routers import (
    ai,
    attendance,
    auth,
    dashboard,
    employees,
    payroll,
    performance,
    recruitment,
)

logging.basicConfig(level=logging.INFO)

# Create tables on startup (Alembic available for real migrations).
import app.models  # noqa: F401, E402  (register models on Base)

Base.metadata.create_all(bind=engine)

# Build the RAG knowledge base. Done at import (not only in lifespan) because
# some serverless ASGI hosts don't run startup lifespan events per cold start.
index_policies()


@asynccontextmanager
async def lifespan(_: FastAPI):
    index_policies()
    yield


app = FastAPI(
    title="FWC AI-Powered HRMS API",
    description="Next-generation HRMS with autonomous resume screening, AI voice "
    "screening, an RAG HR assistant, and AI performance insights.",
    version="1.0.0",
    lifespan=lifespan,
)

# Auth is via Bearer tokens (not cookies), so a wildcard origin is safe: set
# CORS_ORIGINS="*" in production to allow the Vercel frontend without hard-coding
# its URL. With "*" we must disable credentials (browsers forbid the combo).
_origins = settings.cors_origin_list
_allow_all = "*" in _origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all else _origins,
    allow_credentials=not _allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)


for r in (auth, employees, attendance, payroll, performance, recruitment, ai, dashboard):
    app.include_router(r.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {
        "status": "ok",
        "ai_enabled": gemini_client.is_available(),
        "version": "1.0.0",
    }


@app.get("/", tags=["meta"])
def root() -> dict:
    return {"name": "FWC AI-Powered HRMS", "docs": "/docs", "health": "/health"}
