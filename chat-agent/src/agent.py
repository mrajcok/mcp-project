# ABOUT-ME: Central agent manager for LLM and MCP server awareness.
# ABOUT-ME: Creates one long-lived manager that can list servers and hold an LLM agent.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .mcp_host import MCPHost


@dataclass
class AgentManager:
    """Holds references to LLM agent and configured MCP servers.

    Keeps a single place to initialize/connect later (13B+). For now, just stores
    config and exposes list_servers().
    """

    config: Dict[str, Any]
    llm: Optional[Any] = None  # Pydantic AI Agent instance (created once)
    mcp_clients: Dict[str, Any] | None = None

    def list_servers(self) -> List[str]:
        servers = self.config.get("mcp_servers") or []
        return [s if isinstance(s, str) else str(s) for s in servers]

    def initialize_llm(self, *, api_key: str | None = None, model: str = "gpt-4o-mini", system_prompt: str | None = None) -> None:
        """Create a single Pydantic AI Agent for the app lifetime."""
        if self.llm is not None:
            return
        # NOTE: These imports must be local due to pydantic_ai packaging quirks.
        # Importing pydantic_ai at module scope can cause ImportError or version issues
        # in some environments (see test failures if moved to top). This is a known
        # workaround for libraries that do dynamic import/version logic at runtime.
        from pydantic_ai import Agent
        from pydantic_ai.models.openai import OpenAIModel
        sp = system_prompt or (
            "You are a helpful assistant. If you recommend using a tool, include a JSON line {\"recommended_tool\": \"tool_name\"}."
        )
        if api_key:
            os.environ.setdefault("OPENAI_API_KEY", api_key)
        model_obj = OpenAIModel(model)
        self.llm = Agent(model_obj, system_prompt=sp)

    def build_mcp_clients(self, bearer_token: str, *, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        host = MCPHost(self.list_servers())
        self.mcp_clients = host.create_clients(bearer_token, extra_headers=extra_headers)
        return self.mcp_clients

    def get_server_status_and_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return status and available tool names for each configured MCP server.

        Uses FastMCP 2.0 Client API directly (list_tools).
        Shape: { server: {"status": "connected"|"not_connected", "tools": [str, ...] } }
        """

        def _run_coro_blocking(coro):
            """Run an async coroutine to completion from sync code.

            - If no loop is running, use asyncio.run.
            - If a loop is running (e.g., inside a Dash callback using asyncio), offload to a background thread
              that creates its own event loop and runs the coroutine.
            """
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                # No running loop
                return asyncio.run(coro)
            # Running loop detected: offload
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(lambda: asyncio.run(coro))
                return fut.result(timeout=5)

        def _list_tool_names(client: Any) -> list[str]:
            try:
                list_tools = getattr(client, "list_tools")
                coro = list_tools()
            except Exception:
                return []
            try:
                tools = _run_coro_blocking(coro)
            except Exception:
                return []

            names: list[str] = []
            for t in tools or []:
                if isinstance(t, str):
                    names.append(t)
                elif isinstance(t, dict):
                    name = t.get("name")
                    if name:
                        names.append(str(name))
                else:
                    name = getattr(t, "name", None)
                    if name:
                        names.append(str(name))
            return names
        statuses: Dict[str, Dict[str, Any]] = {}
        servers = self.list_servers()
        for server in servers:
            info: Dict[str, Any] = {"status": "not_connected", "tools": []}
            if self.mcp_clients and server in self.mcp_clients:
                info["status"] = "connected"
                client = self.mcp_clients[server]
                info["tools"] = _list_tool_names(client)
            statuses[server] = info
        return statuses
