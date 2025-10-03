"""
Base LLM Provider for Translation
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from models.session_data import TranslationResult
import logging

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key
        self.model = model
        self.total_tokens = 0
        self.total_cost = 0.0

    @abstractmethod
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        task_type: str = "normal",
        context: Dict[str, Any] = None,
        temperature: float = 0.3
    ) -> TranslationResult:
        """Translate text using the LLM."""
        pass

    @abstractmethod
    async def validate_key(self) -> bool:
        """Validate API key."""
        pass

    def get_prompt(self, text: str, source_lang: str, target_lang: str,
                   task_type: str, context: Dict[str, Any]) -> tuple[str, str]:
        """Get system and user prompts for translation."""

        # System prompt based on task type
        if task_type == "yellow":  # Retranslation
            system_prompt = f"""You are a professional game translator.
The following text needs retranslation from {source_lang} to {target_lang}.
Previous translation may have issues. Provide a more accurate translation.
Keep the same tone and style as the original text.
Preserve any game-specific terminology."""

        elif task_type == "blue":  # Shortening
            system_prompt = f"""You are a professional game translator.
Translate the following text from {source_lang} to {target_lang}.
The translation should be shorter and more concise than the original.
Keep the core meaning but make it more compact.
Target length: 80% of original or less."""

        else:  # Normal translation
            system_prompt = f"""You are a professional game translator.
Translate the following text from {source_lang} to {target_lang}.
Keep the same tone and style as the original text.
Preserve any game-specific terminology and formatting."""

        # User prompt with context
        user_parts = [f"Text to translate: {text}"]

        if context:
            if context.get('sheet_context'):
                user_parts.append(f"Sheet context: {context['sheet_context']}")
            if context.get('row_context'):
                user_parts.append(f"Row context: {context['row_context']}")
            if context.get('column_context'):
                user_parts.append(f"Column context: {context['column_context']}")
            if context.get('previous_translations'):
                user_parts.append(f"Previous translations: {context['previous_translations']}")

        user_parts.append("Translation:")
        user_prompt = "\n\n".join(user_parts)

        return system_prompt, user_prompt

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage."""
        # Override in subclasses with provider-specific pricing
        return 0.0

    def get_total_tokens(self) -> int:
        """Get total tokens used."""
        return self.total_tokens

    def get_total_cost(self) -> float:
        """Get total cost."""
        return self.total_cost