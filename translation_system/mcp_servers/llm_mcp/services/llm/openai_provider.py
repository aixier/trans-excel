"""
OpenAI Provider for Translation
"""

import os
import openai
import logging
from typing import Dict, Any, Optional
import asyncio

from services.llm.base_provider import BaseLLMProvider
from models.session_data import TranslationResult

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI translation provider."""

    PRICING = {
        'gpt-4-turbo': {'input': 0.01, 'output': 0.03},  # per 1K tokens
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
    }

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        base_url: str = None,
        temperature: float = 0.3,
        max_tokens: int = 8000,
        timeout: int = 90
    ):
        super().__init__(api_key, model)

        # Set API key
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key

        # Set model
        self.model = model or 'gpt-4-turbo'

        # Set base URL
        self.base_url = base_url or 'https://api.openai.com/v1'

        # Set default parameters
        self.default_temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        # Initialize client
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
        except:
            # Fallback for older openai versions
            self.client = None

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        task_type: str = "normal",
        context: Dict[str, Any] = None,
        temperature: float = 0.3
    ) -> TranslationResult:
        """Translate text using OpenAI."""
        try:
            # Get prompts
            system_prompt, user_prompt = self.get_prompt(
                text, source_lang, target_lang, task_type, context or {}
            )

            # Call OpenAI API
            if self.client:  # New API
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=2000
                )

                # Extract result
                translated_text = response.choices[0].message.content.strip()
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens

            else:  # Old API
                response = await asyncio.to_thread(
                    openai.ChatCompletion.create,
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=2000
                )

                translated_text = response.choices[0].message.content.strip()
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens

            # Calculate cost
            total_tokens = input_tokens + output_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)

            # Update totals
            self.total_tokens += total_tokens
            self.total_cost += cost

            return TranslationResult(
                text=translated_text,
                tokens_used=total_tokens,
                cost=cost,
                provider="openai",
                model=self.model,
                metadata={
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens
                }
            )

        except Exception as e:
            logger.error(f"OpenAI translation failed: {e}")
            raise

    async def validate_key(self) -> bool:
        """Validate OpenAI API key."""
        try:
            if self.client:
                # Test with a simple call
                await self.client.models.list()
            else:
                # Old API test
                await asyncio.to_thread(openai.Model.list)
            return True
        except:
            return False

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for OpenAI."""
        pricing = self.PRICING.get(self.model, self.PRICING['gpt-3.5-turbo'])
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        return round(input_cost + output_cost, 6)