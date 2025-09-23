"""
OpenAI LLM实现
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from openai import AsyncOpenAI
from .base_llm import BaseLLM, LLMConfig, LLMMessage, LLMResponse, ResponseFormat


logger = logging.getLogger(__name__)


class OpenAILLM(BaseLLM):
    """OpenAI LLM实现"""

    # OpenAI模型配置
    MODELS = {
        "gpt-4-turbo": {
            "name": "GPT-4 Turbo",
            "max_tokens": 4096,
            "context_window": 128000,
            "price_per_1k_tokens": {"input": 0.01, "output": 0.03}
        },
        "gpt-4": {
            "name": "GPT-4",
            "max_tokens": 8192,
            "context_window": 8192,
            "price_per_1k_tokens": {"input": 0.03, "output": 0.06}
        },
        "gpt-3.5-turbo": {
            "name": "GPT-3.5 Turbo",
            "max_tokens": 4096,
            "context_window": 16385,
            "price_per_1k_tokens": {"input": 0.001, "output": 0.002}
        },
        "gpt-3.5-turbo-16k": {
            "name": "GPT-3.5 Turbo 16K",
            "max_tokens": 4096,
            "context_window": 16385,
            "price_per_1k_tokens": {"input": 0.003, "output": 0.004}
        },
        "gpt-4o": {
            "name": "GPT-4o",
            "max_tokens": 4096,
            "context_window": 128000,
            "price_per_1k_tokens": {"input": 0.005, "output": 0.015}
        },
        "gpt-4o-mini": {
            "name": "GPT-4o Mini",
            "max_tokens": 16384,
            "context_window": 128000,
            "price_per_1k_tokens": {"input": 0.00015, "output": 0.0006}
        },
        "gpt-5-nano": {
            "name": "GPT-5 Nano",
            "max_tokens": 128000,
            "context_window": 400000,
            "price_per_1k_tokens": {"input": 0.05, "output": 0.40},
            "max_input_tokens": 272000,
            "max_output_tokens": 128000,
            "description": "Smallest GPT-5 variant with reasoning capabilities",
            "actual_model_id": "gpt-5-nano-2025-08-07",
            "supports_reasoning": True,
            "endpoint": "/v1/responses"
        },
        "gpt-5-nano-2025-08-07": {
            "name": "GPT-5 Nano (2025-08-07)",
            "max_tokens": 128000,
            "context_window": 400000,
            "price_per_1k_tokens": {"input": 0.05, "output": 0.40},
            "max_input_tokens": 272000,
            "max_output_tokens": 128000,
            "description": "Smallest GPT-5 variant with reasoning capabilities",
            "supports_reasoning": True,
            "endpoint": "/v1/responses"
        }
    }

    def __init__(self, config: LLMConfig):
        """初始化OpenAI LLM"""
        super().__init__(config)

        # 验证模型
        if config.model not in self.MODELS:
            # 允许自定义模型名称，但发出警告
            logger.warning(f"Using custom OpenAI model: {config.model} (not in predefined list)")
            logger.info("This model will be passed directly to OpenAI API")

        # OpenAI默认配置
        if not config.base_url:
            config.base_url = "https://api.openai.com/v1"

    async def initialize(self):
        """异步初始化OpenAI客户端"""
        self._client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            # OpenAI特定的配置
            organization=None,  # 可以从配置中读取
            max_retries=0  # 我们自己处理重试
        )
        logger.info(f"Initialized OpenAI LLM with model: {self.config.model}")

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

        # OpenAI响应格式处理
        if response_format == ResponseFormat.JSON:
            # GPT-4、GPT-3.5-turbo和GPT-5的新版本支持JSON模式
            if self.config.model in ["gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-5-nano", "gpt-5-nano-2025-08-07"]:
                request_params["response_format"] = {"type": "json_object"}
            # 对于不支持JSON模式的模型，在prompt中强调
            else:
                if formatted_messages and formatted_messages[0]["role"] == "system":
                    formatted_messages[0]["content"] += "\nYou must respond with valid JSON format only."

        # 添加OpenAI特定参数
        if "top_p" in kwargs:
            request_params["top_p"] = kwargs["top_p"]
        if "frequency_penalty" in kwargs:
            request_params["frequency_penalty"] = kwargs["frequency_penalty"]
        if "presence_penalty" in kwargs:
            request_params["presence_penalty"] = kwargs["presence_penalty"]
        if "seed" in kwargs:  # GPT-4 Turbo支持seed参数
            request_params["seed"] = kwargs["seed"]
        if "stop" in kwargs:
            request_params["stop"] = kwargs["stop"]
        if "n" in kwargs:  # 生成多个响应
            request_params["n"] = kwargs["n"]
        if "logprobs" in kwargs:  # 返回对数概率
            request_params["logprobs"] = kwargs["logprobs"]
        if "user" in kwargs:  # 用户标识符
            request_params["user"] = kwargs["user"]

        # Function calling支持
        if "functions" in kwargs:
            request_params["functions"] = kwargs["functions"]
        if "function_call" in kwargs:
            request_params["function_call"] = kwargs["function_call"]
        if "tools" in kwargs:  # 新版本的function calling
            request_params["tools"] = kwargs["tools"]
        if "tool_choice" in kwargs:
            request_params["tool_choice"] = kwargs["tool_choice"]

        try:
            response = await self._client.chat.completions.create(**request_params)

            # 提取响应内容
            content = response.choices[0].message.content

            # 如果有function call，处理它
            if response.choices[0].message.function_call:
                function_call = response.choices[0].message.function_call
                content = json.dumps({
                    "function_call": {
                        "name": function_call.name,
                        "arguments": function_call.arguments
                    }
                })

            # 如果有tool calls，处理它们
            if response.choices[0].message.tool_calls:
                tool_calls = []
                for tool_call in response.choices[0].message.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
                content = json.dumps({"tool_calls": tool_calls})

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
            logger.error(f"OpenAI API call failed: {e}")
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
                    logger.info(f"OpenAI retry attempt {attempt + 1}/{max_retries}, delay: {delay}s, timeout: {current_timeout}s")
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
                logger.warning(f"OpenAI timeout on attempt {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise
            except Exception as e:
                # OpenAI特定的错误处理
                error_message = str(e)
                if "rate limit" in error_message.lower():
                    # Rate limit错误，增加延迟
                    delay = retry_delay * (3 ** attempt)
                    logger.warning(f"OpenAI rate limit hit, waiting {delay}s")
                    await asyncio.sleep(delay)
                elif "context length" in error_message.lower():
                    # 上下文长度超限，不重试
                    logger.error("OpenAI context length exceeded")
                    raise
                else:
                    logger.error(f"OpenAI error on attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt == max_retries - 1:
                        raise

        raise Exception(f"Failed after {max_retries} retries")

    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "OpenAI"

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
                "json_mode": self.config.model in ["gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-5-nano", "gpt-5-nano-2025-08-07"],
                "function_calling": True,
                "streaming": True,
                "vision": self.config.model in ["gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-5-nano", "gpt-5-nano-2025-08-07"],  # 视觉能力
                "seed_deterministic": self.config.model in ["gpt-4-turbo", "gpt-4o", "gpt-5-nano", "gpt-5-nano-2025-08-07"],  # 支持seed参数
                "verbosity_control": self.config.model in ["gpt-5-nano", "gpt-5-nano-2025-08-07"],  # 支持verbosity参数
                "reasoning_effort": self.config.model in ["gpt-5-nano", "gpt-5-nano-2025-08-07"],  # 支持reasoning_effort参数
                "reasoning": self.config.model in ["gpt-5-nano", "gpt-5-nano-2025-08-07"]  # 支持reasoning能力
            }
        }

    async def close(self):
        """关闭客户端连接"""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("OpenAI LLM client closed")