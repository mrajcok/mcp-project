# ABOUT-ME: Tests for tool parsing, confirmation flow, and invocation recording.
# ABOUT-ME: Ensures explicit tags bypass confirmation, dangerous tools require approval, and outputs are truncated.

from datetime import datetime, timezone

from sqlalchemy import select

from src.db import init_db
from src.models import User, ChatSession, ChatMessage, ToolInvocation
from src.tools import parse_tool_tags, process_tool_invocation


def test_parse_tool_tags_extracts_names():
    text = "Please run #read_text_file and maybe #delete_file next."
    assert parse_tool_tags(text) == ["read_text_file", "delete_file"]


def test_explicit_tool_invocation_stores_truncated_output_and_success(tmp_path):
    engine, SessionLocal = init_db("sqlite:///:memory:")

    # Minimal config with no confirmation needed for read_text_file
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        """
        authorized_users: [alice]
        admin_users: []
        mcp_servers: [fileserver]
        confirmation_required_tools: [delete_file]
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    # Setup user/session/message
    with SessionLocal() as session:
        u = User(username="alice")
        session.add(u)
        session.commit()
        session.refresh(u)
        s = ChatSession(user_id=u.id, description="d")
        session.add(s)
        session.commit()
        session.refresh(s)
        m = ChatMessage(chat_session_id=s.id, user_id=u.id, message_text="msg", agent_response_text=None)
        session.add(m)
        session.commit()
        session.refresh(m)
        msg_id = m.id

    # Mock tool call returns large output (>100k)
    calls = {"count": 0}

    def call_fn(tool: str, server: str, bearer: str) -> str:
        calls["count"] += 1
        return "x" * 150_000

    out = process_tool_invocation(
        tool_name="read_text_file",
        server_name="fileserver",
        bearer_token="tok",
        was_explicit=True,
        is_llm_request=False,
        user_confirmed=None,
        chat_message_id=msg_id,
        config_path=cfg,
        call_tool=call_fn,
        SessionLocal=SessionLocal,
    )

    assert out is not None
    assert calls["count"] == 1

    with SessionLocal() as session:
        inv = session.execute(select(ToolInvocation)).scalars().one()
        assert inv.was_explicit is True
        assert inv.user_confirmed is False  # stored as False when None for explicit
        assert inv.success is True
        assert len(inv.output_text) == 100_000


def test_llm_requested_dangerous_tool_requires_confirmation_and_skips_when_denied(tmp_path):
    engine, SessionLocal = init_db("sqlite:///:memory:")

    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        """
        authorized_users: [bob]
        admin_users: []
        mcp_servers: [fileserver]
        confirmation_required_tools: [delete_file]
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    # Setup user/session/message
    with SessionLocal() as session:
        u = User(username="bob")
        session.add(u)
        session.commit()
        session.refresh(u)
        s = ChatSession(user_id=u.id, description="d")
        session.add(s)
        session.commit()
        session.refresh(s)
        m = ChatMessage(chat_session_id=s.id, user_id=u.id, message_text="msg", agent_response_text=None)
        session.add(m)
        session.commit()
        session.refresh(m)
        msg_id = m.id

    calls = {"count": 0}

    def call_fn(tool: str, server: str, bearer: str) -> str:
        calls["count"] += 1
        return "ok"

    out = process_tool_invocation(
        tool_name="delete_file",
        server_name="fileserver",
        bearer_token="tok",
        was_explicit=False,
        is_llm_request=True,
        user_confirmed=False,
        chat_message_id=msg_id,
        config_path=cfg,
        call_tool=call_fn,
        SessionLocal=SessionLocal,
    )

    assert out is None  # not executed
    assert calls["count"] == 0

    with SessionLocal() as session:
        inv = session.execute(select(ToolInvocation)).scalars().one()
        assert inv.was_explicit is False
        assert inv.user_confirmed is False
        assert inv.success is False
        assert inv.output_text is None
        assert inv.error_message is not None
