"""OpenAI LLM Provider implementation."""

import asyncio
import time
from typing import List, Dict, Any
import httpx
import json
import logging

from .base_provider import (
    BaseLLMProvider,
    TranslationRequest,
    TranslationResponse,
    LLMConfig
)
from .prompt_template import PromptTemplate

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT-4 provider for translation."""

    def __init__(self, config: LLMConfig):
        """Initialize OpenAI provider."""
        super().__init__(config)
        self.base_url = config.base_url or "https://api.openai.com/v1"
        self.model = config.model or "gpt-4-turbo-preview"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        self.prompt_template = PromptTemplate()

    async def translate_single(
        self,
        request: TranslationRequest
    ) -> TranslationResponse:
        """Translate a single text using OpenAI API."""
        start_time = time.time()
        self._log_request(request)

        try:
            # Build task-specific prompt (根据任务类型选择合适的prompt)
            prompt = self.prompt_template.build_task_specific_prompt(
                source_text=request.source_text,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                task_type=request.task_type,
                context=request.context,
                game_info=request.game_info
            )

            # Prepare API request
            api_request = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a professional game translator."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "response_format": {"type": "text"}
            }

            # Make API call with retries
            translated_text, usage = await self._call_api_with_retry(api_request)

            # Calculate confidence
            confidence = self._calculate_confidence(request.source_text, translated_text)

            # Create response
            response = TranslationResponse(
                translated_text=translated_text,
                confidence=confidence,
                token_usage=usage,
                model=self.model,
                duration_ms=int((time.time() - start_time) * 1000),
                task_id=request.task_id
            )

            self._log_response(response)
            return response

        except Exception as e:
            logger.error(f"Translation failed for task {request.task_id}: {str(e)}")
            return TranslationResponse(
                translated_text="",
                confidence=0.0,
                error=str(e),
                task_id=request.task_id,
                duration_ms=int((time.time() - start_time) * 1000)
            )

    async def translate_batch(
        self,
        requests: List[TranslationRequest]
    ) -> List[TranslationResponse]:
        """Translate multiple texts in batch."""
        # OpenAI doesn't have native batch API, so we use concurrent requests
        tasks = [self.translate_single(req) for req in requests]

        # Limit concurrent requests to avoid rate limiting
        max_concurrent = min(5, len(requests))
        responses = []

        for i in range(0, len(tasks), max_concurrent):
            batch = tasks[i:i + max_concurrent]
            batch_responses = await asyncio.gather(*batch)
            responses.extend(batch_responses)

            # Small delay between batches to avoid rate limiting
            if i + max_concurrent < len(tasks):
                await asyncio.sleep(1)

        return responses

    async def health_check(self) -> bool:
        """Check OpenAI API health."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self.headers,
                    timeout=10
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

    async def _call_api_with_retry(self, request: Dict[str, Any]) -> tuple:
        """Call OpenAI API with retry logic."""
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=request
                    )

                    if response.status_code == 200:
                        data = response.json()

                        # Extract translated text
                        translated_text = data["choices"][0]["message"]["content"].strip()

                        # Extract token usage
                        usage = data.get("usage", {})
                        token_usage = {
                            "prompt_tokens": usage.get("prompt_tokens", 0),
                            "completion_tokens": usage.get("completion_tokens", 0),
                            "total_tokens": usage.get("total_tokens", 0)
                        }

                        return translated_text, token_usage

                    elif response.status_code == 429:
                        # Rate limited, wait longer
                        wait_time = self.config.retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limited, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)

                    else:
                        error_msg = f"API error: {response.status_code} - {response.text}"
                        logger.error(error_msg)
                        last_error = error_msg

            except httpx.TimeoutException:
                last_error = "Request timeout"
                logger.warning(f"Timeout on attempt {attempt + 1}")

            except Exception as e:
                last_error = str(e)
                logger.error(f"API call failed: {last_error}")

            # Wait before retry
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        raise Exception(f"Failed after {self.config.max_retries} attempts: {last_error}")