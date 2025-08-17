# ABOUT-ME: Central SQLAlchemy models for the chat agent app.
# ABOUT-ME: Defines Base and core tables (users) used by the database layer.

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
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


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_activity_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    agent_response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))

    session: Mapped[ChatSession] = relationship(back_populates="messages")


class ToolInvocation(Base):
    __tablename__ = "tool_invocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_message_id: Mapped[int] = mapped_column(ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)
    server_name: Mapped[str] = mapped_column(String(255), nullable=False)
    was_explicit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    invocation_time: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False, default=lambda: datetime.now(timezone.utc))
    output_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
