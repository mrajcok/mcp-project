# ABOUT-ME: Basic tests for Dash app structure and nav presence.
# ABOUT-ME: Verifies the layout and servers panel render expected elements.

from src.app import create_app
from src.agent import AgentManager
from dash import html
from src.db import init_db, User
from sqlalchemy.orm import Session, sessionmaker
from flask import session as flask_session


def test_app_layout_contains_nav_and_sections():
    config = {"mcp_servers": ["fileserver", "vectorstore"]}
    mgr = AgentManager(config=config)
    app = create_app(mgr)
    # By default (no session), the login page should render
    login_layout = app.layout() if callable(app.layout) else app.layout
    # Find login input by id in the layout tree
    def find_by_id(node, target_id):
        if getattr(node, "id", None) == target_id:
            return True
        children = getattr(node, "children", None)
        # If children is a list/tuple, walk each; if single component, recurse into it
        if isinstance(children, (list, tuple)):
            for c in children:
                if find_by_id(c, target_id):
                    return True
        elif children is not None:
            # single child component
            if find_by_id(children, target_id):
                return True
        return False

    assert find_by_id(login_layout, "login-username")

    # With a logged-in session, main layout should render
    app.server.secret_key = "test"
    with app.server.test_request_context("/"):
        flask_session["user"] = {"id": 1, "username": "alice"}
        layout = app.layout() if callable(app.layout) else app.layout
        # Navbar elements
        assert any(getattr(child, "children", None) == "Chat Agent" for child in layout.children[0].children)
        assert isinstance(layout.children[1].children[0].children, list)  # servers list exists
        # Chat input present
        chat_main = layout.children[1].children[1]
        input_children = chat_main.children[0].children
        ids = [getattr(c, "id", None) for c in input_children]
        assert "chat-input" in ids


def test_servers_panel_shows_status_and_tools(monkeypatch):
    config = {"mcp_servers": ["fileserver", "vectorstore"]}
    mgr = AgentManager(config=config)

    def fake_statuses():
        return {
            "fileserver": {"status": "connected", "tools": ["read_file", "list_dir"]},
            "vectorstore": {"status": "not_connected", "tools": []},
        }

    monkeypatch.setattr(mgr, "get_server_status_and_tools", fake_statuses)
    app = create_app(mgr)
    app.server.secret_key = "test"
    with app.server.test_request_context("/"):
        flask_session["user"] = {"id": 1, "username": "alice"}
        layout = app.layout() if callable(app.layout) else app.layout
        servers_panel = layout.children[1].children[0]
    # Ensure we rendered two servers
    li_items = servers_panel.children[1].children
    assert len(li_items) == 2
    # Check first server content includes status and tools
    first = li_items[0]
    text_parts = []
    for c in first.children:
        if hasattr(c, "children") and isinstance(c.children, str):
            text_parts.append(c.children)
    combined = " ".join(text_parts)
    assert "fileserver" in combined
    # Expect a status span with class 'status connected'
    status_span = first.children[1]
    assert "connected" in getattr(status_span, "children", "")
    assert "status connected" in " ".join(getattr(status_span, "className", "").split())
    # Tools list should contain 'read_file'
    tools_ul = first.children[2]
    tool_texts = [li.children for li in tools_ul.children]
    assert "read_file" in tool_texts


def test_callbacks_registered_and_render_updates(monkeypatch):
    config = {"mcp_servers": ["fileserver"]}
    mgr = AgentManager(config=config)

    # Fake status changes
    calls = {"n": 0}
    def fake_statuses():
        calls["n"] += 1
        return {"fileserver": {"status": "connected" if calls["n"] > 1 else "not_connected", "tools": ["t1"]}}

    monkeypatch.setattr(mgr, "get_server_status_and_tools", fake_statuses)
    app = create_app(mgr)
    app.server.secret_key = "test"
    with app.server.test_request_context("/"):
        flask_session["user"] = {"id": 1, "username": "alice"}
        layout = app.layout() if callable(app.layout) else app.layout
        servers_panel = layout.children[1].children[0]
    # interval and store exist
    children = servers_panel.children
    tags = [type(c).__name__ for c in children]
    assert any(getattr(c, "id", None) == "servers-store" for c in children)
    assert any(getattr(c, "id", None) == "servers-interval" for c in children)

    # Simulate the render callback body directly (unit-level)
    from src.app import _render_servers_list
    rendered = _render_servers_list(fake_statuses())
    assert isinstance(rendered, list)
    assert any(isinstance(li, html.Li) for li in rendered)


def test_chat_persistence_roundtrip(monkeypatch):
    # Set up in-memory DB
    _, SessionLocal = init_db("sqlite:///:memory:")
    mgr = AgentManager(config={"mcp_servers": []})
    # Create a user to satisfy FK
    with SessionLocal() as s:
        u = User(username="tester")
        s.add(u)
        s.commit()
        s.refresh(u)
        user_id = u.id

    class FakeResult:
        output = "AI says hi"

    class FakeAgent:
        def run_sync(self, prompt: str):
            return FakeResult()

    monkeypatch.setattr(AgentManager, "initialize_llm", lambda self, **kw: None)
    mgr.llm = FakeAgent()

    app = create_app(mgr, session_local=SessionLocal, user_id=user_id)
    layout = app.layout
    # Simulate sending a message via internal helper by invoking the callback body
    # Note: importing from module to access helper is acceptable for unit-level tests
    from src.app import _persist_and_render
    sid, children = _persist_and_render(mgr, SessionLocal, user_id, None, "hello")
    assert sid is not None
    # persist a second message
    sid2, children2 = _persist_and_render(mgr, SessionLocal, user_id, sid, "second")
    assert sid2 == sid
    # Messages should render at least 4 divs (You/AI pairs x2)
    assert len(children2) >= 4
