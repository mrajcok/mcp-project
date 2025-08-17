# ABOUT-ME: Entrypoint to run the Dash chat-agent web server.
# ABOUT-ME: Creates AgentManager, optional DB, and starts the Dash server.

from __future__ import annotations

import os
from typing import Optional

from src.agent import AgentManager
from src.app import create_app
from src.db import init_db


def main():
    # Initialize DB (creates sqlite file by default). Tests use in-memory; here we use a persistent file.
    engine, SessionLocal = init_db()

    # Minimal AgentManager setup; you can customize via env vars or edit this file.
    cfg = {"mcp_servers": []}
    mgr = AgentManager(config=cfg)

    # Optionally initialize LLM if OPENAI_API_KEY provided
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        mgr.initialize_llm(api_key=api_key, model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))

    # Auth config path (optional). If not provided or binder is None, login will be disabled.
    auth_config = os.environ.get("AUTH_CONFIG_PATH")
    # Binder is intentionally left None here; pass a binder callable if you wire LDAP.
    auth_binder = None

    app = create_app(
        mgr,
        session_local=SessionLocal,
        auth_config_path=auth_config,
        auth_binder=auth_binder,
    )

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8050"))
    debug = bool(os.environ.get("DEBUG", "1"))

    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
