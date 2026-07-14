from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def _build_engine() -> Engine:
    return create_engine(
        settings.db_url,
        # SQLite needs this when used across threads (FastAPI threadpool, scheduler, etc.)
        connect_args={"check_same_thread": False},
        echo=False,
        future=True,
    )


engine: Engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for all models."""

    pass


def init_db() -> None:
    """Create tables if they don't exist.

    Used as a convenience for first-run. For schema evolution, use Alembic
    migrations (see backend/alembic/). When the first migration is generated,
    this call can be replaced with `alembic upgrade head` at startup.
    """
    # Import here so models are registered on Base.metadata before create_all runs.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
