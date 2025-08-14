# ABOUT-ME: Tests for the SQLAlchemy User model CRUD and nullable fields.
# ABOUT-ME: Ensures mapping to users table with fields from spec and basic persistence.

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from src.db import init_db
from src.models import User


def test_user_model_crud_and_nullable_fields():
    engine, SessionLocal = init_db("sqlite:///:memory:")

    # Create user and persist
    with SessionLocal() as session:
        u = User(username="bob", is_admin=True)
        session.add(u)
        session.commit()
        session.refresh(u)
        assert u.id is not None

        # Defaults / nullable fields
        assert u.lockout_until is None
        assert u.token is None
        assert u.last_activity_at is None

        # Update some fields
        now = datetime.now(timezone.utc)
        u.last_login_at = now
        u.token = "abc"
        u.token_issued_at = now - timedelta(hours=1)
        u.last_activity_at = now
        session.commit()

    # Query back and verify
    with SessionLocal() as session:
        got = session.execute(select(User).where(User.username == "bob")).scalar_one()
        assert got.is_admin is True
        assert got.token == "abc"
        assert got.last_login_at is not None
        assert got.token_issued_at is not None
        assert got.last_activity_at is not None
