# ABOUT-ME: MCP host that creates FastMCP Clients over HTTP (streamable) for configured servers.
# ABOUT-ME: Builds Client from config dicts with Authorization headers; avoids legacy SSE.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional
import importlib


def _get_fastmcp_client_class():
    """Dynamically import FastMCP Client class."""
    client_mod = importlib.import_module("fastmcp")
    return getattr(client_mod, "Client")


@dataclass
class MCPHost:
    """Build per-server FastMCP Clients using streaming HTTP.

    config_servers may be a list of URLs; non-HTTP entries are ignored.
    """

    config_servers: Iterable[str]

    def create_clients(
        self, bearer_token: str, *, extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        Client = _get_fastmcp_client_class()
        clients: Dict[str, Any] = {}
        headers = {"Authorization": f"Bearer {bearer_token}"}
        if extra_headers:
            headers.update(extra_headers)

        for url in self.config_servers:
            if isinstance(url, str) and url.startswith(("http://", "https://")):
                # Build a single-server config using HTTP transport with headers
                config = {
                    "mcpServers": {
                        url: {
                            "transport": "http",
                            "url": url,
                            "headers": headers,
                        }
                    }
                }
                clients[url] = Client(config)
        return clients
