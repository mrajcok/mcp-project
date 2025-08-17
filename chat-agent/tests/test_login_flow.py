# ABOUT-ME: Tests for login flow helpers and app integration hooks.
# ABOUT-ME: Validates successful/failed login processing and username display behavior.

from pathlib import Path
from textwrap import dedent

from src.db import init_db, User
from src.app import _process_login


def write_config(tmp_path: Path, users: list[str]) -> str:
    cfg = dedent(
        f"""
        authorized_users:
        {''.join(f'  - {u}\n' for u in users)}
        admin_users: []
        mcp_servers: []
        confirmation_required_tools: []
        """
    ).strip() + "\n"
    p = tmp_path / "config.yaml"
    p.write_text(cfg, encoding="utf-8")
    return str(p)


def test_process_login_success(tmp_path):
    # Arrange: DB and config
    _, SessionLocal = init_db("sqlite:///:memory:")
    config_path = write_config(tmp_path, ["alice"])  # only alice authorized

    def binder(u: str, p: str) -> bool:
        return u == "alice" and p == "secret"

    # Act
    result = _process_login(
        username="alice",
        password="secret",
        ip="127.0.0.1",
        config_path=config_path,
        binder=binder,
        session_local=SessionLocal,
    )

    # Assert
    assert result is not None
    assert result["username"] == "alice"
    assert isinstance(result.get("id"), int)
    # User exists in DB
    with SessionLocal() as s:
        user = s.query(User).filter_by(username="alice").first()
        assert user is not None
        assert user.id == result["id"]


def test_process_login_failure_wrong_password(tmp_path):
    _, SessionLocal = init_db("sqlite:///:memory:")
    config_path = write_config(tmp_path, ["alice"])  # only alice authorized

    def binder(u: str, p: str) -> bool:
        return False  # always fail

    result = _process_login(
        username="alice",
        password="bad",
        ip="127.0.0.1",
        config_path=config_path,
        binder=binder,
        session_local=SessionLocal,
    )
    assert result is None


def test_process_login_failure_unauthorized_user(tmp_path):
    _, SessionLocal = init_db("sqlite:///:memory:")
    config_path = write_config(tmp_path, ["bob"])  # alice not authorized

    def binder(u: str, p: str) -> bool:
        return True

    result = _process_login(
        username="alice",
        password="secret",
        ip="127.0.0.1",
        config_path=config_path,
        binder=binder,
        session_local=SessionLocal,
    )
    assert result is None
