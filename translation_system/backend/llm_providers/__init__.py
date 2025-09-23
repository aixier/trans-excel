"""
LLM Providers Package
提供多种LLM服务的统一接口
"""

from .base_llm import BaseLLM, LLMConfig, LLMMessage, LLMResponse, ResponseFormat
from .qwen_llm import QwenLLM
from .openai_llm import OpenAILLM
from .gemini_llm import GeminiLLM
from .llm_factory import LLMFactory, LLMProvider
from .llm_config_manager import LLMConfigManager

__all__ = [
    # 基类
    "BaseLLM",
    "LLMConfig",
    "LLMMessage",
    "LLMResponse",
    "ResponseFormat",

    # 具体实现
    "QwenLLM",
    "OpenAILLM",
    "GeminiLLM",

    # 工厂和管理
    "LLMFactory",
    "LLMProvider",
    "LLMConfigManager"
]

# 版本信息
__version__ = "1.0.0"