# ABOUT-ME: Pytest configuration to make the local src/ importable without extra plugins.
# ABOUT-ME: Prepends the chat-agent/src path to sys.path for test imports.

import os
import sys
from pathlib import Path

# Resolve path to chat-agent/src relative to this file
_SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))
