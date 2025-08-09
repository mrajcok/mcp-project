# ABOUT-ME: Pytest configuration for test suite including warning filters
# ABOUT-ME: Programmatically filters third-party warnings we cannot control

import warnings
import pytest
import os
import sys
from datetime import datetime, timezone
import asyncio


def pytest_configure(config):
    """Configure pytest to filter out specific third-party warnings"""
    
    # Keep third-party noise minimal; do not suppress our own warnings
    # Note: We intentionally do not suppress websockets.legacy deprecation warnings per guidance
    # Minimal suppression: urllib3 InsecureRequestWarning for self-signed certs in tests
    try:
        import urllib3.exceptions
        warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)
    except ImportError:
        pass


# --- Lightweight progress logging to detect hangs ---
_current_test = {"nodeid": None}
_progress_log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "test-progress.log"))


def _log_progress(event: str, nodeid: str) -> None:
    """Write progress events to a log file; optionally echo to stdout if enabled."""
    try:
        ts = datetime.now(timezone.utc).isoformat()
        line = f"[{ts}] {event}: {nodeid}\n"
        with open(_progress_log_path, "a", encoding="utf-8") as f:
            f.write(line)
        if os.environ.get("TEST_PROGRESS_STDOUT") == "1":
            # Keep output minimal and flush so it's visible immediately
            sys.stdout.write(line)
            sys.stdout.flush()
    except Exception:
        # Never fail tests due to logging issues
        pass


def pytest_runtest_logstart(nodeid, location):  # type: ignore[override]
    _current_test["nodeid"] = nodeid
    _log_progress("START", nodeid)


def pytest_runtest_logfinish(nodeid, location):  # type: ignore[override]
    _log_progress("FINISH", nodeid)
    if _current_test.get("nodeid") == nodeid:
        _current_test["nodeid"] = None


# Ensure each test gets a clean, fully-closed event loop to avoid teardown warnings
@pytest.fixture(scope="function")
def event_loop():
    """Create a fresh event loop per test, set it current, and close it cleanly after use."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        try:
            # Cancel any pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            # Final tiny tick to let transports close
            loop.run_until_complete(asyncio.sleep(0))
        finally:
            loop.close()
            # Clear current loop to avoid lingering references
            try:
                asyncio.set_event_loop(None)  # type: ignore[arg-type]
            except Exception:
                pass
