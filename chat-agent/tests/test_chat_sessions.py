# ABOUT-ME: Tests for chat sessions and messages CRUD and purge logic.
# ABOUT-ME: Ensures creation, listing, deletion, and 30-day purge behavior.

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from src.db import init_db
from src.models import User, ChatSession, ChatMessage
from src.chat_store import (
    create_session,
    add_message,
    get_messages,
    delete_session,
    purge_old_sessions,
)


def test_chat_session_crud_and_messages():
    engine, SessionLocal = init_db("sqlite:///:memory:")

    # Create user
    with SessionLocal() as session:
        u = User(username="zoe")
        session.add(u)
        session.commit()
        session.refresh(u)
        user_id = u.id

    # Create session
    sid = create_session(user_id, SessionLocal, description="test session")
    assert isinstance(sid, int)

    # Add messages
    m1 = add_message(sid, user_id, "hello", None, SessionLocal)
    m2 = add_message(sid, user_id, "how are you?", "fine", SessionLocal)
    assert m1 != m2

    # Retrieve messages in order
    msgs = get_messages(sid, SessionLocal)
    assert [m.message_text for m in msgs] == ["hello", "how are you?"]

    # Delete session cascades messages
    delete_session(sid, SessionLocal)
    with SessionLocal() as session:
        exists = session.execute(select(ChatSession).where(ChatSession.id == sid)).scalar_one_or_none()
        assert exists is None
        msgs_left = session.execute(select(ChatMessage)).scalars().all()
        assert msgs_left == []


def test_purge_old_sessions_removes_data_older_than_30_days():
    engine, SessionLocal = init_db("sqlite:///:memory:")
    now = datetime.now(timezone.utc)

    with SessionLocal() as session:
        u = User(username="yuki")
        session.add(u)
        session.commit()
        session.refresh(u)
        user_id = u.id

    # Create two sessions: one recent, one old
    fresh_id = create_session(user_id, SessionLocal, description="fresh")
    old_id = create_session(user_id, SessionLocal, description="old")

    add_message(fresh_id, user_id, "hi", None, SessionLocal)
    add_message(old_id, user_id, "stale", None, SessionLocal)

    # Manually backdate old session's last_activity to 31 days ago
    with SessionLocal() as session:
        old = session.execute(select(ChatSession).where(ChatSession.id == old_id)).scalar_one()
        old.last_activity_at = now - timedelta(days=31)
        session.commit()

    # Purge
    purge_old_sessions(SessionLocal, retention_days=30, now=now)

    with SessionLocal() as session:
        fresh = session.execute(select(ChatSession).where(ChatSession.id == fresh_id)).scalar_one_or_none()
        old = session.execute(select(ChatSession).where(ChatSession.id == old_id)).scalar_one_or_none()
        assert fresh is not None
        assert old is None
        msgs = session.execute(select(ChatMessage)).scalars().all()
        # Only messages for fresh session should remain
        assert len(msgs) == 1
