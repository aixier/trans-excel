"""
LLM抽象基类
定义所有LLM提供商必须实现的接口
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio
import json
from enum import Enum


class ResponseFormat(Enum):
    """响应格式枚举"""
    TEXT = "text"
    JSON = "json_object"


@dataclass
class LLMConfig:
    """LLM基础配置"""
    api_key: str
    base_url: str
    model: str
    temperature: float = 0.3
    max_tokens: int = 4000
    timeout: int = 90
    max_retries: int = 3
    retry_delay: float = 3.0


@dataclass
class LLMMessage:
    """消息格式"""
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    """LLM响应格式"""
    content: str
    usage: Dict[str, int] = None  # tokens usage
    model: str = None
    finish_reason: str = None


class BaseLLM(ABC):
    """LLM抽象基类"""

    def __init__(self, config: LLMConfig):
        """初始化LLM"""
        self.config = config
        self._client = None

    @abstractmethod
    async def initialize(self):
        """异步初始化客户端"""
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: ResponseFormat = ResponseFormat.TEXT,
        timeout: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        执行聊天补全

        Args:
            messages: 消息列表
            temperature: 温度参数（可选，覆盖默认值）
            max_tokens: 最大token数（可选，覆盖默认值）
            response_format: 响应格式
            timeout: 超时时间（可选，覆盖默认值）
            **kwargs: 其他特定于提供商的参数

        Returns:
            LLMResponse: 响应结果
        """
        pass

    @abstractmethod
    async def chat_completion_with_retry(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: ResponseFormat = ResponseFormat.TEXT,
        timeout: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        带重试机制的聊天补全

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式
            timeout: 超时时间
            **kwargs: 其他参数

        Returns:
            LLMResponse: 响应结果
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        pass

    async def close(self):
        """关闭客户端连接"""
        if self._client:
            # 基础清理逻辑
            self._client = None

    def format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """格式化消息为标准格式"""
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def validate_response_format(self, response: str, format_type: ResponseFormat) -> bool:
        """验证响应格式"""
        if format_type == ResponseFormat.JSON:
            try:
                json.loads(response)
                return True
            except json.JSONDecodeError:
                return False
        return True

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            test_messages = [
                LLMMessage(role="user", content="Hello")
            ]
            response = await self.chat_completion(
                messages=test_messages,
                max_tokens=10,
                timeout=10
            )
            return bool(response.content)
        except Exception:
            return False