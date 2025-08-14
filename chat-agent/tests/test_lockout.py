# ABOUT-ME: Tests for lockout after repeated failed authentications by username+IP.
# ABOUT-ME: Ensures lockout_until is set after 3 failures and a 4th attempt is blocked.

from datetime import datetime, timezone

from sqlalchemy import select

from src.db import init_db
from src.models import User
from src.auth import authenticate_user_with_lockout


def test_lockout_after_three_failures_blocks_fourth_and_sets_field(tmp_path):
    # Setup DB and config
    engine, SessionLocal = init_db("sqlite:///:memory:")

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
        authorized_users: [bob]
        admin_users: []
        mcp_servers: [fileserver]
        confirmation_required_tools: [delete_file]
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    calls = {"count": 0}

    def binder(_u: str, _p: str) -> bool:
        calls["count"] += 1
        return False  # always fail

    ip = "1.2.3.4"

    # 3 failed attempts
    for _ in range(3):
        ok = authenticate_user_with_lockout("bob", "bad", ip, cfg_path, binder, SessionLocal)
        assert ok is False

    # lockout_until should be set in DB
    with SessionLocal() as session:
        user = session.execute(select(User).where(User.username == "bob")).scalar_one()
        assert user.lockout_until is not None
        assert user.lockout_until.tzinfo is not None  # stored as aware
        assert user.lockout_until > datetime.now(timezone.utc)

    # 4th attempt should be blocked without invoking binder
    calls_before = calls["count"]
    ok = authenticate_user_with_lockout("bob", "bad", ip, cfg_path, binder, SessionLocal)
    assert ok is False
    assert calls["count"] == calls_before  # binder not called when locked
