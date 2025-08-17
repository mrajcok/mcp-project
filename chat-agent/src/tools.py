# ABOUT-ME: Tool parsing and invocation recording helpers.
# ABOUT-ME: Provides parse_tool_tags() and process_tool_invocation() with confirmation logic and truncation.

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Callable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from .config import load_config
from .models import ToolInvocation


_TOOL_TAG_RE = re.compile(r"#([a-zA-Z0-9_]+)")


def parse_tool_tags(text: str) -> list[str]:
    return _TOOL_TAG_RE.findall(text)


CallTool = Callable[[str, str, str], str]


def process_tool_invocation(
    *,
    tool_name: str,
    server_name: str,
    bearer_token: str,
    was_explicit: bool,
    is_llm_request: bool,
    user_confirmed: Optional[bool],
    chat_message_id: int,
    config_path,
    call_tool: CallTool,
    SessionLocal: sessionmaker[Session],
    max_output: int = 100_000,
) -> Optional[str]:
    """
    Decide if a tool should be run and record its invocation. Returns truncated output on success or None.
    """
    cfg = load_config(config_path)

    need_confirmation = (
        (tool_name in cfg.confirmation_required_tools)
        and is_llm_request
        and not was_explicit
    )

    allowed = True
    if need_confirmation:
        allowed = bool(user_confirmed)

    now = datetime.now(timezone.utc)

    with SessionLocal() as session:
        inv = ToolInvocation(
            chat_message_id=chat_message_id,
            tool_name=tool_name,
            server_name=server_name,
            was_explicit=was_explicit,
            user_confirmed=bool(user_confirmed) if user_confirmed is not None else False,
            invocation_time=now,
        )
        session.add(inv)
        session.commit()
        session.refresh(inv)

        if not allowed:
            inv.success = False
            inv.output_text = None
            inv.error_message = "User confirmation required and not granted"
            session.commit()
            return None

        # Call tool and truncate output
        try:
            output = call_tool(tool_name, server_name, bearer_token)
            truncated = output[:max_output] if output and len(output) > max_output else output
            inv.success = True
            inv.output_text = truncated
            inv.error_message = None
            session.commit()
            return truncated
        except Exception as e:  # defensive, not expected in tests
            inv.success = False
            inv.error_message = str(e)
            session.commit()
            return None
