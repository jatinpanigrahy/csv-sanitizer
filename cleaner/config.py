"""Configuration management module for the CSV Sanitizer pipeline.

Provides functionality to load user configuration from a YAML file, validate
its structure, and merge it with sensible system defaults via recursive deep merging.
"""

import copy
from pathlib import Path
from typing import Any

import yaml

# Master default configuration ensuring zero-failure execution when user config is omitted or incomplete.
DEFAULTS: dict[str, Any] = {
    "columns": {
        "name": "name",
        "phone": "phone",
        "email": "email",
        "date": "date",
    },
    "phone": {
        "default_country": "US",
        "output_format": "E164",
    },
    "deduplication": {
        "auto_merge_threshold": 90,
        "flag_threshold": 70,
    },
    "output": {
        "date_format": "%Y-%m-%d",
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge an override dictionary into a base dictionary.

    Args:
        base: The foundational dictionary providing fallback defaults.
        override: The user-supplied dictionary containing custom overrides.

    Returns:
        A new dictionary containing base values overlaid with user overrides.
    """
    result = copy.deepcopy(base)

    for key, value in override.items():
        # If both base and override have nested dictionaries, merge recursively
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            # Overwrite or insert non-dict or leaf values directly
            result[key] = value

    return result


def load(config_path: str = "config.yaml") -> dict[str, Any]:
    """Load configuration from a YAML file and merge with system defaults.

    If the specified file does not exist or is empty, the complete set of
    system defaults is returned without raising an error.

    Args:
        config_path: Path to the YAML configuration file. Defaults to "config.yaml".

    Returns:
        A dictionary containing the fully resolved configuration.
    """
    path = Path(config_path)

    # Missing configuration file triggers clean fallback to default settings
    if not path.exists():
        return copy.deepcopy(DEFAULTS)

    with open(path, encoding="utf-8") as f:
        user_config = yaml.safe_load(f)

    # Empty files or null YAML payloads resolve to system defaults
    if not user_config:
        return copy.deepcopy(DEFAULTS)

    return _deep_merge(DEFAULTS, user_config)
