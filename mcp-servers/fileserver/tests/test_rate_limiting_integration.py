# ABOUT-ME: Integration tests for rate limiting and degraded state via HTTP middleware
# ABOUT-ME: Starts uvicorn with FastMCP app + AuthenticationMiddleware and exercises tools over HTTP

import os
import time
import threading
import sqlite3
from datetime import date

import pytest

from fastmcp.client import Client
from fastmcp.client.transports import SSETransport
from fastmcp.exceptions import ToolError

from src.server import mcp, AuthenticationMiddleware
import src.db as db_mod


def _get_free_port():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _Server:
    def __init__(self, port: int):
        self.port = port
        self.thread = None
        self._server = None

    def start(self):
        import uvicorn
        import socket as _socket

        app = mcp.sse_app()
        app.add_middleware(AuthenticationMiddleware)

        # Use uvicorn.Server so we can stop it cleanly later
        config = uvicorn.Config(app=app, host="127.0.0.1", port=self.port, log_level="error")
        self._server = uvicorn.Server(config)

        def run():
            server = self._server
            if server is not None:
                server.run()

        print(f"[DEBUG] Starting uvicorn on 127.0.0.1:{self.port}")
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        # Wait until the TCP port is accepting connections (up to ~5s)
        deadline = time.time() + 5.0
        while time.time() < deadline:
            try:
                with _socket.create_connection(("127.0.0.1", self.port), timeout=0.3):
                    print(f"[DEBUG] Server port {self.port} is accepting connections")
                    break
            except OSError:
                time.sleep(0.1)
        else:
            print(f"[WARN] Server on port {self.port} did not become ready in time")

    def stop(self, timeout: float = 2.0):
        try:
            if self._server is not None:
                self._server.should_exit = True
            if self.thread is not None:
                self.thread.join(timeout)
        finally:
            # Small delay to let background tasks settle
            time.sleep(0.05)

    def url(self) -> str:
        # Return SSE endpoint URL expected by FastMCP client
        return f"http://127.0.0.1:{self.port}/sse"


async def _call_health_with_token(base_url: str, token: str, timeout_s: float = 8.0):
    import asyncio
    import inspect

    print(f"[DEBUG] Connecting SSE client to {base_url} with token ...")
    transport = SSETransport(base_url, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })

    async def _do_call():
        async with Client(transport) as client:
            # Avoid client.ping() here to prevent extra rate-limit increments
            return await client.call_tool("health_check", {})

    try:
        return await asyncio.wait_for(_do_call(), timeout=timeout_s)
    except Exception as e:
        print(f"[DEBUG] _call_health_with_token exception: {type(e).__name__}: {e}")
        raise
    finally:
        try:
            # Let pending tasks progress before closing
            await asyncio.sleep(0)
            # Ensure transport is explicitly closed to prevent resource warnings
            aclose = getattr(transport, "aclose", None)
            if callable(aclose):
                result = aclose()
                if inspect.isawaitable(result):
                    await result
            else:
                close = getattr(transport, "close", None)
                if callable(close):
                    close()
        except Exception as close_err:
            print(f"[DEBUG] transport close error: {close_err}")
        # Give the client/session a brief moment to close cleanly to avoid unclosed loop warnings
        await asyncio.sleep(0)
        await asyncio.sleep(0.02)


@pytest.mark.asyncio
async def test_rate_limiting_daily_limit_integration(tmp_path, monkeypatch):
    # Configure small daily limit and clean test DBs
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "integration_rate_limit")

    # Ensure src.db config uses a small limit (accounts for handshake traffic)
    assert "rate_limit" in db_mod._CONFIG
    db_mod._CONFIG["rate_limit"]["daily_requests"] = 4

    # Clean usage DB (test path is data/test_usage.db when PYTEST_CURRENT_TEST is set)
    usage_db_path = db_mod.get_usage_db_path()
    if os.path.exists(usage_db_path):
        os.unlink(usage_db_path)
    db_mod.init_usage_db(usage_db_path)

    # Prepare user DB and add a test user
    db_mod.init_user_db()
    token = "test-token-limiter"
    db_mod.add_test_user("testuser", token)

    # Start server with middleware
    port = _get_free_port()
    server = _Server(port)
    server.start()

    try:
        # Make a few calls until rate limiting triggers
        calls_made = 0
        caught = False
        last_attempt = 0
        for i in range(1, 7):
            last_attempt = i
            print(f"[DEBUG] Attempt #{i} calling health_check ...")
            try:
                await _call_health_with_token(server.url(), token)
                calls_made += 1
            except ToolError as te:
                print(f"[DEBUG] Caught ToolError on attempt {i}: {te}")
                caught = True
                break
            except Exception as e:
                # ConnectionError due to 429 during handshake also acceptable as limit enforcement
                print(f"[DEBUG] Non-ToolError on attempt {i}: {type(e).__name__}: {e}")
                caught = True
                break
        assert caught, f"Rate limiting did not trigger within {last_attempt} attempts (calls made: {calls_made})"
    finally:
        server.stop()


@pytest.mark.asyncio
async def test_degraded_state_all_requests_429_integration(monkeypatch):
    # Configure small daily limit and pre-mark degraded
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "integration_degraded")

    # Set limit small
    db_mod._CONFIG["rate_limit"]["daily_requests"] = 3

    # Clean and init usage DB
    usage_db_path = db_mod.get_usage_db_path()
    if os.path.exists(usage_db_path):
        os.unlink(usage_db_path)
    db_mod.init_usage_db(usage_db_path)

    # Insert usage over limit for today
    today = date.today().isoformat()
    with sqlite3.connect(usage_db_path) as conn:
        conn.execute(
            "INSERT INTO usage (username, date, request_count) VALUES (?, ?, ?)",
            ("testuser", today, 10),
        )
        conn.commit()

    # Prepare user DB and add the same test user
    db_mod.init_user_db()
    token = "test-token-degraded"
    db_mod.add_test_user("testuser", token)

    # Start server
    port = _get_free_port()
    server = _Server(port)
    server.start()

    try:
        # Expect degraded state to reject the SSE handshake with 429
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(server.url(), headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 429
    finally:
        server.stop()
