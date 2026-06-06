"""SQLAlchemy engine, session factory and declarative base."""
import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

is_sqlite = settings.database_url.startswith("sqlite")
# check_same_thread is only needed for SQLite; harmless to compute conditionally.
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine_kwargs: dict = {"connect_args": connect_args, "pool_pre_ping": True}

# On serverless (Vercel sets VERCEL=1) we must NOT keep a persistent connection
# pool: many short-lived function instances would each hold idle connections and
# quickly exhaust a small Postgres connection cap (e.g. Aiven's 20). NullPool
# opens one connection per request and closes it immediately afterwards.
if os.getenv("VERCEL") and not is_sqlite:
    engine_kwargs["poolclass"] = NullPool

engine = create_engine(settings.database_url, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
