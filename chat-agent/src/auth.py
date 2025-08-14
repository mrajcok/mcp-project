# ABOUT-ME: Authentication helpers for LDAP and config-based authorization.
# ABOUT-ME: Provides authenticate_user() and authenticate_user_with_lockout() with username+IP lockout.

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from .config import Config, load_config
from .models import User, LoginAttempt

Binder = Callable[[str, str], bool]


def authenticate_user(username: str, password: str, config_path: str | Path, binder: Binder) -> bool:
    """
    Authenticate a user using an LDAP binder and the YAML config.

    Steps:
    - Load config from the provided config_path.
    - If username not in authorized_users, return False.
    - Otherwise, call binder(username, password) and return its result.

    Note: Lockout, tokens, and logging are handled in later steps.
    """
    cfg: Config = load_config(config_path)

    if username not in cfg.authorized_users:
        return False

    # Delegate to LDAP binder (in tests, a mock is passed)
    return bool(binder(username, password))


def _get_or_create_user(session: Session, username: str) -> User:
    user = session.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if user is None:
        user = User(username=username)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def authenticate_user_with_lockout(
    username: str,
    password: str,
    ip: str,
    config_path: str | Path,
    binder: Binder,
    SessionLocal: sessionmaker[Session],
) -> bool:
    """
    Authenticate with lockout after 3 failed attempts for username+IP.

    - If user is not authorized (per config), return False.
    - If lockout_until > now, return False without calling binder.
    - On failed binder result, increment a per-user counter via last_activity_at token fields are not used here; after 3 failures set lockout_until = now + 15m.
    - On success, reset lockout (lockout_until=None) and return True.
    """
    cfg: Config = load_config(config_path)
    if username not in cfg.authorized_users:
        return False

    now = datetime.now(timezone.utc)

    with SessionLocal() as session:
        user = _get_or_create_user(session, username)

        # Check existing lockout
        if user.lockout_until and user.lockout_until > now:
            return False

        # Fetch or create login attempt record for username+ip
        attempt = (
            session.execute(
                select(LoginAttempt).where(
                    LoginAttempt.username == username, LoginAttempt.ip == ip
                )
            ).scalar_one_or_none()
        )
        if attempt is None:
            attempt = LoginAttempt(username=username, ip=ip, count=0, last_attempt_at=now)
            session.add(attempt)
            session.commit()
            session.refresh(attempt)

        # Try binder only if not locked
        ok = binder(username, password)
        if ok:
            # Reset lockout and attempts
            user.lockout_until = None
            attempt.count = 0
            attempt.last_attempt_at = now
            session.commit()
            return True
        # Failed attempt: increment and maybe lock
        attempt.count = (attempt.count or 0) + 1
        attempt.last_attempt_at = now
        if attempt.count >= 3:
            user.lockout_until = now + timedelta(minutes=15)
        session.commit()
        return False
