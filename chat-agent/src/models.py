# ABOUT-ME: Central SQLAlchemy models for the chat agent app.
# ABOUT-ME: Defines Base and core tables (users) used by the database layer.

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class AwareDateTime(TypeDecorator):
    """A DateTime that guarantees timezone-aware UTC datetimes on read/write.

    SQLite loses tzinfo; this decorator re-attaches UTC on result processing.
    """
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Fields from spec.md (nullable by default until features implemented)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(AwareDateTime(), nullable=True)
    lockout_until: Mapped[Optional[datetime]] = mapped_column(AwareDateTime(), nullable=True)
    token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    token_issued_at: Mapped[Optional[datetime]] = mapped_column(AwareDateTime(), nullable=True)
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(AwareDateTime(), nullable=True)


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ip: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(AwareDateTime(), nullable=True)
