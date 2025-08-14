# ABOUT-ME: Tests for bearer token issuance and invalidation behavior.
# ABOUT-ME: Ensures issue_token generates unique tokens and updates DB fields.

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from src.db import init_db
from src.models import User
from src.tokens import issue_token


def test_issue_token_generates_and_overrides_previous_token():
    engine, SessionLocal = init_db("sqlite:///:memory:")

    # Create user
    with SessionLocal() as session:
        u = User(username="carol")
        session.add(u)
        session.commit()
        session.refresh(u)
        user_id = u.id

    # First token
    t1 = issue_token(user_id, SessionLocal)
    assert isinstance(t1, str) and len(t1) >= 64

    with SessionLocal() as session:
        u = session.execute(select(User).where(User.id == user_id)).scalar_one()
        assert u.token == t1
        assert u.token_issued_at is not None
        first_issued_at = u.token_issued_at

    # Second token overrides the first
    t2 = issue_token(user_id, SessionLocal)
    assert t2 != t1

    with SessionLocal() as session:
        u = session.execute(select(User).where(User.id == user_id)).scalar_one()
        assert u.token == t2
        assert u.token_issued_at is not None
        assert u.token_issued_at >= first_issued_at


def test_issue_token_for_missing_user_raises_value_error():
    engine, SessionLocal = init_db("sqlite:///:memory:")

    with pytest.raises(ValueError):
        issue_token(9999, SessionLocal)
