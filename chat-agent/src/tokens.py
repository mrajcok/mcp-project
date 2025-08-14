# ABOUT-ME: Bearer token issuance helpers for users.
# ABOUT-ME: Provides issue_token(user_id, SessionLocal) to generate and persist tokens and validation helpers.

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from .models import User


def issue_token(user_id: int, SessionLocal: sessionmaker[Session]) -> str:
    """
    Generate an opaque bearer token for the given user, invalidating any previous token.

    Returns the new token string.
    Raises ValueError if the user does not exist.
    """
    token = secrets.token_hex(32)
    now = datetime.now(timezone.utc)

    with SessionLocal() as session:
        user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if user is None:
            raise ValueError(f"User not found: {user_id}")
        user.token = token
        user.token_issued_at = now
        user.last_activity_at = None  # reset activity on new token
        session.commit()

    return token


def validate_and_touch_token(
    token: str,
    SessionLocal: sessionmaker[Session],
    *,
    idle_hours: int = 12,
    now: Optional[datetime] = None,
) -> bool:
    """
    Validate a bearer token with idle timeout. If valid, update last_activity_at.

    Returns True if token is valid and not idle-expired; False otherwise.
    """
    now = now or datetime.now(timezone.utc)
    with SessionLocal() as session:
        user = session.execute(select(User).where(User.token == token)).scalar_one_or_none()
        if not user:
            return False

        last = user.last_activity_at or user.token_issued_at
        if not last:
            # No baseline; consider invalid for safety
            return False

        if now - last > timedelta(hours=idle_hours):
            return False

        user.last_activity_at = now
        session.commit()
        return True
