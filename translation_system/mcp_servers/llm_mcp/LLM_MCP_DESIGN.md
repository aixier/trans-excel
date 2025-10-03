# LLM MCP Server Design Document

## 目录
1. [概述](#概述)
2. [架构设计](#架构设计)
3. [功能模块](#功能模块)
4. [MCP工具设计](#mcp工具设计)
5. [数据流设计](#数据流设计)
6. [集成方案](#集成方案)
7. [技术选型](#技术选型)
8. [安全考虑](#安全考虑)

## 概述

### 项目定位
LLM MCP Server 是翻译系统的核心执行引擎，负责：
- 接收 Excel MCP 导出的翻译任务
- 调用 LLM API 执行批量翻译
- 管理翻译进度和状态
- 输出翻译结果文件

### 核心特性
- **多 LLM 支持**：OpenAI、Qwen、Anthropic、DeepSeek
- **批量处理**：智能批次管理，优化 API 调用
- **断点续传**：支持任务中断后继续
- **成本控制**：Token 使用统计和成本计算
- **质量保证**：翻译验证和错误重试
- **实时进度**：WebSocket 进度推送

## 架构设计

```
┌──────────────────────────────────────────────────────┐
│                    LLM MCP Server                     │
├──────────────────────────────────────────────────────┤
│                                                        │
│   ┌──────────────┐         ┌──────────────┐         │
│   │  HTTP/MCP    │         │  WebSocket   │         │
│   │   Gateway    │         │    Server    │         │
│   └──────┬───────┘         └──────┬───────┘         │
│          │                         │                  │
│          └──────────┬──────────────┘                 │
│                     │                                 │
│          ┌──────────▼──────────┐                     │
│          │    MCP Handler      │                     │
│          │  (工具路由和验证)    │                     │
│          └──────────┬──────────┘                     │
│                     │                                 │
│     ┌───────────────┼───────────────┐               │
│     │               │               │               │
│ ┌───▼────┐    ┌────▼────┐    ┌────▼────┐         │
│ │ Task   │    │ Batch   │    │Progress │         │
│ │Manager │    │Executor │    │Tracker  │         │
│ └────────┘    └─────────┘    └─────────┘         │
│                     │                               │
│     ┌───────────────┼───────────────┐              │
│     │               │               │              │
│ ┌───▼────┐    ┌────▼────┐    ┌────▼────┐        │
│ │  LLM   │    │  Prompt │    │  Cost   │        │
│ │Provider│    │ Manager │    │ Counter │        │
│ └────────┘    └─────────┘    └─────────┘        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 功能模块

### 1. 任务管理模块 (Task Manager)
**职责**：
- 解析上传的任务文件（Excel/JSON）
- 任务验证和预处理
- 任务状态管理
- 任务持久化

**核心类**：
```python
class TaskManager:
    def load_tasks(file_path: str) -> List[TranslationTask]
    def validate_tasks(tasks: List[TranslationTask]) -> ValidationResult
    def save_progress(session_id: str, progress: Dict)
    def restore_session(session_id: str) -> TranslationSession
```

### 2. 批次执行模块 (Batch Executor)
**职责**：
- 批次调度和并发控制
- 错误处理和重试
- 进度跟踪
- 结果聚合

**核心类**：
```python
class BatchExecutor:
    def execute_batch(batch: TranslationBatch) -> BatchResult
    def handle_failure(task: TranslationTask, error: Exception)
    def merge_results(results: List[BatchResult]) -> FinalResult
```

### 3. LLM 提供者模块 (LLM Provider)
**职责**：
- 统一的 LLM 接口
- 多模型支持
- Token 管理
- Rate limiting

**支持的提供者**：
```python
class LLMProvider(ABC):
    @abstractmethod
    async def translate(text: str, source_lang: str, target_lang: str, context: Dict) -> TranslationResult

class OpenAIProvider(LLMProvider)
class QwenProvider(LLMProvider)
class AnthropicProvider(LLMProvider)
class DeepSeekProvider(LLMProvider)
```

### 4. 提示词管理模块 (Prompt Manager)
**职责**：
- 动态提示词生成
- 上下文注入
- 特殊指令处理

**提示词模板**：
```python
class PromptTemplate:
    def build_translation_prompt(
        text: str,
        source_lang: str,
        target_lang: str,
        task_type: str,  # normal/yellow/blue
        context: Dict
    ) -> str
```

### 5. 进度跟踪模块 (Progress Tracker)
**职责**：
- 实时进度计算
- WebSocket 推送
- 统计信息收集

**进度数据**：
```python
class ProgressData:
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    current_batch: int
    total_batches: int
    estimated_time_remaining: int
    tokens_used: int
    estimated_cost: float
```

### 6. 成本计算模块 (Cost Counter)
**职责**：
- Token 使用统计
- 成本估算
- 预算控制

**成本模型**：
```python
class CostModel:
    provider: str
    model: str
    input_token_price: float  # per 1K tokens
    output_token_price: float  # per 1K tokens

class CostCounter:
    def calculate_cost(tokens: TokenUsage, model: CostModel) -> float
    def check_budget(current_cost: float, budget: float) -> bool
```

## MCP工具设计

### 1. llm_upload_tasks
**功能**：上传翻译任务文件
```json
{
  "name": "llm_upload_tasks",
  "description": "Upload translation tasks file (Excel/JSON)",
  "inputSchema": {
    "type": "object",
    "properties": {
      "token": {"type": "string", "description": "Auth token"},
      "file": {"type": "string", "description": "Base64 encoded file"},
      "file_url": {"type": "string", "description": "URL to download file"},
      "format": {"type": "string", "enum": ["excel", "json"], "description": "File format"}
    },
    "required": ["token"]
  }
}
```

### 2. llm_configure_translation
**功能**：配置翻译参数
```json
{
  "name": "llm_configure_translation",
  "description": "Configure translation settings",
  "inputSchema": {
    "type": "object",
    "properties": {
      "token": {"type": "string"},
      "session_id": {"type": "string"},
      "provider": {"type": "string", "enum": ["openai", "qwen", "anthropic", "deepseek"]},
      "model": {"type": "string"},
      "max_workers": {"type": "integer", "minimum": 1, "maximum": 20},
      "temperature": {"type": "number", "minimum": 0, "maximum": 2},
      "max_retries": {"type": "integer", "minimum": 0, "maximum": 5},
      "budget_limit": {"type": "number", "description": "Maximum cost in USD"}
    },
    "required": ["token", "session_id", "provider"]
  }
}
```

### 3. llm_start_translation
**功能**：开始执行翻译
```json
{
  "name": "llm_start_translation",
  "description": "Start translation execution",
  "inputSchema": {
    "type": "object",
    "properties": {
      "token": {"type": "string"},
      "session_id": {"type": "string"},
      "mode": {"type": "string", "enum": ["all", "failed_only", "specific_batches"]},
      "batch_ids": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["token", "session_id"]
  }
}
```

### 4. llm_get_progress
**功能**：获取翻译进度
```json
{
  "name": "llm_get_progress",
  "description": "Get translation progress",
  "inputSchema": {
    "type": "object",
    "properties": {
      "token": {"type": "string"},
      "session_id": {"type": "string"},
      "include_details": {"type": "boolean"}
    },
    "required": ["token", "session_id"]
  }
}
```

### 5. llm_pause_translation
**功能**：暂停翻译
```json
{
  "name": "llm_pause_translation",
  "description": "Pause translation execution",
  "inputSchema": {
    "type": "object",
    "properties": {
      "token": {"type": "string"},
      "session_id": {"type": "string"}
    },
    "required": ["token", "session_id"]
  }
}
```

### 6. llm_resume_translation
**功能**：恢复翻译
```json
{
  "name": "llm_resume_translation",
  "description": "Resume paused translation",
  "inputSchema": {
    "type": "object",
    "properties": {
      "token": {"type": "string"},
      "session_id": {"type": "string"}
    },
    "required": ["token", "session_id"]
  }
}
```

### 7. llm_get_results
**功能**：获取翻译结果
```json
{
  "name": "llm_get_results",
  "description": "Get translation results",
  "inputSchema": {
    "type": "object",
    "properties": {
      "token": {"type": "string"},
      "session_id": {"type": "string"},
      "format": {"type": "string", "enum": ["excel", "json", "csv"]},
      "include_failed": {"type": "boolean"}
    },
    "required": ["token", "session_id"]
  }
}
```

### 8. llm_export_results
**功能**：导出翻译结果
```json
{
  "name": "llm_export_results",
  "description": "Export translation results to file",
  "inputSchema": {
    "type": "object",
    "properties": {
      "token": {"type": "string"},
      "session_id": {"type": "string"},
      "format": {"type": "string", "enum": ["excel", "json", "csv"]},
      "merge_with_source": {"type": "boolean", "description": "Merge results with source Excel"}
    },
    "required": ["token", "session_id"]
  }
}
```

### 9. llm_get_statistics
**功能**：获取翻译统计
```json
{
  "name": "llm_get_statistics",
  "description": "Get translation statistics",
  "inputSchema": {
    "type": "object",
    "properties": {
      "token": {"type": "string"},
      "session_id": {"type": "string"}
    },
    "required": ["token", "session_id"]
  }
}
```

### 10. llm_validate_api_key
**功能**：验证 API Key
```json
{
  "name": "llm_validate_api_key",
  "description": "Validate LLM provider API key",
  "inputSchema": {
    "type": "object",
    "properties": {
      "token": {"type": "string"},
      "provider": {"type": "string"},
      "api_key": {"type": "string"}
    },
    "required": ["token", "provider", "api_key"]
  }
}
```

## 数据流设计

### 1. 任务上传流程
```
Client → Upload Excel/JSON
         ↓
      Parse Tasks
         ↓
      Validate Tasks
         ↓
      Create Session
         ↓
      Group into Batches
         ↓
      Return session_id
```

### 2. 翻译执行流程
```
Start Translation
      ↓
Load Configuration
      ↓
Initialize Provider
      ↓
┌─→ Get Next Batch
│     ↓
│  Execute Batch (Parallel)
│     ↓
│  Update Progress
│     ↓
│  Save Results
│     ↓
└─ More Batches? → Yes ─┘
      ↓ No
  Finalize Results
```

### 3. 进度推送流程
```
Task Execution
      ↓
Progress Update
      ↓
WebSocket Broadcast
      ↓
Client UI Update
```

## 集成方案

### 与 Excel MCP 集成

#### 工作流
1. Excel MCP 导出任务文件 (tasks_xxx.xlsx)
2. 用户下载任务文件
3. 上传到 LLM MCP (llm_upload_tasks)
4. 配置翻译参数 (llm_configure_translation)
5. 开始翻译 (llm_start_translation)
6. 监控进度 (llm_get_progress + WebSocket)
7. 导出结果 (llm_export_results)
8. 合并回原始 Excel（可选）

#### 数据格式兼容
```python
# Excel MCP 导出格式
class ExportedTask:
    task_id: str
    batch_id: str
    source_lang: str
    source_text: str
    target_lang: str
    target_text: str  # 空或已有翻译
    task_type: str  # normal/yellow/blue
    context: Dict

# LLM MCP 接收格式（相同）
class TranslationTask(ExportedTask):
    status: str = 'pending'  # pending/processing/completed/failed
    result: Optional[str] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    retry_count: int = 0
```

### 与前端集成

#### WebSocket 协议
```javascript
// 连接
ws = new WebSocket('ws://localhost:8023/ws/progress/{session_id}')

// 接收进度
ws.onmessage = (event) => {
  const progress = JSON.parse(event.data)
  // progress.type: 'progress' | 'batch_complete' | 'task_complete' | 'error'
  // progress.data: 具体数据
}
```

#### 前端页面设计
```html
<!-- 翻译执行页面 -->
<div id="translation-executor">
  <!-- 1. 上传区域 -->
  <div class="upload-section">
    <input type="file" accept=".xlsx,.json" />
    <button>Upload Tasks</button>
  </div>

  <!-- 2. 配置区域 -->
  <div class="config-section">
    <select name="provider">
      <option value="openai">OpenAI</option>
      <option value="qwen">Qwen</option>
    </select>
    <input type="number" name="max_workers" />
    <input type="number" name="temperature" />
  </div>

  <!-- 3. 控制按钮 -->
  <div class="controls">
    <button>Start</button>
    <button>Pause</button>
    <button>Resume</button>
    <button>Stop</button>
  </div>

  <!-- 4. 进度显示 -->
  <div class="progress">
    <div class="progress-bar"></div>
    <div class="stats">
      <span>Tasks: 100/500</span>
      <span>Batches: 2/10</span>
      <span>Cost: $1.23</span>
    </div>
  </div>

  <!-- 5. 结果预览 -->
  <div class="results">
    <table id="translation-results"></table>
  </div>

  <!-- 6. 导出按钮 -->
  <div class="export">
    <button>Export Results</button>
  </div>
</div>
```

## 技术选型

### 核心技术栈
- **语言**：Python 3.10+
- **框架**：
  - MCP (Model Context Protocol)
  - aiohttp (HTTP/WebSocket)
  - asyncio (异步处理)
- **LLM SDK**：
  - openai
  - dashscope (Qwen)
  - anthropic
- **数据处理**：
  - pandas
  - openpyxl
- **存储**：
  - Redis (可选，会话缓存)
  - SQLite (可选，任务持久化)

### 并发策略
```python
# 多级并发控制
MAX_CONCURRENT_BATCHES = 3  # 同时处理的批次数
MAX_WORKERS_PER_BATCH = 5   # 每批次的并发数
MAX_TOKENS_PER_REQUEST = 4000  # 每次请求的最大token数

# 使用 asyncio.Semaphore 控制并发
batch_semaphore = asyncio.Semaphore(MAX_CONCURRENT_BATCHES)
worker_semaphore = asyncio.Semaphore(MAX_WORKERS_PER_BATCH)
```

### 错误处理策略
```python
# 重试策略
RETRY_DELAYS = [1, 2, 5, 10, 30]  # 秒
MAX_RETRIES = 5

# 错误分类
class ErrorType(Enum):
    RATE_LIMIT = "rate_limit"      # 降低并发，延迟重试
    API_ERROR = "api_error"         # 立即重试
    INVALID_RESPONSE = "invalid"    # 记录并跳过
    NETWORK_ERROR = "network"       # 延迟重试
    BUDGET_EXCEEDED = "budget"      # 停止执行
```

## 安全考虑

### 1. API Key 管理
- 加密存储 API Keys
- 支持环境变量配置
- Key 轮换机制
- 权限隔离

### 2. Token 验证
- JWT Token 验证
- 权限检查：llm:translate, llm:export
- Session 隔离

### 3. 输入验证
- 文件大小限制（100MB）
- 任务数量限制（10000条/文件）
- 文本长度限制（10000字符/任务）
- 恶意内容检测

### 4. 成本控制
- 预算限制
- Token 使用配额
- 实时成本监控
- 自动停止机制

### 5. 数据隐私
- 任务数据加密传输
- 临时文件自动清理
- 日志脱敏
- GDPR 合规

## 性能优化

### 1. 批处理优化
```python
# 动态批次大小调整
def calculate_batch_size(avg_text_length: int) -> int:
    if avg_text_length < 100:
        return 20  # 短文本，更多并发
    elif avg_text_length < 500:
        return 10  # 中等文本
    else:
        return 5   # 长文本，减少并发
```

### 2. 缓存策略
- 相同文本的翻译缓存
- 提示词模板缓存
- LLM 响应缓存（可选）

### 3. 流式处理
- 大文件流式读取
- 结果流式写入
- 进度实时更新

### 4. 资源管理
- 连接池管理
- 内存使用监控
- 自动垃圾回收

## 监控指标

### 关键指标
1. **性能指标**
   - TPS (Translations Per Second)
   - 平均响应时间
   - 批次完成时间
   - 队列等待时间

2. **质量指标**
   - 翻译成功率
   - 重试率
   - 错误分布

3. **成本指标**
   - Token 使用量
   - API 调用次数
   - 单位成本

4. **系统指标**
   - CPU/内存使用率
   - 并发连接数
   - 队列长度

## 部署架构

### 单机部署
```yaml
services:
  llm_mcp:
    image: llm_mcp:latest
    ports:
      - "8023:8023"  # HTTP/MCP
      - "8024:8024"  # WebSocket
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - QWEN_API_KEY=${QWEN_API_KEY}
    volumes:
      - ./data:/data
      - ./logs:/logs
```

### 分布式部署
```yaml
# 使用 Redis 作为任务队列
services:
  llm_mcp_master:
    # 接收任务，分发到 workers

  llm_mcp_worker_1:
    # 执行翻译任务

  llm_mcp_worker_2:
    # 执行翻译任务

  redis:
    # 任务队列和缓存

  nginx:
    # 负载均衡
```

## 开发计划

### Phase 1: MVP (1周)
- [x] 设计文档
- [ ] 基础架构搭建
- [ ] 任务上传和解析
- [ ] OpenAI 提供者实现
- [ ] 单批次翻译执行
- [ ] 结果导出

### Phase 2: 核心功能 (2周)
- [ ] 多 LLM 提供者支持
- [ ] 批量并发执行
- [ ] 进度跟踪
- [ ] WebSocket 推送
- [ ] 错误处理和重试

### Phase 3: 高级功能 (2周)
- [ ] 断点续传
- [ ] 成本控制
- [ ] 翻译缓存
- [ ] 质量评估
- [ ] 监控和告警

### Phase 4: 优化和扩展 (持续)
- [ ] 性能优化
- [ ] 分布式支持
- [ ] 更多 LLM 提供者
- [ ] 自定义提示词
- [ ] A/B 测试

---

**版本**: v1.0.0
**日期**: 2025-10-03
**作者**: LLM MCP Team