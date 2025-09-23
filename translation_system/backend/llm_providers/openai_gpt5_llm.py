"""
OpenAI GPT-5 LLM实现
专门处理GPT-5系列模型，使用新的/v1/responses端点
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
import httpx
from .base_llm import BaseLLM, LLMConfig, LLMMessage, LLMResponse, ResponseFormat

logger = logging.getLogger(__name__)


class OpenAIGPT5LLM(BaseLLM):
    """OpenAI GPT-5 LLM实现，使用新的responses API"""

    # GPT-5模型配置
    MODELS = {
        "gpt-5-nano": {
            "name": "GPT-5 Nano",
            "actual_id": "gpt-5-nano-2025-08-07",
            "max_tokens": 128000,
            "context_window": 400000,
            "price_per_1k_tokens": {"input": 0.05, "output": 0.40},
            "supports_reasoning": True
        },
        "gpt-5-nano-2025-08-07": {
            "name": "GPT-5 Nano (2025-08-07)",
            "max_tokens": 128000,
            "context_window": 400000,
            "price_per_1k_tokens": {"input": 0.05, "output": 0.40},
            "supports_reasoning": True
        }
    }

    def __init__(self, config: LLMConfig):
        """初始化OpenAI GPT-5 LLM"""
        super().__init__(config)

        # 初始化客户端为None
        self._client = None

        # 验证模型
        if config.model not in self.MODELS:
            logger.warning(f"Using custom GPT-5 model: {config.model}")

        # 默认配置
        if not config.base_url:
            config.base_url = "https://api.openai.com"

        # 设置端点
        self.responses_endpoint = f"{config.base_url}/v1/responses"
        self.chat_endpoint = f"{config.base_url}/v1/chat/completions"

    async def initialize(self):
        """异步初始化客户端"""
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(self.config.timeout or 90.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            verify=True  # Ensure SSL verification is enabled
        )
        logger.info(f"Initialized OpenAI GPT-5 LLM with model: {self.config.model}")

    async def chat_completion(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: ResponseFormat = ResponseFormat.TEXT,
        timeout: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """执行聊天补全 - 使用新的responses API"""

        if not self._client:
            await self.initialize()

        # 使用提供的参数或默认值
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        timeout = timeout if timeout is not None else self.config.timeout

        # 将messages转换为input格式
        # 对于responses API，我们需要将消息历史转换为单个输入
        input_text = self._convert_messages_to_input(messages)

        # 构建请求参数
        request_params = {
            "model": self.config.model,
            "input": input_text,
            "max_output_tokens": max_tokens,
            "store": False  # 不存储响应
        }

        # GPT-5 nano 不支持自定义temperature，只能用默认值1
        # 所以我们不设置temperature参数

        # 添加reasoning参数（如果支持）
        model_info = self.MODELS.get(self.config.model, {})
        if model_info.get("supports_reasoning"):
            request_params["reasoning"] = {
                "effort": kwargs.get("reasoning_effort", "medium")
            }

        # 响应格式处理 - GPT-5 支持 JSON 输出！
        if response_format == ResponseFormat.JSON:
            request_params["text"] = {
                "format": {
                    "type": "json_object"  # 这确实有效！
                }
            }

        try:
            # 发送请求到新的responses端点
            response = await self._client.post(
                self.responses_endpoint,
                json=request_params
            )

            if response.status_code != 200:
                # 如果responses端点失败，尝试使用传统端点
                error_detail = response.text
                logger.warning(f"Responses API failed with {response.status_code}: {error_detail}")
                return await self._fallback_to_chat_completions(messages, temperature, max_tokens, response_format, timeout, **kwargs)

            response_data = response.json()

            # 提取响应内容
            content = ""
            if "output" in response_data:
                for output in response_data["output"]:
                    if output.get("type") == "message":
                        for content_item in output.get("content", []):
                            if content_item.get("type") == "output_text":
                                content = content_item.get("text", "")
                                if content:  # 如果找到内容就退出
                                    break
                        if content:  # 如果找到内容就退出外层循环
                            break

            # 调试日志
            if not content:
                logger.warning(f"No content extracted from response. Response structure: {json.dumps(response_data, ensure_ascii=False)[:500]}")

            # 构建响应
            usage = response_data.get("usage", {})
            return LLMResponse(
                content=content,
                usage={
                    "prompt_tokens": usage.get("input_tokens", 0),
                    "completion_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "reasoning_tokens": usage.get("output_tokens_details", {}).get("reasoning_tokens", 0)
                },
                model=response_data.get("model", self.config.model),
                finish_reason="stop"
            )

        except Exception as e:
            import traceback
            logger.error(f"GPT-5 API call failed: {type(e).__name__}: {str(e)}")
            logger.debug(f"Full traceback: {traceback.format_exc()}")
            # 尝试降级到传统API
            return await self._fallback_to_chat_completions(messages, temperature, max_tokens, response_format, timeout, **kwargs)

    def _convert_messages_to_input(self, messages: List[LLMMessage]) -> str:
        """将消息列表转换为单个输入字符串"""
        input_parts = []

        for msg in messages:
            role = msg.role
            content = msg.content

            if role == "system":
                input_parts.append(f"System: {content}")
            elif role == "user":
                input_parts.append(f"User: {content}")
            elif role == "assistant":
                input_parts.append(f"Assistant: {content}")

        # 如果只有一条用户消息，直接返回内容
        if len(messages) == 1 and messages[0].role == "user":
            return messages[0].content

        # 否则组合所有消息
        return "\n\n".join(input_parts)

    async def _fallback_to_chat_completions(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float],
        max_tokens: Optional[int],
        response_format: ResponseFormat,
        timeout: Optional[int],
        **kwargs
    ) -> LLMResponse:
        """降级到传统的chat completions API"""
        logger.info("Using fallback chat completions API")

        formatted_messages = self.format_messages(messages)

        request_params = {
            "model": self.config.model,
            "messages": formatted_messages
        }

        # GPT-5 的特殊处理
        if "gpt-5" in self.config.model.lower():
            # GPT-5 使用 max_completion_tokens 而不是 max_tokens
            request_params["max_completion_tokens"] = max_tokens
            # GPT-5 nano 只支持默认temperature (1.0)
            # 不设置temperature参数，让它使用默认值
        else:
            request_params["max_tokens"] = max_tokens
            request_params["temperature"] = temperature

        if response_format == ResponseFormat.JSON:
            request_params["response_format"] = {"type": "json_object"}

        try:
            response = await self._client.post(
                self.chat_endpoint,
                json=request_params
            )

            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Chat completions API error: {error_detail}")
            response.raise_for_status()
            response_data = response.json()

            content = response_data["choices"][0]["message"]["content"]

            return LLMResponse(
                content=content,
                usage={
                    "prompt_tokens": response_data.get("usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": response_data.get("usage", {}).get("completion_tokens", 0),
                    "total_tokens": response_data.get("usage", {}).get("total_tokens", 0)
                },
                model=response_data.get("model", self.config.model),
                finish_reason=response_data["choices"][0].get("finish_reason", "stop")
            )

        except Exception as e:
            logger.error(f"Fallback API also failed: {e}")
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
                    delay = retry_delay * (2 ** (attempt - 1))
                    logger.info(f"GPT-5 retry attempt {attempt + 1}/{max_retries}, delay: {delay}s")
                    await asyncio.sleep(delay)

                response = await self.chat_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                    timeout=timeout,
                    **kwargs
                )

                return response

            except asyncio.TimeoutError:
                logger.warning(f"GPT-5 timeout on attempt {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise
            except Exception as e:
                logger.error(f"GPT-5 error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt == max_retries - 1:
                    raise

        raise Exception(f"Failed after {max_retries} retries")

    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "OpenAI GPT-5"

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        model_info = self.MODELS.get(self.config.model, {})
        return {
            "provider": self.get_provider_name(),
            "model": self.config.model,
            "model_name": model_info.get("name", self.config.model),
            "max_tokens": model_info.get("max_tokens", 128000),
            "context_window": model_info.get("context_window", 400000),
            "pricing": model_info.get("price_per_1k_tokens", {}),
            "base_url": self.config.base_url,
            "endpoint": self.responses_endpoint,
            "features": {
                "json_mode": True,
                "function_calling": True,
                "streaming": True,
                "vision": True,
                "reasoning": True,
                "reasoning_effort": True
            }
        }

    async def close(self):
        """关闭客户端连接"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("OpenAI GPT-5 LLM client closed")