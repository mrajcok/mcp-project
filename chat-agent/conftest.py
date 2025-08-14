# ABOUT-ME: Root-level pytest configuration ensuring src/ is importable during test collection.
# ABOUT-ME: Adds the chat-agent/src path to sys.path before tests import modules.

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
