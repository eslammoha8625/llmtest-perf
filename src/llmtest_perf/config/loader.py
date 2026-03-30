"""Configuration file loading and validation."""

from pathlib import Path
from typing import Union

import yaml
from pydantic import ValidationError

from llmtest_perf.config.models import PerfTestConfig


class ConfigError(Exception):
    """Error loading or validating configuration."""

    pass


def load_config(config_path: Union[str, Path]) -> PerfTestConfig:
    """
    Load and validate a performance test configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Validated PerfTestConfig instance

    Raises:
        ConfigError: If file cannot be read or config is invalid
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML syntax: {e}")
    except Exception as e:
        raise ConfigError(f"Error reading configuration file: {e}")

    if not isinstance(raw_config, dict):
        raise ConfigError("Configuration must be a YAML dictionary")

    try:
        config = PerfTestConfig(**raw_config)
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            msg = error["msg"]
            error_messages.append(f"  {loc}: {msg}")
        raise ConfigError(f"Configuration validation failed:\n" + "\n".join(error_messages))

    return config


def validate_config(config_path: Union[str, Path]) -> tuple[bool, str]:
    """
    Validate a configuration file without loading it.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Tuple of (is_valid, message)
    """
    try:
        load_config(config_path)
        return True, "Configuration is valid"
    except ConfigError as e:
        return False, str(e)
