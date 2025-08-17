# ABOUT-ME: Helpers for chat sessions and messages CRUD and purge.
# ABOUT-ME: Provides simple functions to create sessions, add messages, list messages, delete sessions, and purge old sessions.

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from .models import ChatSession, ChatMessage


def create_session(user_id: int, SessionLocal: sessionmaker[Session], *, description: Optional[str] = None) -> int:
    now = datetime.now(timezone.utc)
    with SessionLocal() as session:
        s = ChatSession(user_id=user_id, description=description or None, created_at=now, last_activity_at=now)
        session.add(s)
        session.commit()
        session.refresh(s)
        return s.id


def add_message(
    chat_session_id: int,
    user_id: int,
    message_text: str,
    agent_response_text: Optional[str],
    SessionLocal: sessionmaker[Session],
) -> int:
    now = datetime.now(timezone.utc)
    with SessionLocal() as session:
        m = ChatMessage(
            chat_session_id=chat_session_id,
            user_id=user_id,
            message_text=message_text,
            agent_response_text=agent_response_text,
            created_at=now,
        )
        session.add(m)
        # bump session last activity
        s = session.execute(select(ChatSession).where(ChatSession.id == chat_session_id)).scalar_one()
        s.last_activity_at = now
        session.commit()
        session.refresh(m)
        return m.id


def get_messages(chat_session_id: int, SessionLocal: sessionmaker[Session]) -> List[ChatMessage]:
    with SessionLocal() as session:
        return (
            session.execute(
                select(ChatMessage).where(ChatMessage.chat_session_id == chat_session_id).order_by(ChatMessage.created_at.asc())
            ).scalars().all()
        )


def delete_session(chat_session_id: int, SessionLocal: sessionmaker[Session]) -> None:
    with SessionLocal() as session:
        s = session.execute(select(ChatSession).where(ChatSession.id == chat_session_id)).scalar_one_or_none()
        if s is None:
            return
        session.delete(s)
        session.commit()


def purge_old_sessions(SessionLocal: sessionmaker[Session], *, retention_days: int = 30, now: Optional[datetime] = None) -> int:
    """
    Delete chat sessions (and cascading messages) whose last_activity_at is older than retention_days.
    Returns number of sessions deleted.
    """
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)
    with SessionLocal() as session:
        old_sessions = (
            session.execute(select(ChatSession).where(ChatSession.last_activity_at < cutoff)).scalars().all()
        )
        count = len(old_sessions)
        for s in old_sessions:
            session.delete(s)
        session.commit()
        return count
