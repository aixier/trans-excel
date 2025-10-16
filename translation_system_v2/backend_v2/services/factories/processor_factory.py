"""Processor factory for creating processor instances from configuration."""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from importlib import import_module

logger = logging.getLogger(__name__)


class ProcessorFactory:
    """Factory for creating processor instances from YAML configuration."""

    def __init__(self, config_path: str = None):
        """Initialize factory with configuration.

        Args:
            config_path: Path to processors.yaml (default: config/processors.yaml)
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'processors.yaml'

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load processors configuration from YAML.

        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded processors config from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Failed to load processors config: {e}")
            return {'processors': {}, 'processor_sets': {}, 'default_processor': 'llm_qwen'}

    def create_processor(self, processor_name: str):
        """Create a processor instance.

        Args:
            processor_name: Processor name (e.g., 'llm_qwen', 'uppercase')

        Returns:
            Processor instance

        Raises:
            ValueError: If processor not found or disabled
        """
        if processor_name not in self.config['processors']:
            raise ValueError(f"Processor '{processor_name}' not found in configuration")

        proc_config = self.config['processors'][processor_name]

        if not proc_config.get('enabled', True):
            raise ValueError(f"Processor '{processor_name}' is disabled")

        # Import processor class
        class_path = proc_config['class']
        module_path, class_name = class_path.rsplit('.', 1)

        try:
            module = import_module(module_path)
            processor_class = getattr(module, class_name)

            # Get configuration
            config = proc_config.get('config', {})
            processor_type = proc_config.get('type', 'unknown')

            # Special handling for LLM providers (they expect LLMConfig object)
            if processor_type == 'llm_translation':
                from services.llm.llm_factory import LLMFactory
                from utils.config_manager import config_manager

                # Create LLM provider using LLMFactory
                # Map processor_name to provider name (e.g., llm_qwen → qwen)
                provider_name = processor_name.replace('llm_', '')
                full_config = config_manager.get_config()

                processor_instance = LLMFactory.create_from_config_file(full_config, provider_name)
                logger.debug(f"Created LLM processor: {processor_name} → {provider_name}")

            else:
                # Standard processors: pass config as kwargs
                if config:
                    processor_instance = processor_class(**config)
                else:
                    processor_instance = processor_class()

                logger.debug(f"Created processor: {processor_name} ({class_name})")

            return processor_instance

        except Exception as e:
            logger.error(f"Failed to create processor '{processor_name}': {e}")
            raise

    def get_processor_config(self, processor_name: str) -> Dict[str, Any]:
        """Get processor configuration.

        Args:
            processor_name: Processor name

        Returns:
            Processor configuration dictionary
        """
        return self.config['processors'].get(processor_name, {})

    def get_default_processor(self):
        """Get default processor instance.

        Returns:
            Default processor instance
        """
        default_name = self.config.get('default_processor', 'llm_qwen')
        return self.create_processor(default_name)

    def list_available_processors(self) -> list:
        """List all available processors.

        Returns:
            List of processor information dictionaries
        """
        processors_info = []
        for proc_name, proc_config in self.config['processors'].items():
            processors_info.append({
                'name': proc_name,
                'description': proc_config.get('description', ''),
                'type': proc_config.get('type', 'unknown'),
                'enabled': proc_config.get('enabled', True),
                'requires_llm': proc_config.get('requires_llm', True)
            })

        return processors_info


# Global instance
processor_factory = ProcessorFactory()
