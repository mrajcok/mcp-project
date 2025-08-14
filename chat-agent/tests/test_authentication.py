# ABOUT-ME: Tests for LDAP-based authenticate_user with config-driven authorization.
# ABOUT-ME: Uses an injected binder to avoid real LDAP and checks authorized_users logic.

from pathlib import Path
import textwrap

from src.config import load_config
from src.auth import authenticate_user


def _write_cfg(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
    return p


def test_auth_user_not_in_config_returns_false(tmp_path: Path):
    cfg_path = _write_cfg(
        tmp_path,
        """
        authorized_users: [alice]
        admin_users: []
        mcp_servers: [fileserver]
        confirmation_required_tools: [delete_file]
        """,
    )

    def binder(_u: str, _p: str) -> bool:
        # Even if LDAP would accept, not authorized in config should fail
        return True

    ok = authenticate_user("bob", "secret", cfg_path, binder)
    assert ok is False


def test_auth_invalid_credentials_returns_false(tmp_path: Path):
    cfg_path = _write_cfg(
        tmp_path,
        """
        authorized_users: [alice, bob]
        admin_users: []
        mcp_servers: [fileserver]
        confirmation_required_tools: [delete_file]
        """,
    )

    def binder(_u: str, _p: str) -> bool:
        return False  # invalid creds

    ok = authenticate_user("bob", "badpass", cfg_path, binder)
    assert ok is False


def test_auth_valid_and_authorized_returns_true(tmp_path: Path):
    cfg_path = _write_cfg(
        tmp_path,
        """
        authorized_users: [alice, bob]
        admin_users: [alice]
        mcp_servers: [fileserver]
        confirmation_required_tools: [delete_file]
        """,
    )

    def binder(u: str, p: str) -> bool:
        return u == "bob" and p == "goodpass"

    ok = authenticate_user("bob", "goodpass", cfg_path, binder)
    assert ok is True
