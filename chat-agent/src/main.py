# ABOUT-ME: Minimal entrypoint for the chat agent CLI.
# ABOUT-ME: Parses commands and wires up the AgentManager and app lifecycle.

import os
import sys

from .agent import AgentManager
from .app import create_app
from .config import Config


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return 0
    cmd = argv[0]
    if cmd == "run":
        # Wire up agent lifecycle: config -> agent -> llm + mcp -> (app)
        # For now, use a minimal inline config; later load from file.
        cfg: dict[str, list[str]] = {
            "authorized_users": [],
            "admin_users": [],
            "mcp_servers": [
                # Example: "https://localhost:3001/mcp"
            ],
            "confirmation_required_tools": [],
        }
        _ = Config(**cfg)  # validate shape early

        mgr = AgentManager(config=cfg)
        # Initialize LLM once; read key/model from env if provided.
        mgr.initialize_llm(
            api_key=os.environ.get("OPENAI_API_KEY"),
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            system_prompt=os.environ.get("SYSTEM_PROMPT"),
        )

        # Optionally build MCP clients if token present.
        token = os.environ.get("MCP_BEARER_TOKEN")
        if token:
            mgr.build_mcp_clients(token, extra_headers={"X-App": "chat-agent"})

        # Create the Dash app (server start omitted to keep CLI fast for tests)
        _ = create_app(mgr)
        return 0
    if cmd == "test-model":
        # Placeholder: later we'll ping the model provider
        print("ok")
        return 0
    if cmd == "--version":
        from . import __version__
        print(__version__)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
