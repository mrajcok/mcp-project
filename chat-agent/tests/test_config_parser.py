# ABOUT-ME: Tests for YAML configuration loading and validation using a Pydantic model.
# ABOUT-ME: Ensures required keys exist and valid configs are parsed correctly.

from pathlib import Path
import textwrap
import pytest

from src.config import load_config


REQUIRED_KEYS = [
    "authorized_users",
    "admin_users",
    "mcp_servers",
    "confirmation_required_tools",
]


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
    return p


@pytest.mark.parametrize("missing", REQUIRED_KEYS)
def test_load_config_missing_required_key_raises_value_error(tmp_path: Path, missing: str):
    # Minimal valid config, then drop one key
    data = {
        "authorized_users": ["alice", "bob"],
        "admin_users": ["alice"],
        "mcp_servers": ["fileserver"],
        "confirmation_required_tools": ["delete_file"],
    }
    data.pop(missing)

    # Build YAML string without importing yaml in tests
    lines = [f"{k}: {v}" for k, v in data.items()]
    cfg_path = _write(tmp_path, "\n".join(lines))

    with pytest.raises(ValueError) as exc:
        load_config(cfg_path)
    assert missing in str(exc.value)


def test_load_config_success_returns_model(tmp_path: Path):
    cfg_path = _write(
        tmp_path,
        """
        authorized_users: [alice, bob]
        admin_users: [alice]
        mcp_servers: [fileserver, modelserver]
        confirmation_required_tools: [delete_file, run_shell]
        """,
    )

    cfg = load_config(cfg_path)

    # Validate types & content
    assert cfg.authorized_users == ["alice", "bob"]
    assert cfg.admin_users == ["alice"]
    assert cfg.mcp_servers == ["fileserver", "modelserver"]
    assert cfg.confirmation_required_tools == ["delete_file", "run_shell"]
