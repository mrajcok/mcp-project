# ABOUT-ME: Minimal SQLAlchemy setup for initializing the database schema and sessions.
# ABOUT-ME: Exposes init_db() and re-exports the User model backed by SQLAlchemy.

from __future__ import annotations

import logging
from typing import Tuple

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, User  # re-export for compatibility

logger = logging.getLogger(__name__)


def init_db(database_url: str = "sqlite:///chat-agent.db") -> Tuple[Engine, sessionmaker[Session]]:
    """
    Initialize the database engine, create tables, and return (engine, SessionLocal).

    Parameters:
        database_url: SQLAlchemy database URL. Use "sqlite:///:memory:" for tests.

    Returns:
        (engine, SessionLocal) where SessionLocal is a sessionmaker factory.
    """
    logger.debug("Initializing database", extra={"database_url": database_url})

    engine = create_engine(database_url, echo=False, future=True)

    # Ensure SQLite enforces foreign key constraints (needed for ON DELETE CASCADE)
    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-redef]
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
            except Exception:
                # Best-effort; tests will reveal if this fails
                pass

    # Create all tables
    Base.metadata.create_all(engine)

    SessionLocal: sessionmaker[Session] = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, future=True
    )
    return engine, SessionLocal
