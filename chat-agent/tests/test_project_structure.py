# ABOUT-ME: Tests that the chat-agent project skeleton exists and is minimally valid.
# ABOUT-ME: Ensures presence of source dir, entrypoint, and dependency manifest with expected libs.

from pathlib import Path


def test_project_structure_exists():
    base = Path(__file__).resolve().parents[1]  # chat-agent directory

    # 1) src/ source directory exists (mirrors fileserver layout)
    src_dir = base / "src"
    assert src_dir.is_dir(), f"Missing source directory: {src_dir}"

    # 2) Minimal entrypoint/module exists under src/
    has_init = (src_dir / "__init__.py").is_file()
    has_main = (src_dir / "main.py").is_file()
    assert has_init or has_main, "Expected __init__.py or main.py in src/"

    # 3) requirements.txt or pyproject.toml lists known packages
    req = base / "requirements.txt"
    pjt = base / "pyproject.toml"
    assert req.is_file() or pjt.is_file(), "Missing requirements.txt or pyproject.toml"

    content = (req if req.is_file() else pjt).read_text().lower()
    # Look for at least one known dependency name (dash or flask)
    assert ("dash" in content) or ("flask" in content), "Expected 'dash' or 'flask' in dependencies"
