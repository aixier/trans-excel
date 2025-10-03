"""Configuration loader for LLM MCP Server."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and manage configuration for LLM MCP."""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self.load_config()

    def load_config(self, config_path: Optional[str] = None):
        """Load configuration from YAML file."""
        if config_path is None:
            # Default config path
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / 'config' / 'llm_config.yaml'

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)

            # Replace environment variables
            self._replace_env_vars(self._config)

            logger.info(f"Configuration loaded from {config_path}")

        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}. Using defaults.")
            self._config = self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = self._get_default_config()

    def _replace_env_vars(self, config: Any):
        """Recursively replace ${VAR} with environment variables."""
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    config[key] = os.environ.get(env_var, value)
                elif isinstance(value, (dict, list)):
                    self._replace_env_vars(value)
        elif isinstance(config, list):
            for i, item in enumerate(config):
                if isinstance(item, (dict, list)):
                    self._replace_env_vars(item)

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'default_provider': 'qwen-plus',
            'providers': {
                'qwen-plus': {
                    'enabled': True,
                    'api_key': 'sk-4c89a24b73d24731b86bf26337398cef',
                    'base_url': 'https://dashscope.aliyuncs.com/api/v1',
                    'model': 'qwen-plus',
                    'temperature': 0.3,
                    'max_tokens': 8000,
                    'timeout': 90,
                    'max_retries': 3,
                    'retry_delay': 3.0,
                    'description': '阿里云通义千问Plus - 平衡性能和成本'
                }
            },
            'retry': {
                'max_attempts': 3,
                'delay_seconds': 5.0,
                'exponential_backoff': True,
                'max_delay_seconds': 60.0
            },
            'execution': {
                'max_workers': 5,
                'batch_size': 10
            }
        }

    def get_config(self) -> Dict[str, Any]:
        """Get full configuration."""
        return self._config

    def get_default_provider(self) -> str:
        """Get default provider name."""
        return self._config.get('default_provider', 'qwen-plus')

    def get_provider_config(self, provider_name: Optional[str] = None) -> Dict[str, Any]:
        """Get provider configuration."""
        if provider_name is None:
            provider_name = self.get_default_provider()

        providers = self._config.get('providers', {})
        provider_config = providers.get(provider_name)

        if not provider_config:
            raise ValueError(f"Provider {provider_name} not found in configuration")

        if not provider_config.get('enabled', True):
            raise ValueError(f"Provider {provider_name} is disabled")

        return provider_config

    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry configuration."""
        return self._config.get('retry', {
            'max_attempts': 3,
            'delay_seconds': 5.0,
            'exponential_backoff': True,
            'max_delay_seconds': 60.0
        })

    def get_execution_config(self) -> Dict[str, Any]:
        """Get execution configuration."""
        return self._config.get('execution', {
            'max_workers': 5,
            'batch_size': 10
        })


# Global config loader instance
config_loader = ConfigLoader()