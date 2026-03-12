from pathlib import Path
from typing import Any

import yaml

REQUIRED_KEYS = {"source", "target", "transformations", "validation"}


class ConfigError(Exception):
    """Raised when pipeline config is invalid."""

    pass


def load_config(config_path: str) -> dict[str, Any]:
    """Load and validate YAML pipeline config."""
    path = Path(config_path)

    if not path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ConfigError("Config must be a YAML mapping (dict)")

    missing = REQUIRED_KEYS - config.keys()
    if missing:
        raise ConfigError(f"Missing required config keys: {missing}")

    return config


def get_rename_map(config: dict) -> dict[str, str]:
    """Extract column rename mappings from config."""
    return config.get("transformations", {}).get("rename_columns", {})


def get_filters(config: dict) -> list[dict]:
    """Extract filter rules from config."""
    return config.get("transformations", {}).get("filters", [])


def get_type_casts(config: dict) -> dict[str, str]:
    """Extract type cast rules from config."""
    return config.get("transformations", {}).get("type_casts", {})
