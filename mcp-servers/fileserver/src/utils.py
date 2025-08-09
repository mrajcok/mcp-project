# ABOUT-ME: Utility functions and configuration management
# ABOUT-ME: Loads base config.yaml and merges optional override YAML files

import yaml
import os
from pathlib import Path
from typing import Dict, Any


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge override into base and return base."""
    for key, val in (override or {}).items():
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(val, dict)
        ):
            _deep_merge(base[key], val)
        else:
            base[key] = val
    return base


def get_config() -> Dict[str, Any]:
    """Load configuration from YAML with optional override file.
    Precedence: CONFIG_OVERRIDE file path > config.local.yaml (if present) > base config.yaml.
    """
    # Paths
    base_dir = Path(__file__).parent
    config_path = base_dir / "config.yaml"

    # Load base configuration
    with open(config_path, "r") as f:
        config = yaml.safe_load(f) or {}

    # Determine override file
    override_path_str = os.environ.get("CONFIG_OVERRIDE")
    override_path: Path | None = None
    if override_path_str:
        override_path = Path(override_path_str)
    else:
        candidate = base_dir / "config.local.yaml"
        if candidate.exists():
            override_path = candidate

    # Merge override if present
    if override_path and override_path.exists():
        with open(override_path, "r") as f:
            override_cfg = yaml.safe_load(f) or {}
        if isinstance(override_cfg, dict):
            _deep_merge(config, override_cfg)

    return config
