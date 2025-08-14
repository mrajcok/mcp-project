# ABOUT-ME: Tests for idle timeout behavior on bearer tokens.
# ABOUT-ME: Validates last_activity_at updates and 12h expiration.

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from src.db import init_db
from src.models import User
from src.tokens import issue_token, validate_and_touch_token


def test_validate_updates_last_activity_and_expires_after_12_hours():
    engine, SessionLocal = init_db("sqlite:///:memory:")

    # Setup user and token
    with SessionLocal() as session:
        u = User(username="dave")
        session.add(u)
        session.commit()
        session.refresh(u)
        user_id = u.id

    now = datetime.now(timezone.utc)
    tok = issue_token(user_id, SessionLocal)

    # First use should be valid and update last_activity_at
    ok = validate_and_touch_token(tok, SessionLocal, now=now)
    assert ok is True
    with SessionLocal() as session:
        u = session.execute(select(User).where(User.id == user_id)).scalar_one()
        assert u.last_activity_at is not None
        assert u.last_activity_at >= now

    # Make it stale (13 hours)
    stale = now - timedelta(hours=13)
    with SessionLocal() as session:
        u = session.execute(select(User).where(User.id == user_id)).scalar_one()
        u.last_activity_at = stale
        session.commit()

    ok = validate_and_touch_token(tok, SessionLocal, now=now)
    assert ok is False


def test_validate_uses_token_issued_when_no_activity():
    engine, SessionLocal = init_db("sqlite:///:memory:")

    with SessionLocal() as session:
        u = User(username="erin")
        session.add(u)
        session.commit()
        session.refresh(u)
        user_id = u.id

    tok = issue_token(user_id, SessionLocal)

    # Force token issuance in the past and no last_activity
    past = datetime.now(timezone.utc) - timedelta(hours=13)
    with SessionLocal() as session:
        u = session.execute(select(User).where(User.id == user_id)).scalar_one()
        u.token_issued_at = past
        u.last_activity_at = None
        session.commit()

    ok = validate_and_touch_token(tok, SessionLocal, now=datetime.now(timezone.utc))
    assert ok is False
