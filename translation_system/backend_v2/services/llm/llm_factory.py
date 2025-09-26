"""LLM Provider Factory."""

from typing import Dict, Any, Optional
import logging

from .base_provider import BaseLLMProvider, LLMConfig
from .openai_provider import OpenAIProvider
from .qwen_provider import QwenProvider

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating LLM provider instances."""

    # Supported providers
    PROVIDERS = {
        'openai': OpenAIProvider,
        'qwen': QwenProvider,
        'gpt4': OpenAIProvider,  # Alias for OpenAI
        'tongyi': QwenProvider,  # Alias for Qwen
    }

    @classmethod
    def create_provider(
        cls,
        provider_name: str,
        config: Dict[str, Any]
    ) -> BaseLLMProvider:
        """
        Create LLM provider instance.

        Args:
            provider_name: Name of the provider
            config: Provider configuration

        Returns:
            LLM provider instance

        Raises:
            ValueError: If provider is not supported
        """
        provider_name = provider_name.lower()

        if provider_name not in cls.PROVIDERS:
            raise ValueError(
                f"Unsupported provider: {provider_name}. "
                f"Supported providers: {', '.join(cls.PROVIDERS.keys())}"
            )

        # Create LLMConfig
        llm_config = LLMConfig(
            provider=provider_name,
            api_key=config.get('api_key', ''),
            base_url=config.get('base_url', ''),
            model=config.get('model', ''),
            temperature=config.get('temperature', 0.3),
            max_tokens=config.get('max_tokens', 4000),
            timeout=config.get('timeout', 90),
            max_retries=config.get('max_retries', 3),
            retry_delay=config.get('retry_delay', 3.0),
            extra_params=config.get('extra_params', {})
        )

        # Validate required fields
        if not llm_config.api_key:
            raise ValueError(f"API key is required for provider {provider_name}")

        # Create provider instance
        provider_class = cls.PROVIDERS[provider_name]
        provider = provider_class(llm_config)

        logger.info(
            f"Created {provider_name} provider with model {llm_config.model or 'default'}"
        )

        return provider

    @classmethod
    def create_from_config_file(
        cls,
        config_dict: Dict[str, Any],
        provider_name: Optional[str] = None
    ) -> BaseLLMProvider:
        """
        Create LLM provider from configuration dictionary.

        Args:
            config_dict: Full configuration dictionary
            provider_name: Override provider name (optional)

        Returns:
            LLM provider instance

        Raises:
            ValueError: If configuration is invalid
        """
        # Get LLM configuration section
        llm_config = config_dict.get('llm', {})

        # Determine provider
        if not provider_name:
            provider_name = llm_config.get('default_provider')

        if not provider_name:
            raise ValueError("No provider specified and no default provider configured")

        # Get provider-specific configuration
        providers_config = llm_config.get('providers', {})
        provider_config = providers_config.get(provider_name)

        if not provider_config:
            raise ValueError(f"No configuration found for provider {provider_name}")

        # Check if provider is enabled
        if not provider_config.get('enabled', True):
            raise ValueError(f"Provider {provider_name} is disabled")

        # Add batch control parameters
        batch_control = llm_config.get('batch_control', {})
        provider_config['max_concurrent_workers'] = batch_control.get('max_concurrent_workers', 10)
        provider_config['max_chars_per_batch'] = batch_control.get('max_chars_per_batch', 50000)

        # Add retry configuration
        retry_config = llm_config.get('retry', {})
        provider_config['max_retries'] = retry_config.get('max_attempts', 3)
        provider_config['retry_delay'] = retry_config.get('delay_seconds', 5.0)

        return cls.create_provider(provider_name, provider_config)

    @classmethod
    def get_supported_providers(cls) -> list:
        """Get list of supported provider names."""
        return list(cls.PROVIDERS.keys())

    @classmethod
    def validate_config(
        cls,
        provider_name: str,
        config: Dict[str, Any]
    ) -> tuple:
        """
        Validate provider configuration.

        Args:
            provider_name: Name of the provider
            config: Provider configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        if provider_name not in cls.PROVIDERS:
            return False, f"Unknown provider: {provider_name}"

        if not config.get('api_key'):
            return False, "API key is required"

        # Provider-specific validation
        if provider_name in ['openai', 'gpt4']:
            if not config.get('model'):
                config['model'] = 'gpt-4-turbo-preview'
        elif provider_name in ['qwen', 'tongyi']:
            if not config.get('model'):
                config['model'] = 'qwen-max'

        return True, None