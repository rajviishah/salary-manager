from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings

_BACKEND_DIR = Path(__file__).resolve().parent.parent
(_BACKEND_DIR / "data").mkdir(parents=True, exist_ok=True)


def _create_engine(database_url: str) -> Engine:
    connect_args = {}
    kwargs: dict = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        # StaticPool shares one connection so sqlite :memory: is visible
        # to every session (default pooling would give each an empty DB).
        if ":memory:" in database_url or database_url.rstrip("/") == "sqlite://":
            kwargs["poolclass"] = StaticPool
    return create_engine(database_url, connect_args=connect_args, **kwargs)


engine = _create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def configure_database(database_url: str) -> None:
    """Replace the process-wide engine. Tests use this for isolated SQLite.

    Production still defaults to ``backend/data/salary.db`` via settings.
    """
    global engine, SessionLocal
    engine.dispose()
    engine = _create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
