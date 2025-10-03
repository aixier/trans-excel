"""
Qwen Provider for Translation
"""

import os
import logging
from typing import Dict, Any, Optional
import aiohttp
import json
import hashlib
import time

from services.llm.base_provider import BaseLLMProvider
from models.session_data import TranslationResult

logger = logging.getLogger(__name__)


class QwenProvider(BaseLLMProvider):
    """Qwen (Alibaba Cloud) translation provider."""

    ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    PRICING = {
        'qwen-max': {'input': 0.02, 'output': 0.06},  # per 1K tokens
        'qwen-plus': {'input': 0.004, 'output': 0.012},
        'qwen-turbo': {'input': 0.002, 'output': 0.006},
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
        self.api_key = api_key or os.getenv('QWEN_API_KEY') or os.getenv('DASHSCOPE_API_KEY')

        # Set model
        self.model = model or 'qwen-plus'

        # Set base URL (use default Dashscope endpoint)
        self.base_url = base_url or self.ENDPOINT

        # Set default parameters
        self.default_temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        task_type: str = "normal",
        context: Dict[str, Any] = None,
        temperature: float = 0.3
    ) -> TranslationResult:
        """Translate text using Qwen."""
        try:
            # Get prompts
            system_prompt, user_prompt = self.get_prompt(
                text, source_lang, target_lang, task_type, context or {}
            )

            # Prepare request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'model': self.model,
                'input': {
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ]
                },
                'parameters': {
                    'temperature': temperature,
                    'max_tokens': 2000,
                    'top_p': 0.8,
                    'repetition_penalty': 1.05,
                    'result_format': 'message'
                }
            }

            # Make API call
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ENDPOINT,
                    headers=headers,
                    json=payload,
                    timeout=60
                ) as response:
                    result = await response.json()

                    if response.status != 200:
                        error_msg = result.get('message', 'Unknown error')
                        raise Exception(f"Qwen API error: {error_msg}")

                    # Extract result
                    output = result.get('output', {})
                    choices = output.get('choices', [])
                    if not choices:
                        raise Exception("No translation result from Qwen")

                    translated_text = choices[0]['message']['content'].strip()

                    # Get token usage
                    usage = output.get('usage', {})
                    input_tokens = usage.get('input_tokens', 0)
                    output_tokens = usage.get('output_tokens', 0)
                    total_tokens = usage.get('total_tokens', input_tokens + output_tokens)

            # Calculate cost
            cost = self._calculate_cost(input_tokens, output_tokens)

            # Update totals
            self.total_tokens += total_tokens
            self.total_cost += cost

            return TranslationResult(
                text=translated_text,
                tokens_used=total_tokens,
                cost=cost,
                provider="qwen",
                model=self.model,
                metadata={
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'request_id': result.get('request_id')
                }
            )

        except Exception as e:
            logger.error(f"Qwen translation failed: {e}")
            raise

    async def validate_key(self) -> bool:
        """Validate Qwen API key."""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            # Test with a minimal request
            payload = {
                'model': self.model,
                'input': {
                    'messages': [
                        {'role': 'user', 'content': 'Hello'}
                    ]
                },
                'parameters': {
                    'max_tokens': 10
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ENDPOINT,
                    headers=headers,
                    json=payload,
                    timeout=10
                ) as response:
                    return response.status == 200

        except:
            return False

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for Qwen."""
        pricing = self.PRICING.get(self.model, self.PRICING['qwen-turbo'])
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        return round(input_cost + output_cost, 6)