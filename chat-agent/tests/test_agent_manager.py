# ABOUT-ME: Tests for AgentManager LLM initialization and MCP client construction.
# ABOUT-ME: Ensures initialize_llm is idempotent and MCP headers are set correctly.

from types import ModuleType

from src.agent import AgentManager


class _DummyAgent:
    def __init__(self, model_obj, system_prompt=None):
        self.model_obj = model_obj
        self.system_prompt = system_prompt


class _DummyOpenAIModel:
    def __init__(self, model: str):
        self.model = model


class _DummyClient:
    def __init__(self, config):
        self.config = config


def test_initialize_llm_idempotent(monkeypatch):
    # Create fake modules to avoid importing real pydantic_ai/openai
    fake_pai = ModuleType("pydantic_ai")
    fake_pai.Agent = _DummyAgent  # type: ignore[attr-defined]
    fake_openai_mod = ModuleType("pydantic_ai.models.openai")
    fake_openai_mod.OpenAIModel = _DummyOpenAIModel  # type: ignore[attr-defined]

    monkeypatch.setitem(__import__("sys").modules, "pydantic_ai", fake_pai)
    monkeypatch.setitem(__import__("sys").modules, "pydantic_ai.models.openai", fake_openai_mod)

    mgr = AgentManager(config={"mcp_servers": []})

    mgr.initialize_llm(api_key="key-1", model="model-a", system_prompt="sp-a")
    first = mgr.llm
    assert first is not None
    assert isinstance(first, _DummyAgent)
    assert first.model_obj.model == "model-a"
    assert first.system_prompt == "sp-a"

    # Second call should be a no-op
    mgr.initialize_llm(api_key="key-2", model="model-b", system_prompt="sp-b")
    assert mgr.llm is first


def test_build_mcp_clients_sets_headers(monkeypatch):
    import src.mcp_host as m

    monkeypatch.setattr(m, "_get_fastmcp_client_class", lambda: _DummyClient)

    cfg = {"mcp_servers": ["https://srv-a/mcp", "not-a-url", "http://srv-b/mcp"]}
    mgr = AgentManager(config=cfg)
    clients = mgr.build_mcp_clients("tok-xyz", extra_headers={"X-App": "chat-agent"})

    assert set(clients.keys()) == {"https://srv-a/mcp", "http://srv-b/mcp"}
    for url, client in clients.items():
        entry = client.config["mcpServers"][url]
        assert entry["transport"] == "http"
        assert entry["url"] == url
        assert entry["headers"]["Authorization"] == "Bearer tok-xyz"
        assert entry["headers"]["X-App"] == "chat-agent"

def test_get_server_status_and_tools_inside_loop(monkeypatch):
    # Simulate FastMCP client with async list_tools
    class FakeClient:
        async def list_tools(self):
            return [{"name": "read_file"}, {"name": "list_dir"}]

    mgr = AgentManager(config={"mcp_servers": ["https://s1"]})
    mgr.mcp_clients = {"https://s1": FakeClient()}

    # Call inside an event loop context to exercise thread offload path
    import asyncio

    def _call_sync():
        return mgr.get_server_status_and_tools()

    result = asyncio.run(asyncio.to_thread(_call_sync))
    assert result["https://s1"]["status"] == "connected"
    assert "read_file" in result["https://s1"]["tools"]
