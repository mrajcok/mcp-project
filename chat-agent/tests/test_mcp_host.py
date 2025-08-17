# ABOUT-ME: Tests for MCPHost client construction with SSE transport and headers.
# ABOUT-ME: Monkeypatches FastMCP classes to avoid real network/deps.

from src.mcp_host import MCPHost


class _DummyClient:
    def __init__(self, config):
        # Emulate FastMCP config-based client by storing the provided config
        self.config = config


def test_mcp_host_builds_clients_with_sse(monkeypatch):
    import src.mcp_host as m

    monkeypatch.setattr(m, "_get_fastmcp_client_class", lambda: _DummyClient)

    host = MCPHost(["https://srv-a/mcp", "http://srv-b/mcp", "./local.py"])  # only http(s) kept
    clients = host.create_clients("tok-123", extra_headers={"X-App": "chat-agent"})

    assert set(clients.keys()) == {"https://srv-a/mcp", "http://srv-b/mcp"}
    for k, c in clients.items():
        assert isinstance(c, _DummyClient)
        # Validate config structure
        assert list(c.config["mcpServers"].keys()) == [k]
        entry = c.config["mcpServers"][k]
        assert entry["transport"] == "http"
        assert entry["url"] == k
        assert entry["headers"]["Authorization"] == "Bearer tok-123"
        assert entry["headers"]["X-App"] == "chat-agent"
