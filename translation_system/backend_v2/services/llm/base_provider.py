"""Base LLM Provider abstract class."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TranslationRequest:
    """Translation request data structure."""

    source_text: str
    source_lang: str
    target_lang: str
    context: str = ""
    game_info: Dict[str, Any] = field(default_factory=dict)
    task_id: Optional[str] = None
    batch_id: Optional[str] = None
    group_id: Optional[str] = None


@dataclass
class TranslationResponse:
    """Translation response data structure."""

    translated_text: str
    confidence: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    model: str = ""
    duration_ms: int = 0
    error: Optional[str] = None
    task_id: Optional[str] = None


@dataclass
class LLMConfig:
    """LLM configuration."""

    provider: str
    api_key: str
    base_url: str = ""
    model: str = ""
    temperature: float = 0.3
    max_tokens: int = 4000
    timeout: int = 90
    max_retries: int = 3
    retry_delay: float = 3.0
    extra_params: Dict[str, Any] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig):
        """
        Initialize LLM provider.

        Args:
            config: LLM configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def translate_single(
        self,
        request: TranslationRequest
    ) -> TranslationResponse:
        """
        Translate a single text.

        Args:
            request: Translation request

        Returns:
            Translation response
        """
        pass

    @abstractmethod
    async def translate_batch(
        self,
        requests: List[TranslationRequest]
    ) -> List[TranslationResponse]:
        """
        Translate multiple texts in batch.

        Args:
            requests: List of translation requests

        Returns:
            List of translation responses
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the LLM provider is healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass

    def _log_request(self, request: TranslationRequest) -> None:
        """Log translation request."""
        self.logger.debug(
            f"Translation request - "
            f"task_id={request.task_id}, "
            f"source_lang={request.source_lang}, "
            f"target_lang={request.target_lang}, "
            f"text_length={len(request.source_text)}"
        )

    def _log_response(self, response: TranslationResponse) -> None:
        """Log translation response."""
        self.logger.debug(
            f"Translation response - "
            f"task_id={response.task_id}, "
            f"duration={response.duration_ms}ms, "
            f"tokens={response.token_usage}, "
            f"confidence={response.confidence}"
        )

    def _calculate_confidence(self, source_text: str, translated_text: str) -> float:
        """
        Calculate translation confidence score.

        Simple heuristic based on text length ratio.
        Override in specific providers for better scoring.
        """
        if not translated_text:
            return 0.0

        source_len = len(source_text)
        target_len = len(translated_text)

        if source_len == 0:
            return 0.0

        ratio = target_len / source_len

        # Expected ratio ranges for different language pairs
        # These are rough estimates
        if ratio < 0.2 or ratio > 5.0:
            return 0.3  # Very unusual ratio
        elif ratio < 0.5 or ratio > 2.0:
            return 0.7  # Somewhat unusual
        else:
            return 0.9  # Normal ratio