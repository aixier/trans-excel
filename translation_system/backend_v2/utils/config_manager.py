"""Configuration management module."""

import os
import yaml
from typing import Dict, Any
from pathlib import Path


class ConfigManager:
    """Manage application configuration."""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self.load_config()

    def load_config(self, config_path: str = None) -> None:
        """Load configuration from YAML file."""
        if config_path is None:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "config.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

    @property
    def config(self) -> Dict[str, Any]:
        """Get configuration dictionary."""
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    @property
    def max_chars_per_batch(self) -> int:
        """Get max characters per batch."""
        return self.get('llm.batch_control.max_chars_per_batch', 50000)

    @property
    def max_concurrent_workers(self) -> int:
        """Get max concurrent workers."""
        return self.get('llm.batch_control.max_concurrent_workers', 10)

    @property
    def log_level(self) -> str:
        """Get log level."""
        return self.get('system.log_level', 'INFO')


# Global instance
config_manager = ConfigManager()