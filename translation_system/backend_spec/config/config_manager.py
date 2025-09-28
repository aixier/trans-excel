"""Configuration management module using Singleton pattern."""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """
    Singleton configuration manager.

    Loads configuration from YAML file and provides access to config values
    using dot notation (e.g., 'api.host', 'excel.max_file_size').
    """

    _instance: Optional['ConfigManager'] = None
    _config: Optional[Dict[str, Any]] = None

    def __new__(cls) -> 'ConfigManager':
        """Ensure only one instance of ConfigManager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize configuration if not already loaded."""
        if self._config is None:
            self.load_config()

    def load_config(self, config_path: Optional[str] = None) -> None:
        """
        Load configuration from YAML file.

        Args:
            config_path: Optional path to config file. If None, uses default path.
        """
        if config_path is None:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "config.yaml"

        if not Path(config_path).exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_str = f.read()
            # Replace environment variables (e.g., ${API_HOST})
            config_str = os.path.expandvars(config_str)
            self._config = yaml.safe_load(config_str)

    @property
    def config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot notation key.

        Args:
            key: Configuration key in dot notation (e.g., 'api.host')
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config_manager.get('api.host')
            '0.0.0.0'
            >>> config_manager.get('api.port', 8000)
            8013
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    # Convenient property accessors for frequently used configs

    @property
    def api_host(self) -> str:
        """Get API server host."""
        return self.get('api.host', '0.0.0.0')

    @property
    def api_port(self) -> int:
        """Get API server port."""
        return self.get('api.port', 8013)

    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.get('system.log_level', 'INFO')

    @property
    def log_rotation(self) -> str:
        """Get log rotation configuration."""
        return self.get('system.log_rotation', '500 MB')

    @property
    def log_retention(self) -> str:
        """Get log retention configuration."""
        return self.get('system.log_retention', '7 days')

    @property
    def max_file_size(self) -> int:
        """Get maximum Excel file size in bytes."""
        return self.get('excel.max_file_size', 10485760)

    @property
    def excel_chunk_size(self) -> int:
        """Get Excel processing chunk size."""
        return self.get('excel.chunk_size', 10000)


# Global singleton instance
config_manager = ConfigManager()