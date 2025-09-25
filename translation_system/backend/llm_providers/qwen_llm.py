"""
阿里云通义千问LLM实现
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
from .base_llm import BaseLLM, LLMConfig, LLMMessage, LLMResponse, ResponseFormat


logger = logging.getLogger(__name__)


class QwenLLM(BaseLLM):
    """阿里云通义千问LLM实现"""

    # Qwen模型特定配置
    MODELS = {
        "qwen-plus": {
            "name": "通义千问Plus",
            "max_tokens": 8192,
            "context_window": 32768,
            "price_per_1k_tokens": {"input": 0.004, "output": 0.012}
        },
        "qwen-max": {
            "name": "通义千问Max",
            "max_tokens": 8192,
            "context_window": 32768,
            "price_per_1k_tokens": {"input": 0.02, "output": 0.06}
        },
        "qwen-turbo": {
            "name": "通义千问Turbo",
            "max_tokens": 8192,
            "context_window": 8192,
            "price_per_1k_tokens": {"input": 0.002, "output": 0.006}
        },
        "qwen-long": {
            "name": "通义千问Long",
            "max_tokens": 8192,
            "context_window": 1000000,  # 百万级上下文
            "price_per_1k_tokens": {"input": 0.0005, "output": 0.002}
        }
    }

    def __init__(self, config: LLMConfig):
        """初始化Qwen LLM"""
        super().__init__(config)

        # 验证模型
        if config.model not in self.MODELS:
            logger.warning(f"Unknown Qwen model: {config.model}, using qwen-plus")
            config.model = "qwen-plus"

        # Qwen特定的默认配置
        if not config.base_url:
            config.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    async def initialize(self):
        """异步初始化OpenAI客户端（Qwen使用OpenAI兼容接口）"""
        import httpx
        import sys

        logger.info(f"Python encoding: {sys.getdefaultencoding()}")
        logger.info(f"API Key length: {len(self.config.api_key) if self.config.api_key else 0}")
        logger.info(f"Base URL: {self.config.base_url}")

        # 创建自定义的httpx客户端，确保正确的编码处理
        http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            timeout=httpx.Timeout(60.0, read=300.0),
            headers={
                "Accept-Charset": "utf-8",
                "Content-Type": "application/json; charset=utf-8"
            }
        )

        self._client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            http_client=http_client
        )
        logger.info(f"Initialized Qwen LLM with model: {self.config.model}")

    async def chat_completion(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: ResponseFormat = ResponseFormat.TEXT,
        timeout: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """执行聊天补全"""

        if not self._client:
            await self.initialize()

        # 使用提供的参数或默认值
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        timeout = timeout if timeout is not None else self.config.timeout

        # 格式化消息
        formatted_messages = self.format_messages(messages)

        # 构建请求参数
        request_params = {
            "model": self.config.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": timeout
        }

        # Qwen特定的响应格式处理
        if response_format == ResponseFormat.JSON:
            request_params["response_format"] = {"type": "json_object"}
            # 添加JSON格式提示到系统消息
            if formatted_messages and formatted_messages[0]["role"] == "system":
                formatted_messages[0]["content"] += "\n请确保返回纯JSON格式的响应。"

        # 添加Qwen特定参数
        if "top_p" in kwargs:
            request_params["top_p"] = kwargs["top_p"]
        if "frequency_penalty" in kwargs:
            request_params["frequency_penalty"] = kwargs["frequency_penalty"]
        if "presence_penalty" in kwargs:
            request_params["presence_penalty"] = kwargs["presence_penalty"]
        if "seed" in kwargs:
            request_params["seed"] = kwargs["seed"]
        if "stream" in kwargs:
            request_params["stream"] = kwargs["stream"]

        # Qwen特定：启用搜索增强（如果需要）
        if kwargs.get("enable_search", False):
            request_params["tools"] = [{
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search for information on the web"
                }
            }]

        try:
            # 添加调试日志
            logger.debug(f"Request params keys: {request_params.keys()}")
            logger.debug(f"Model: {request_params.get('model')}")
            logger.debug(f"Temperature: {request_params.get('temperature')}")

            # 检查消息内容
            if isinstance(request_params.get("messages"), list):
                for i, msg in enumerate(request_params["messages"]):
                    logger.debug(f"Message {i}: role={msg.get('role')}")
                    content = msg.get("content", "")
                    logger.debug(f"Message {i} content type: {type(content)}")
                    logger.debug(f"Message {i} content length: {len(content) if isinstance(content, str) else 'N/A'}")
                    if isinstance(content, str) and len(content) > 0:
                        # 检查是否包含中文
                        try:
                            content.encode('ascii')
                            logger.debug(f"Message {i}: ASCII only")
                        except UnicodeEncodeError as e:
                            logger.debug(f"Message {i}: Contains non-ASCII at position {e.start}-{e.end}")
                            logger.debug(f"Message {i} first 50 chars: {content[:50]}")

            logger.debug("About to call OpenAI API...")
            response = await self._client.chat.completions.create(**request_params)

            # 提取响应内容
            content = response.choices[0].message.content

            # 验证JSON格式（如果需要）
            if response_format == ResponseFormat.JSON:
                if not self.validate_response_format(content, response_format):
                    raise ValueError("Response is not valid JSON format")

            # 构建响应
            return LLMResponse(
                content=content,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                model=response.model,
                finish_reason=response.choices[0].finish_reason
            )

        except Exception as e:
            logger.error(f"Qwen API call failed: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception args: {e.args if hasattr(e, 'args') else 'N/A'}")

            # 打印完整的堆栈跟踪
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            raise

    async def chat_completion_with_retry(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: ResponseFormat = ResponseFormat.TEXT,
        timeout: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """带重试机制的聊天补全"""

        max_retries = kwargs.get("max_retries", self.config.max_retries)
        retry_delay = kwargs.get("retry_delay", self.config.retry_delay)

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # 指数退避
                    delay = retry_delay * (2 ** (attempt - 1))
                    # 增加超时时间
                    current_timeout = min(timeout * (1 + attempt * 0.5), 600) if timeout else self.config.timeout
                    logger.info(f"Qwen retry attempt {attempt + 1}/{max_retries}, delay: {delay}s, timeout: {current_timeout}s")
                    await asyncio.sleep(delay)
                else:
                    current_timeout = timeout if timeout else self.config.timeout

                # 执行API调用
                response = await self.chat_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                    timeout=current_timeout,
                    **kwargs
                )

                return response

            except asyncio.TimeoutError:
                logger.warning(f"Qwen timeout on attempt {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise
            except Exception as e:
                logger.error(f"Qwen error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt == max_retries - 1:
                    raise

        raise Exception(f"Failed after {max_retries} retries")

    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "Alibaba Cloud Qwen (通义千问)"

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        model_info = self.MODELS.get(self.config.model, {})
        return {
            "provider": self.get_provider_name(),
            "model": self.config.model,
            "model_name": model_info.get("name", self.config.model),
            "max_tokens": model_info.get("max_tokens", 4096),
            "context_window": model_info.get("context_window", 8192),
            "pricing": model_info.get("price_per_1k_tokens", {}),
            "base_url": self.config.base_url,
            "features": {
                "json_mode": True,
                "function_calling": True,
                "streaming": True,
                "search_enhanced": True  # Qwen特有功能
            }
        }

    async def close(self):
        """关闭客户端连接"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Qwen LLM client closed")