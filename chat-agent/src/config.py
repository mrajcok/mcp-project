# ABOUT-ME: YAML configuration loader and validation using Pydantic models.
# ABOUT-ME: Provides a load_config(path) function that returns a strongly typed Config model.

from __future__ import annotations

from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, Field, ValidationError


class Config(BaseModel):
    authorized_users: List[str] = Field(default_factory=list)
    admin_users: List[str] = Field(default_factory=list)
    mcp_servers: List[str] = Field(default_factory=list)
    confirmation_required_tools: List[str] = Field(default_factory=list)


def load_config(path: str | Path) -> Config:
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"Config file not found: {path}")

    try:
        import textwrap
        raw = path.read_text(encoding="utf-8")
        # Be tolerant of leading indentation in YAML files written from indented triple-quoted strings
        dedented = textwrap.dedent(raw)
        try:
            data = yaml.safe_load(dedented) or {}
        except yaml.YAMLError:
            # Fallback: aggressively strip leading spaces from all lines and try again
            normalized = "\n".join(line.lstrip() for line in dedented.splitlines())
            data = yaml.safe_load(normalized) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}") from e

    # Ensure required keys exist explicitly to raise clear messages
    required = [
        "authorized_users",
        "admin_users",
        "mcp_servers",
        "confirmation_required_tools",
    ]
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(
            "Missing required config keys: " + ", ".join(missing)
        )

    try:
        return Config(**data)
    except ValidationError as e:
        # Wrap pydantic errors in ValueError for simpler surface
        raise ValueError(str(e)) from e
