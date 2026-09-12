"""Engine/session factory helpers.

Kept database-agnostic: the only SQLite-specific bit is the connection
arguments needed to share a connection across threads (required for
FastAPI's TestClient and for an in-memory/temp-file DB in tests), which is
driver configuration rather than SQL.
"""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str) -> Engine:
    connect_args: dict = {}
    extra: dict = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if ":memory:" in database_url:
            extra["poolclass"] = StaticPool
    return create_engine(database_url, connect_args=connect_args, **extra)


def make_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
