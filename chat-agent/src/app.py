# ABOUT-ME: Minimal Dash app skeleton with routing placeholders and nav layout.
# ABOUT-ME: Provides a factory to build the app with an AgentManager instance.

from __future__ import annotations

import dash
from dash import Dash, dcc, html, Input, Output, State
from typing import Optional, Tuple, List, Callable
from pathlib import Path
from sqlalchemy.orm import Session, sessionmaker

from .agent import AgentManager
from .chat_store import create_session as cs_create_session, add_message as cs_add_message, get_messages as cs_get_messages
from .auth import authenticate_user_with_lockout
from .config import load_config
from .models import User
from flask import session as flask_session, has_request_context, request


def _render_servers_list(statuses: dict[str, dict]) -> list:
    # Helper to render servers list items from status dict
    items = []
    for name, status in statuses.items():
        items.append(
            html.Li(
                [
                    html.Span(name, className="server-name"),
                    html.Span(status.get("status", "not_connected"), className=f"status {status.get('status', 'not_connected')}"),
                    html.Ul([html.Li(t) for t in status.get("tools", [])], className="tools-list"),
                ]
            )
        )
    return items


def _run_agent_sync(agent_mgr: AgentManager, text: str) -> str:
    # Minimal extraction: rely on pydantic-ai AgentRunResult.output
    if not text:
        return ""
    agent = getattr(agent_mgr, "llm", None)
    if not agent:
        return ""
    try:
        result = agent.run_sync(text)
    except Exception:
        return ""
    out = getattr(result, "output", None)
    return out.strip() if isinstance(out, str) else (str(out).strip() if out is not None else "")


def _render_messages(messages: List) -> List:
    items: List = []
    for m in messages:
        user_text = getattr(m, "message_text", "")
        ai_text = getattr(m, "agent_response_text", "")
        items.append(html.Div([html.Strong("You:"), html.Span(user_text or "")] ))
        items.append(html.Div([html.Strong("AI:"), html.Span((ai_text or ""))] ))
    return items


def _persist_and_render(
    agent_mgr: AgentManager,
    session_local: Optional[sessionmaker[Session]],
    user_id: int,
    session_id: Optional[int],
    text: str,
) -> Tuple[Optional[int], List]:
    # If no DB provided, return ephemeral render only
    ai = _run_agent_sync(agent_mgr, text or "")
    if session_local is None:
        return session_id, [html.Div([html.Strong("You:"), html.Span(text or "")]), html.Div([html.Strong("AI:"), html.Span(ai)])]

    # Ensure session exists
    sid = session_id or cs_create_session(user_id, session_local)
    # Persist message
    cs_add_message(sid, user_id, text or "", ai or "", session_local)
    # Load all messages and render
    msgs = cs_get_messages(sid, session_local)
    return sid, _render_messages(msgs)


def _process_login(
    username: str,
    password: str,
    ip: str,
    config_path: str,
    binder,
    session_local: sessionmaker[Session],
) -> Optional[dict]:
    """
    Validate credentials via authenticate_user_with_lockout and return a user dict on success.

    Returns {"id": int, "username": str} on success, otherwise None.
    """
    ok = authenticate_user_with_lockout(
        username=username,
        password=password,
        ip=ip,
        config_path=config_path,
        binder=binder,
        SessionLocal=session_local,
    )
    if not ok:
        return None
    # Determine admin from config and fetch user
    cfg = load_config(config_path)
    is_admin = username in (cfg.admin_users or [])
    with session_local() as s:
        user = s.query(User).filter_by(username=username).first()
        if not user:
            return None
        # Keep DB flag synchronized with config
        desired = bool(is_admin)
        if bool(user.is_admin) != desired:
            user.is_admin = desired
            s.commit()
        return {"id": user.id, "username": user.username, "is_admin": desired}


