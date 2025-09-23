"""
LLM工厂类
负责根据配置创建相应的LLM实例
"""
import logging
from typing import Dict, Any, Optional
from enum import Enum
from .base_llm import BaseLLM, LLMConfig
from .qwen_llm import QwenLLM
from .openai_llm import OpenAILLM
from .openai_gpt5_llm import OpenAIGPT5LLM
from .gemini_llm import GeminiLLM


logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """LLM提供商枚举"""
    QWEN = "qwen"
    OPENAI = "openai"
    OPENAI_GPT5 = "openai-gpt5"  # GPT-5专用
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"  # 预留
    COHERE = "cohere"  # 预留
    CUSTOM = "custom"  # 自定义


class LLMFactory:
    """LLM工厂类"""

    # 提供商到实现类的映射
    _provider_map = {
        LLMProvider.QWEN: QwenLLM,
        LLMProvider.OPENAI: OpenAILLM,
        LLMProvider.OPENAI_GPT5: OpenAIGPT5LLM,
        LLMProvider.GEMINI: GeminiLLM,
    }

    # 默认配置
    _default_configs = {
        LLMProvider.QWEN: {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-plus",
            "temperature": 0.3,
            "max_tokens": 4000
        },
        LLMProvider.OPENAI: {
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo",
            "temperature": 0.3,
            "max_tokens": 4000
        },
        LLMProvider.GEMINI: {
            "model": "gemini-pro",
            "temperature": 0.3,
            "max_tokens": 4000
        },
        LLMProvider.OPENAI_GPT5: {
            "base_url": "https://api.openai.com",
            "model": "gpt-5-nano",
            "temperature": 0.3,
            "max_tokens": 128000
        }
    }

    @classmethod
    def create_llm(
        cls,
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ) -> BaseLLM:
        """
        创建LLM实例

        Args:
            provider: 提供商名称
            api_key: API密钥
            model: 模型名称（可选）
            base_url: API基础URL（可选）
            **kwargs: 其他配置参数

        Returns:
            BaseLLM: LLM实例
        """
        # 转换provider为枚举
        try:
            # 处理特殊情况
            provider_lower = provider.lower()
            if provider_lower == "openai-gpt5":
                provider_lower = "openai-gpt5"  # 保持连字符
            elif "-" in provider_lower:
                provider_lower = provider_lower.replace("-", "_")

            provider_enum = LLMProvider(provider_lower)
        except ValueError:
            # 尝试直接匹配
            for enum_val in LLMProvider:
                if enum_val.value == provider.lower() or enum_val.value.replace("-", "_") == provider.lower().replace("-", "_"):
                    provider_enum = enum_val
                    break
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")

        # 检查是否有对应的实现
        if provider_enum not in cls._provider_map:
            raise NotImplementedError(f"LLM provider {provider} is not implemented yet")

        # 获取默认配置
        default_config = cls._default_configs.get(provider_enum, {})

        # 构建配置
        config_dict = {
            "api_key": api_key,
            "base_url": base_url or default_config.get("base_url"),
            "model": model or default_config.get("model"),
            "temperature": kwargs.get("temperature", default_config.get("temperature", 0.3)),
            "max_tokens": kwargs.get("max_tokens", default_config.get("max_tokens", 4000)),
            "timeout": kwargs.get("timeout", 90),
            "max_retries": kwargs.get("max_retries", 3),
            "retry_delay": kwargs.get("retry_delay", 3.0)
        }

        # 创建配置对象
        config = LLMConfig(**config_dict)

        # 创建LLM实例
        llm_class = cls._provider_map[provider_enum]
        llm = llm_class(config)

        logger.info(f"Created LLM instance: {provider} with model {config.model}")
        return llm

    @classmethod
    def create_from_config(cls, config_dict: Dict[str, Any]) -> BaseLLM:
        """
        从配置字典创建LLM实例

        Args:
            config_dict: 配置字典

        Returns:
            BaseLLM: LLM实例
        """
        provider = config_dict.pop("provider", None)
        if not provider:
            raise ValueError("Provider is required in config")

        api_key = config_dict.pop("api_key", None)
        if not api_key:
            raise ValueError("API key is required in config")

        return cls.create_llm(provider, api_key, **config_dict)

    @classmethod
    def get_supported_providers(cls) -> list:
        """获取支持的提供商列表"""
        return [p.value for p in cls._provider_map.keys()]

    @classmethod
    def get_provider_info(cls, provider: str) -> Dict[str, Any]:
        """
        获取提供商信息

        Args:
            provider: 提供商名称

        Returns:
            Dict: 提供商信息
        """
        try:
            provider_enum = LLMProvider(provider.lower())
        except ValueError:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        if provider_enum not in cls._provider_map:
            raise NotImplementedError(f"LLM provider {provider} is not implemented yet")

        llm_class = cls._provider_map[provider_enum]
        default_config = cls._default_configs.get(provider_enum, {})

        # 获取模型列表
        models = []
        if hasattr(llm_class, "MODELS"):
            models = list(llm_class.MODELS.keys())

        return {
            "provider": provider,
            "default_config": default_config,
            "supported_models": models,
            "implemented": True
        }

    @classmethod
    def validate_config(cls, provider: str, config_dict: Dict[str, Any]) -> bool:
        """
        验证配置是否有效

        Args:
            provider: 提供商名称
            config_dict: 配置字典

        Returns:
            bool: 是否有效
        """
        try:
            provider_enum = LLMProvider(provider.lower())
        except ValueError:
            return False

        # 检查必需字段
        if "api_key" not in config_dict:
            return False

        # 检查模型是否支持
        if provider_enum in cls._provider_map:
            llm_class = cls._provider_map[provider_enum]
            if hasattr(llm_class, "MODELS"):
                model = config_dict.get("model")
                if model and model not in llm_class.MODELS:
                    logger.warning(f"Model {model} not in supported list for {provider}")
                    # 不直接返回False，因为可能支持其他模型

        return True