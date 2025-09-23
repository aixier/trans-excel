# LLM Providers 组件

## 概述

LLM Providers 是一个可扩展的多LLM提供商管理组件，支持灵活切换不同的大语言模型服务。

## 支持的提供商

### 1. 阿里云通义千问 (Qwen)
- **模型**: qwen-plus, qwen-max, qwen-turbo, qwen-long
- **特点**: 支持搜索增强、超长上下文
- **配置示例**:
```python
{
    "provider": "qwen",
    "model": "qwen-plus",
    "api_key": "your_api_key",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "temperature": 0.3,
    "max_tokens": 4000
}
```

### 2. OpenAI
- **模型**: gpt-3.5-turbo, gpt-4, gpt-4-turbo, gpt-4o, gpt-4o-mini
- **特点**: Function calling、JSON模式、视觉能力
- **配置示例**:
```python
{
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "api_key": "your_api_key",
    "temperature": 0.3,
    "max_tokens": 4000
}
```

### 3. Google Gemini
- **模型**: gemini-pro, gemini-pro-vision, gemini-1.5-pro, gemini-1.5-flash
- **特点**: 多模态、百万级上下文
- **配置示例**:
```python
{
    "provider": "gemini",
    "model": "gemini-pro",
    "api_key": "your_api_key",
    "temperature": 0.3,
    "max_tokens": 4000
}
```

## 使用方法

### 1. 直接使用LLM工厂

```python
from llm_providers import LLMFactory, LLMMessage, ResponseFormat

# 创建LLM实例
llm = LLMFactory.create_llm(
    provider="qwen",
    api_key="your_api_key",
    model="qwen-plus",
    temperature=0.3
)

# 初始化
await llm.initialize()

# 发送消息
messages = [
    LLMMessage(role="system", content="You are a helpful assistant."),
    LLMMessage(role="user", content="Hello!")
]

# 获取响应
response = await llm.chat_completion(
    messages=messages,
    temperature=0.3,
    response_format=ResponseFormat.TEXT
)

print(response.content)

# 关闭连接
await llm.close()
```

### 2. 使用配置管理器

```python
from llm_providers import LLMConfigManager

# 创建配置管理器
manager = LLMConfigManager()

# 添加新配置
manager.add_profile("my-gpt4", {
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "your_api_key",
    "temperature": 0.2
})

# 设置活动配置
manager.set_active_profile("my-gpt4")

# 获取LLM实例
llm = await manager.get_llm()

# 使用LLM...
messages = [LLMMessage(role="user", content="Translate this to French: Hello")]
response = await llm.chat_completion(messages=messages)

# 切换到另一个配置
llm2 = await manager.get_llm("qwen-default")

# 清理
await manager.cleanup()
```

### 3. 在翻译引擎中使用

```python
from llm_providers import LLMConfigManager, LLMMessage, ResponseFormat
import json

class TranslationEngine:
    def __init__(self):
        self.llm_manager = LLMConfigManager()

    async def translate(self, text: str, target_language: str):
        # 获取当前LLM
        llm = await self.llm_manager.get_llm()

        # 构建消息
        messages = [
            LLMMessage(
                role="system",
                content=f"Translate Chinese to {target_language}. Return JSON format."
            ),
            LLMMessage(
                role="user",
                content=json.dumps({"text": text}, ensure_ascii=False)
            )
        ]

        # 获取翻译
        response = await llm.chat_completion_with_retry(
            messages=messages,
            response_format=ResponseFormat.JSON,
            temperature=0.3
        )

        # 解析结果
        result = json.loads(response.content)
        return result
```

## 配置文件格式

配置文件位于 `config/llm_configs.json`:

```json
{
  "profiles": {
    "qwen-default": {
      "provider": "qwen",
      "model": "qwen-plus",
      "api_key": "sk-xxx",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "temperature": 0.3,
      "max_tokens": 4000,
      "description": "阿里云通义千问Plus - 默认配置"
    },
    "openai-gpt35": {
      "provider": "openai",
      "model": "gpt-3.5-turbo",
      "api_key": "sk-xxx",
      "temperature": 0.3,
      "max_tokens": 4000,
      "description": "OpenAI GPT-3.5 Turbo"
    }
  },
  "active_profile": "qwen-default"
}
```

## 特性对比

| 特性 | Qwen | OpenAI | Gemini |
|------|------|---------|---------|
| JSON模式 | ✅ | ✅ | ❌ (通过Prompt实现) |
| Function Calling | ✅ | ✅ | ❌ |
| 流式输出 | ✅ | ✅ | ✅ |
| 视觉能力 | ❌ | ✅ (GPT-4V) | ✅ |
| 搜索增强 | ✅ | ❌ | ❌ |
| 超长上下文 | ✅ (qwen-long) | ✅ (128k) | ✅ (1M) |
| 价格 | 低 | 高 | 中 |

## 扩展新的提供商

1. 创建新的LLM类，继承自`BaseLLM`:

```python
from llm_providers.base_llm import BaseLLM, LLMConfig

class MyCustomLLM(BaseLLM):
    def __init__(self, config: LLMConfig):
        super().__init__(config)

    async def initialize(self):
        # 初始化客户端
        pass

    async def chat_completion(self, messages, **kwargs):
        # 实现聊天补全
        pass

    # 实现其他必需方法...
```

2. 在`llm_factory.py`中注册:

```python
from .my_custom_llm import MyCustomLLM

class LLMFactory:
    _provider_map = {
        # ...
        LLMProvider.CUSTOM: MyCustomLLM
    }
```

## 环境变量

建议在环境变量中设置API密钥：

```bash
export QWEN_API_KEY="your_qwen_api_key"
export OPENAI_API_KEY="your_openai_api_key"
export GEMINI_API_KEY="your_gemini_api_key"
```

## 错误处理

所有LLM类都实现了重试机制和错误处理：

- **超时重试**: 自动重试并增加超时时间
- **速率限制**: 指数退避策略
- **上下文超限**: 立即失败，不重试
- **健康检查**: `health_check()`方法测试连接

## 性能优化

1. **实例缓存**: ConfigManager会缓存LLM实例，避免重复创建
2. **并发控制**: 支持并发请求限制
3. **动态超时**: 根据文本长度自动调整超时时间
4. **批处理优化**: 支持批量请求处理

## 注意事项

1. API密钥安全：不要将密钥硬编码在代码中
2. 成本控制：注意不同模型的价格差异
3. 上下文限制：注意不同模型的上下文窗口大小
4. 响应格式：不是所有模型都原生支持JSON模式