def _process_logout() -> bool:
    """Clear server-side session user; return True if cleared."""
    if not has_request_context():
        return False
    try:
        if "user" in flask_session:
            flask_session.pop("user", None)
        return True
    except Exception:
        return False


def create_app(
    agent_mgr: AgentManager,
    session_local: Optional[sessionmaker[Session]] = None,
    user_id: int = 1,
    auth_config_path: Optional[str] = None,
    auth_binder: Optional[Callable[..., bool]] = None,
) -> Dash:
    def _build_login_layout() -> html.Div:
        # Simple navbar so users always see the app name
        navbar = html.Nav(
            [
                html.Img(src="/assets/logo.svg", className="brand-logo", alt="Chat Agent logo"),
                html.Span("Chat Agent", className="brand"),
                html.Button(html.Span("\ud83c\udf19", id="theme-icon"), id="theme-toggle", className="icon-button", title="Toggle theme"),
            ],
            className="navbar",
        )

        # Login page: navbar at top, card centered inside a content container
        return html.Div(
            [
                navbar,
                dcc.Location(id="url"),
                html.Div(
                    html.Div(
                        [
                            html.H2("Sign in", className="login-title"),
                            html.Div(
                                [
                                    dcc.Input(id="login-username", type="text", placeholder="Username", className="input"),
                                    dcc.Input(id="login-password", type="password", placeholder="Password", className="input"),
                                    html.Div(id="login-error", className="login-error"),
                                    html.Button("Login", id="login-submit", n_clicks=0, className="btn-primary"),
                                ],
                                className="login-form",
                            ),
                        ],
                        className="login-card",
                    ),
                    className="login-card-container",
                ),
                dcc.Store(id="theme-store", data="light", storage_type="local"),
            ],
            id="app-root",
            className="login-page theme-light",
        )

    def _build_main_layout() -> html.Div:
        navbar = html.Nav(
            [
                html.Img(src="/assets/logo.svg", className="brand-logo", alt="Chat Agent logo"),
                html.Span("Chat Agent", className="brand"),
                html.A("History", href="/history"),
                (html.A("Admin", href="/admin") if (flask_session.get("user", {}).get("is_admin")) else html.Span("", className="hidden")),
                html.Span(flask_session.get("user", {}).get("username", "Guest"), id="username-display", className="username"),
                html.A("Logout", href="#", id="logout-link"),
                html.Button(html.Span("\ud83c\udf19", id="theme-icon"), id="theme-toggle", className="icon-button", title="Toggle theme"),
            ],
            className="navbar",
        )

        # Left panel listing MCP servers with status and tools
        initial_statuses = agent_mgr.get_server_status_and_tools()
        servers_panel = html.Div(
            [
                html.H3("MCP Servers"),
                html.Ul(_render_servers_list(initial_statuses)),
                dcc.Store(id="servers-store", data=initial_statuses),
                dcc.Interval(id="servers-interval", interval=10_000, n_intervals=0),
            ],
            id="servers-panel",
            className="servers-panel",
        )

        # Main chat layout
        chat_layout = html.Div(
            [
                html.Div(
                    [
                        dcc.Input(id="chat-input", type="text", placeholder="Type a message...", maxLength=2000, className="input"),
                        html.Button("Send", id="chat-send"),
                    ],
                    className="chat-input-row",
                ),
                html.Div(id="chat-messages", className="chat-messages"),
                dcc.Store(id="chat-session-store", data=None),
            ],
            className="chat-main",
        )

        return html.Div(
            [
                navbar,
                html.Div([servers_panel, chat_layout, dcc.Location(id="main-url")], className="content"),
                dcc.Store(id="theme-store", data="light", storage_type="local"),
            ],
            id="app-root",
            className="app-shell theme-light",
        )

    def serve_layout():
        # Gate by server-side session user; if no request context, show login page
        if not has_request_context():
            return _build_login_layout()
        user = flask_session.get("user")
        if user and isinstance(user, dict) and user.get("id"):
            # Role-based restriction: non-admin cannot access /admin
            try:
                path = request.path or "/"
            except Exception:
                path = "/"
            if path.startswith("/admin") and not user.get("is_admin"):
                return html.Div([dcc.Location(id="main-url"), html.H2("Forbidden")])
            return _build_main_layout()
        return _build_login_layout()

    # Ensure Dash loads the global assets directory (chat-agent/assets)
    assets_path = Path(__file__).resolve().parent.parent / "assets"
    app = dash.Dash(__name__, suppress_callback_exceptions=True, assets_folder=str(assets_path))
    app.layout = serve_layout

    # Periodically refresh server status
    @app.callback(
        Output("servers-store", "data"),
        Input("servers-interval", "n_intervals"),
        prevent_initial_call=False,
    )
    def _refresh_servers(_n):
        return agent_mgr.get_server_status_and_tools()

    # Re-render servers panel list when store updates
    @app.callback(
        Output("servers-panel", "children"),
        Input("servers-store", "data"),
    )
    def _render_servers(data):
        return [html.H3("MCP Servers"), html.Ul(_render_servers_list(data)) , dcc.Store(id="servers-store", data=data), dcc.Interval(id="servers-interval", interval=10_000, n_intervals=0)]

    # Chat send: append AI response into messages area (simple replace for now)
    @app.callback(
        Output("chat-messages", "children"),
        Output("chat-session-store", "data"),
        Output("username-display", "children"),
        Input("chat-send", "n_clicks"),
        State("chat-input", "value"),
        State("chat-session-store", "data"),
        prevent_initial_call=True,
    )
    def _on_send(_clicks, text, sid):
        user = flask_session.get("user") or {}
        active_user_id = user.get("id") or user_id
        active_username = user.get("username") or "Guest"
        new_sid, children = _persist_and_render(agent_mgr, session_local, active_user_id, sid, text or "")
        return children, new_sid, active_username

    # Login handler: updates auth store and username display
    @app.callback(
        Output("url", "href"),
        Output("login-error", "children"),
        Input("login-submit", "n_clicks"),
        State("login-username", "value"),
        State("login-password", "value"),
        prevent_initial_call=True,
    )
    def _on_login(_n, u, p):
        if not (auth_config_path and auth_binder and session_local):
            return dash.no_update, "Login not configured"
        username = (u or "").strip()
        password = p or ""
        if not username or not password:
            return dash.no_update, "Enter username and password"
        result = _process_login(
            username=username,
            password=password,
            ip="127.0.0.1",
            config_path=auth_config_path,
            binder=auth_binder,
            session_local=session_local,
        )
        if not result:
            return dash.no_update, "Invalid credentials"
        # Set server-side session and refresh
        flask_session["user"] = result
        return "/", ""

    # Logout handler: clears session and redirects to login
    @app.callback(
        Output("main-url", "href"),
        Input("logout-link", "n_clicks"),
        prevent_initial_call=True,
    )
    def _on_logout(_n):
        _process_logout()
        return "/"

    # Toggle theme: switch store between light/dark
    @app.callback(
        Output("theme-store", "data"),
        Input("theme-toggle", "n_clicks"),
        State("theme-store", "data"),
        prevent_initial_call=True,
    )
    def _toggle_theme(_n, theme):
        t = theme if theme in ("light", "dark") else "light"
        return "dark" if t == "light" else "light"

    # Apply theme to root class and icon glyph based on store value
    @app.callback(
        Output("app-root", "className"),
        Output("theme-icon", "children"),
        Input("theme-store", "data"),
        prevent_initial_call=False,
    )
    def _apply_theme(theme):
        t = theme if theme in ("light", "dark") else "light"
        base = "app-shell" if (flask_session.get("user") and isinstance(flask_session.get("user"), dict)) else "login-page"
        icon = "\ud83c\udf19" if t == "light" else "\u2600\ufe0f"
        return f"{base} theme-{t}", icon

    return app
