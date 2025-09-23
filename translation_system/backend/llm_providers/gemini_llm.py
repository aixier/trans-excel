"""
Google Gemini LLM实现
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional

# 尝试导入Google Gemini SDK
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    HarmCategory = None
    HarmBlockThreshold = None

from .base_llm import BaseLLM, LLMConfig, LLMMessage, LLMResponse, ResponseFormat


logger = logging.getLogger(__name__)


class GeminiLLM(BaseLLM):
    """Google Gemini LLM实现"""

    # Gemini模型配置
    MODELS = {
        "gemini-pro": {
            "name": "Gemini Pro",
            "max_tokens": 32768,
            "context_window": 32768,
            "price_per_1k_tokens": {"input": 0.00125, "output": 0.00375}
        },
        "gemini-pro-vision": {
            "name": "Gemini Pro Vision",
            "max_tokens": 4096,
            "context_window": 16384,
            "price_per_1k_tokens": {"input": 0.00125, "output": 0.00375}
        },
        "gemini-1.5-pro": {
            "name": "Gemini 1.5 Pro",
            "max_tokens": 8192,
            "context_window": 1048576,  # 1M tokens
            "price_per_1k_tokens": {"input": 0.00125, "output": 0.00375}
        },
        "gemini-1.5-flash": {
            "name": "Gemini 1.5 Flash",
            "max_tokens": 8192,
            "context_window": 1048576,  # 1M tokens
            "price_per_1k_tokens": {"input": 0.000075, "output": 0.0003}
        }
    }

    def __init__(self, config: LLMConfig):
        """初始化Gemini LLM"""
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Gemini SDK is not installed. Please install: pip install google-generativeai")
        super().__init__(config)

        # 验证模型
        if config.model not in self.MODELS:
            logger.warning(f"Unknown Gemini model: {config.model}, using gemini-pro")
            config.model = "gemini-pro"

        # Gemini特定配置
        self._model = None
        self._chat = None

    async def initialize(self):
        """异步初始化Gemini客户端"""
        # 配置API密钥
        genai.configure(api_key=self.config.api_key)

        # 创建模型实例
        generation_config = {
            "temperature": self.config.temperature,
            "max_output_tokens": self.config.max_tokens,
            "top_p": 0.95,
            "top_k": 40
        }

        # 安全设置（放宽限制以适应翻译任务）
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        self._model = genai.GenerativeModel(
            model_name=self.config.model,
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        logger.info(f"Initialized Gemini LLM with model: {self.config.model}")

    def _convert_messages_to_gemini_format(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """将消息转换为Gemini格式"""
        gemini_messages = []
        system_prompt = ""

        for msg in messages:
            if msg.role == "system":
                # Gemini不支持system角色，将其添加到第一个用户消息
                system_prompt = msg.content
            elif msg.role == "user":
                content = msg.content
                if system_prompt:
                    content = f"{system_prompt}\n\n{content}"
                    system_prompt = ""  # 只添加一次
                gemini_messages.append({"role": "user", "parts": [content]})
            elif msg.role == "assistant":
                gemini_messages.append({"role": "model", "parts": [msg.content]})

        # 如果只有system消息，创建一个用户消息
        if system_prompt and not gemini_messages:
            gemini_messages.append({"role": "user", "parts": [system_prompt]})

        return gemini_messages

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

        if not self._model:
            await self.initialize()

        # 使用提供的参数或默认值
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens

        # 更新生成配置
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 40)
        }

        # Gemini特定：候选数量
        if "candidate_count" in kwargs:
            generation_config["candidate_count"] = kwargs["candidate_count"]

        # Gemini特定：停止序列
        if "stop_sequences" in kwargs:
            generation_config["stop_sequences"] = kwargs["stop_sequences"]

        # 转换消息格式
        gemini_messages = self._convert_messages_to_gemini_format(messages)

        # 处理JSON响应格式
        if response_format == ResponseFormat.JSON:
            # 在提示中添加JSON格式要求
            if gemini_messages:
                last_msg = gemini_messages[-1]["parts"][0]
                gemini_messages[-1]["parts"][0] = last_msg + "\n\nPlease respond with valid JSON format only. The response must be a valid JSON object."

        try:
            # 创建聊天会话
            chat = self._model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])

            # 发送最后一条消息并获取响应
            last_message = gemini_messages[-1]["parts"][0] if gemini_messages else ""

            # 异步执行（Gemini SDK目前主要是同步的，这里用asyncio包装）
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                chat.send_message,
                last_message,
                generation_config
            )

            # 提取响应内容
            content = response.text

            # 验证JSON格式（如果需要）
            if response_format == ResponseFormat.JSON:
                # 尝试清理响应（去除可能的markdown标记）
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

                if not self.validate_response_format(content, response_format):
                    raise ValueError("Response is not valid JSON format")

            # 构建响应（Gemini不直接提供token使用信息）
            return LLMResponse(
                content=content,
                usage={
                    "prompt_tokens": 0,  # Gemini API不提供详细的token统计
                    "completion_tokens": 0,
                    "total_tokens": 0
                },
                model=self.config.model,
                finish_reason="stop"
            )

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
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
                    logger.info(f"Gemini retry attempt {attempt + 1}/{max_retries}, delay: {delay}s")
                    await asyncio.sleep(delay)

                # 执行API调用
                response = await self.chat_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                    timeout=timeout,
                    **kwargs
                )

                return response

            except Exception as e:
                error_message = str(e)
                # Gemini特定的错误处理
                if "quota" in error_message.lower() or "rate" in error_message.lower():
                    # 配额或速率限制
                    delay = retry_delay * (3 ** attempt)
                    logger.warning(f"Gemini rate/quota limit hit, waiting {delay}s")
                    await asyncio.sleep(delay)
                elif "safety" in error_message.lower():
                    # 安全过滤触发，不重试
                    logger.error("Gemini safety filter triggered")
                    raise
                else:
                    logger.error(f"Gemini error on attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt == max_retries - 1:
                        raise

        raise Exception(f"Failed after {max_retries} retries")

    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return "Google Gemini"

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        model_info = self.MODELS.get(self.config.model, {})
        return {
            "provider": self.get_provider_name(),
            "model": self.config.model,
            "model_name": model_info.get("name", self.config.model),
            "max_tokens": model_info.get("max_tokens", 4096),
            "context_window": model_info.get("context_window", 32768),
            "pricing": model_info.get("price_per_1k_tokens", {}),
            "features": {
                "json_mode": False,  # Gemini不原生支持JSON模式
                "function_calling": False,  # 当前版本不支持
                "streaming": True,
                "vision": "vision" in self.config.model,  # 视觉能力
                "multimodal": True,  # 多模态能力
                "large_context": self.config.model in ["gemini-1.5-pro", "gemini-1.5-flash"]  # 超大上下文
            }
        }

    async def close(self):
        """关闭客户端连接"""
        # Gemini SDK不需要显式关闭连接
        self._model = None
        self._chat = None
        logger.info("Gemini LLM client closed")