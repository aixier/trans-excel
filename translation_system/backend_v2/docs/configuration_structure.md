# Backend V2 配置结构说明

## 🔧 配置分离设计

为了区分**任务拆解控制**和**LLM API配置**，我们重新设计了配置结构：

### 📊 1. 任务执行控制 (`task_execution`)

**用途**: 控制任务拆解、批次分组、并发执行等业务逻辑

```yaml
task_execution:
  # 批次控制 - 用于任务分组和执行控制
  batch_control:
    max_chars_per_batch: 1000      # 每批次最大字符数（用于任务拆解）
    max_concurrent_workers: 10     # 最大并发worker数

  # 拆解控制 - 用于任务分割
  split_control:
    max_task_chars: 500           # 单个任务最大字符数
    context_overlap: 50           # 上下文重叠字符数
    min_batch_size: 1             # 最小批次大小
```

### 🤖 2. LLM API配置 (`llm`)

**用途**: 控制LLM API调用参数，包括token限制、模型设置等

```yaml
llm:
  default_provider: qwen-plus

  providers:
    qwen-plus:
      enabled: true
      api_key: "sk-xxx"
      base_url: "https://dashscope.aliyuncs.com/api/v1"
      model: "qwen-plus"
      temperature: 0.3
      max_tokens: 8000              # LLM API最大输出token数（比任务控制大很多）
      timeout: 90
      max_retries: 3
      retry_delay: 3.0
```

## 🔍 关键差异对比

| 配置项 | 旧结构 | 新结构 | 用途 | 典型值 |
|--------|--------|--------|------|--------|
| **任务拆解控制** | `llm.batch_control.max_chars_per_batch` | `task_execution.batch_control.max_chars_per_batch` | 控制任务分组大小 | 1000 |
| **LLM Token限制** | `llm.providers.*.max_tokens` | `llm.providers.*.max_tokens` | LLM API输出限制 | 8000 |
| **单任务大小** | ❌ 未配置 | `task_execution.split_control.max_task_chars` | 单个任务字符限制 | 500 |
| **并发控制** | `llm.batch_control.max_concurrent_workers` | `task_execution.batch_control.max_concurrent_workers` | Worker并发数 | 10 |

## 📝 代码使用示例

### 1. 获取任务执行控制值

```python
from utils.config_manager import config_manager

# 获取任务拆解相关配置
max_chars_per_batch = config_manager.max_chars_per_batch        # 1000
max_concurrent_workers = config_manager.max_concurrent_workers  # 10
max_task_chars = config_manager.max_task_chars                 # 500
context_overlap = config_manager.context_overlap              # 50
```

### 2. 获取LLM API配置

```python
from services.llm.llm_factory import LLMFactory

# 创建LLM Provider时会自动读取max_tokens等配置
provider = LLMFactory.create_from_config_file(config, 'qwen-plus')
# provider.config.max_tokens = 8000（从配置文件读取）
```

## 🎯 配置原理说明

### 为什么需要分离？

1. **业务逻辑不同**:
   - `max_chars_per_batch` (1000): 用于控制**业务批次**大小，避免单批次任务过多
   - `max_tokens` (8000): 用于控制**LLM API**的输出长度，技术限制

2. **数值差异巨大**:
   - 任务控制值通常较小 (500-1000 字符)
   - LLM token限制较大 (4000-8000 tokens)

3. **配置独立性**:
   - 任务执行参数: 影响性能和资源使用
   - LLM API参数: 影响翻译质量和成本

### 实际使用场景

```
任务拆解流程:
原始文本(5000字符)
→ 按max_task_chars(500)拆分成10个任务
→ 按max_chars_per_batch(1000)分成5个批次
→ 每批次并发调用LLM
→ LLM使用max_tokens(8000)限制输出长度
```

## ⚡ 性能调优建议

### 1. 任务执行优化
- `max_chars_per_batch`: 1000-5000 (根据内存和性能调整)
- `max_concurrent_workers`: 5-20 (根据API限制调整)
- `max_task_chars`: 300-800 (根据翻译精度调整)

### 2. LLM API优化
- `max_tokens`: 4000-8000 (根据模型限制设置)
- `temperature`: 0.1-0.5 (翻译任务建议较低值)
- `timeout`: 60-120 (根据网络情况调整)

这样的配置分离使得系统更加清晰，便于调优和维护。