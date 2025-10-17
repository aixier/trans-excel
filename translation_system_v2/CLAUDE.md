# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ 核心架构理念（必读）

**在进行任何开发之前，请先阅读：** `.claude/ARCHITECTURE_PRINCIPLES.md`

### 三大核心原则

#### 1. 数据状态的连续性
**原始数据 = 结果数据 = 数据状态**

不存在"原始"和"结果"的本质区别，所有数据都是某个时刻的状态快照：
- Excel原始文件 = 数据状态0
- Excel翻译后 = 数据状态1
- Excel大写转换后 = 数据状态2
- 任何状态都可以作为下一个转换的输入

#### 2. 任务拆分表是唯一的中间数据
任务表描述"如何从状态N变成状态N+1"，它不是数据本身，而是状态转换的指令集。

#### 3. 统一的转换流程
```
数据状态N → [拆分器] → 任务表 → [转换器] → 数据状态N+1
                                               ↓
                                          可继续流转
```

这个流程可以无限循环，每个阶段都遵循相同的模式。

**详细说明请查看：**
- `.claude/ARCHITECTURE_PRINCIPLES.md` - 完整的架构原则
- `.claude/PIPELINE_REFACTOR_PLAN.md` - 最新的Pipeline重构方案（推荐阅读）
- `backend_v2/SIMPLIFIED_ARCHITECTURE.md` - 简化架构设计文档
- `backend_v2/PIPELINE_ARCHITECTURE.md` - 管道式架构设计

---

## Overview

This is a Translation System V2 - an Excel-based translation management system that processes game localization files using LLMs (Large Language Models). The system analyzes Excel files containing multilingual text, splits them into translation tasks, executes translations via LLM APIs, and exports the results back to Excel format.

## Architecture

### 新架构模型（基于数据流理念）

系统采用**数据状态流转**模式，所有操作都遵循统一的转换流程：

```
数据状态 → [拆分器] → 任务表 → [转换器] → 新数据状态 → 下一个阶段...
```

**示例流程**（CAPS翻译）：
```
状态0(原始Excel)
    ↓ [拆分] 规则: 空单元格、黄色单元格
任务表1(翻译任务)
    ↓ [转换] LLM翻译处理器
状态1(翻译后Excel)
    ↓ [拆分] 规则: CAPS sheet
任务表2(大写任务)
    ↓ [转换] 大写处理器(依赖任务表1)
状态2(最终Excel)
```

### Core Components

- **Backend (FastAPI)**: Located in `backend_v2/`, handles all business logic, LLM integrations, and task processing
- **Frontend (Vanilla JS)**: Located in `frontend_v2/`, single-page application with hash routing, no framework dependencies
- **Memory-Only Mode**: All data stored in memory, no database persistence, sessions timeout after 8 hours
- **Task DataFrame**: 任务拆分表 - 描述状态转换的唯一中间数据
- **Data State**: Excel数据状态 - 可以无限流转的数据快照
- **PipelineSession**: 管道会话 - 每个Session管理一次转换（一个输入状态→一个输出状态）
- **Session Chaining**: 会话链接 - 通过parent_session_id实现多阶段Pipeline

### 系统的三种数据格式 ⭐

系统只有三种数据格式，它们对应架构原则中的核心概念：

#### 1. Excel文件格式（.xlsx）
**角色**：用户可见的外部格式
```
用户视角：input.xlsx → 系统处理 → output.xlsx
```
- **用途**：外部边界的数据交换格式
- **出现位置**：用户上传、用户下载
- **特点**：人类可读、可编辑、标准Excel格式

#### 2. ExcelDataFrame（数据状态）⭐⭐⭐
**角色**：内部数据状态表示（对应架构原则中的"数据状态N"）

**核心理念：DataFrame Pipeline** 🎯

整个系统就是一个 **DataFrame 的 Pipeline**！所有数据状态都是**相同格式的 DataFrame**：

```python
# models/excel_dataframe.py
@dataclass
class ExcelDataFrame:
    sheets: Dict[str, pd.DataFrame]  # DataFrame包含所有信息
    filename: str
    excel_id: str

# DataFrame 列结构（统一格式）：
# - 数据列：key, CH, EN, TH, PT, VN
# - 颜色列：color_CH, color_EN, color_TH, color_PT, color_VN
# - 注释列：comment_CH, comment_EN, comment_TH, comment_PT, comment_VN
```

**DataFrame 示例**：
```
key              CH         color_CH   comment_CH        EN           color_EN  comment_EN
PET_SKILL_1      强化宠物... #FFFFFF00  格式占位符有误    Enhance...   #FFFFFF00  原文：...
ELEMENT_BOX_2    初阶墨水... None       None             example1     #FFFFFF00  None
```

**为什么这样设计？**
- ✅ **格式一致性**：state_0, state_1, state_2 ... 都是相同格式的 DataFrame
- ✅ **可级联性**：任何状态都可以作为下一个转换的输入
- ✅ **单一数据源**：所有信息在 DataFrame 中，不需要单独的字典
- ✅ **简化处理**：处理器输入/输出都是 DataFrame，保持格式一致

**旧设计（已废弃）**：
```python
# ❌ 旧设计：分离存储
class ExcelDataFrame:
    sheets: Dict[str, pd.DataFrame]  # 只有数据列
    color_map: Dict  # 单独的颜色字典
    comment_map: Dict  # 单独的注释字典
```
问题：格式不一致，无法实现 DataFrame Pipeline

- **用途**：表示某个时刻的完整数据快照
- **出现位置**：
  - ✅ Split的**输入**（session.input_state）
  - ✅ Execute的**输出**（session.output_state）
  - ✅ Session之间的继承（parent的output_state → child的input_state）
- **特点**：内存对象、100%保留所有数据和元数据、零拷贝传递、格式一致可级联

#### 3. TaskDataFrame（任务表）
**角色**：状态转换的指令集（对应架构原则中的"任务拆分表"）
```python
# models/task_dataframe.py
class TaskDataFrameManager:
    df: DataFrame with columns:
        - task_id, sheet_name, row_idx, col_idx
        - source_text, target_lang
        - task_type, status, result
        # ... 任务执行信息
```
- **用途**：描述"如何从状态N变成状态N+1"
- **出现位置**：
  - ✅ Split的**输出**（session.tasks）
  - ✅ Execute的**输入**（tasks + input_state一起）
- **特点**：不是数据本身，而是对数据的操作描述

#### 数据流转规则

**格式转换边界（唯一的I/O点）**：
```
上传：.xlsx文件 → [解析] → ExcelDataFrame
下载：ExcelDataFrame → [序列化] → .xlsx文件
```

**系统内部流转（无格式转换）**：
```
Split:   ExcelDataFrame → TaskDataFrame
Execute: ExcelDataFrame + TaskDataFrame → ExcelDataFrame
继承：    parent.output_state (ExcelDataFrame) → child.input_state (ExcelDataFrame)
```

#### 完整Pipeline示例

**阶段1（翻译）：**
```
input.xlsx                    # 格式1：Excel文件
    ↓ 上传解析
ExcelDataFrame (state_0)      # 格式2：数据状态
    ↓ Split
TaskDataFrame (tasks_1)       # 格式3：任务表
    ↓ Execute (需要state_0 + tasks_1)
ExcelDataFrame (state_1)      # 格式2：数据状态
```

**阶段2（CAPS）- 内存继承：**
```
ExcelDataFrame (state_1)      # 格式2：数据状态（从上一阶段继承，无需文件转换）
    ↓ Split
TaskDataFrame (tasks_2)       # 格式3：任务表
    ↓ Execute (需要state_1 + tasks_2)
ExcelDataFrame (state_2)      # 格式2：数据状态
    ↓ 下载序列化
output.xlsx                   # 格式1：Excel文件
```

**关键点**：
- ✅ 上传文件和从父Session继承都得到**相同格式**（ExcelDataFrame）
- ✅ Split输入ExcelDataFrame，输出TaskDataFrame
- ✅ Execute输入ExcelDataFrame + TaskDataFrame，输出ExcelDataFrame
- ✅ 系统内部流转零拷贝，只有外部边界需要格式转换

### Key Design Patterns

1. **Data State Flow**: 数据状态连续流转，任何输出都可作为下一个输入
2. **Session-per-Transformation**: 每个Session管理一次转换，不是多个状态
3. **Parent-Child Session Chaining**: Session通过parent_session_id链接，实现多阶段Pipeline
4. **Configuration-Driven Processing**: Rules和Processors通过YAML配置，由Factory创建
5. **Task-Driven Transformation**: 通过任务表驱动数据转换，而非直接修改
6. **Rule-Based Splitting**: 拆分器使用可配置规则，而非硬编码逻辑
7. **Modular Processors**: 转换器只关心任务执行，不关心数据来源
8. **Worker Pool Pattern**: Concurrent execution using configurable worker pools (default 10 workers)
9. **Batch Processing**: Tasks grouped by character count (max 50,000 chars per batch) for efficient LLM calls
10. **WebSocket Real-time Updates**: Progress monitoring via WebSocket connections

## 开发规范（必须遵守）

### ✅ 正确的开发方式

1. **分离拆分和转换**
   ```python
   # ✅ 正确：分两个阶段
   tasks = splitter.split(data_state, rules)  # 拆分
   new_state = transformer.execute(data_state, tasks)  # 转换

   # ❌ 错误：在拆分时执行转换
   tasks = splitter.split_and_translate(data_state)
   ```

2. **状态独立性**
   ```python
   # ✅ 正确：每个状态可以独立使用
   state_1 = load_excel("translated.xlsx")
   tasks = splitter.split(state_1, rules=[CapsRule])

   # ❌ 错误：假设一定是从原始文件开始
   if not is_original_file(data_state):
       raise Error("Must start from original")
   ```

3. **转换器依赖管理**
   ```python
   # ✅ 正确：通过context传递依赖
   state_2 = transformer.execute(
       state_1,
       tasks_2,
       context={'previous_tasks': tasks_1}
   )

   # ❌ 错误：转换器内部查找依赖
   state_2 = transformer.execute_with_lookup(state_1, tasks_2)
   ```

### ❌ 禁止的做法

1. **不要在拆分阶段创建依赖其他任务的任务**
   ```python
   # ❌ CAPS任务不应该在翻译前创建
   tasks = splitter.split(original_excel, rules=[
       NormalTranslation,
       CapsUppercase  # 此时翻译还没执行！
   ])
   ```

2. **不要在转换器中执行拆分逻辑**
   ```python
   # ❌ LLM转换器不应该处理CAPS任务
   def translate(task):
       if task['type'] == 'caps':
           # 不要在这里做大写转换！
           return task['source'].upper()
   ```

3. **不要混淆数据状态和任务表**
   ```python
   # ❌ 任务表不应该存储完整数据
   task['full_excel_data'] = excel_df

   # ✅ 任务表只存储位置和操作
   task['sheet_name'] = 'Sheet1'
   task['row_idx'] = 0
   ```

### 添加新功能时的步骤

1. **确定是拆分规则还是转换处理器**
2. **实现独立的类（不依赖现有逻辑）**
3. **通过配置或编排器组装到流程**
4. **更新架构文档说明新增功能**

**详细规范请查看：** `.claude/ARCHITECTURE_PRINCIPLES.md`

## Development Commands

### Backend Setup and Running

⚠️ **IMPORTANT**: Always use `python3` command, NOT `python`, to avoid compatibility issues.

```bash
# Navigate to backend
cd backend_v2

# Install dependencies
pip3 install -r requirements.txt

# Run the backend server (MUST use python3)
python3 main.py
# Server runs on http://localhost:8013 by default

# Run specific test files
python3 test_api_flow.py
python3 test_batch_allocator_max_chars.py
python3 test_translation_flow.py

# Run unit tests
python3 -m pytest tests/
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend_v2

# Serve with Python (no build needed - pure HTML/JS/CSS)
python -m http.server 8080

# Or use Node.js
npx http-server -p 8080

# Access at http://localhost:8080
```

### Docker Deployment (Optional)

```bash
# Build and run with Docker
docker build -t translation-system .
docker run -p 8013:8013 translation-system
```

## Configuration

### Backend Configuration

Main config files:
- `backend_v2/config/config.yaml` - 系统配置
- `backend_v2/config/rules.yaml` - 拆分规则配置（新增）
- `backend_v2/config/processors.yaml` - 处理器配置（新增）

Key configuration parameters in `config.yaml`:
- `task_execution.batch_control.max_chars_per_batch`: Max characters per LLM batch (default: 1000)
- `task_execution.batch_control.max_concurrent_workers`: Max concurrent workers (default: 10)
- `llm.providers`: Configure different LLM providers (OpenAI, Qwen, etc.)
- `llm.default_provider`: Set default LLM provider (default: qwen-plus)

### Rules Configuration (`config/rules.yaml`)

定义拆分规则和规则集：
```yaml
rules:
  empty:
    class: services.splitter.rules.empty_cell.EmptyCellRule
    priority: 5
    enabled: true

  caps:
    class: services.splitter.rules.caps_sheet.CapsSheetRule
    priority: 3
    enabled: true
    requires_translation_first: true  # CAPS需要翻译后才能执行

rule_sets:
  translation:  # 翻译规则集
    - empty
    - yellow
    - blue

  caps_only:    # CAPS规则集
    - caps
```

### Processors Configuration (`config/processors.yaml`)

定义处理器和处理器集：
```yaml
processors:
  llm_qwen:
    class: services.llm.qwen_provider.QwenProvider
    type: llm_translation
    enabled: true

  uppercase:
    class: services.processors.uppercase_processor.UppercaseProcessor
    type: text_transform
    enabled: true
    requires_llm: false

processor_sets:
  default_translation:
    processor: llm_qwen
    max_workers: 10

  caps_transform:
    processor: uppercase
    max_workers: 20
```

### LLM Providers

Currently supported providers in `backend_v2/services/llm/`:
- **OpenAI** (`openai_provider.py`): GPT-4, GPT-3.5
- **Qwen** (`qwen_provider.py`): Alibaba Cloud's Qwen models
- Base class for custom providers: `base_provider.py`

To add a new LLM provider, extend `BaseLLMProvider` and register in `llm_factory.py`.

## Key APIs

### Task Management (新架构)

**Split API（合并了Analyze）**
```
POST /api/tasks/split
Body: {
  "file": <file_upload>,         // 上传新文件
  "source_lang": "CH",
  "target_langs": ["EN", "JP"],
  "rule_set": "translation"       // 使用哪个规则集
}
或
Body: {
  "parent_session_id": "xxx",     // 从父Session继承数据
  "rule_set": "caps_only"         // 使用不同的规则集
}

Response: {
  "session_id": "new-session-id",
  "parent_session_id": "xxx",     // 如果有
  "tasks_count": 100,
  "stage": "SPLIT_COMPLETED"
}
```

**Execute API（新增processor参数）**
```
POST /api/execute/start
Body: {
  "session_id": "xxx",
  "processor": "llm_qwen",        // 指定处理器
  "max_workers": 10
}
或
Body: {
  "session_id": "xxx",
  "processor": "uppercase",       // CAPS处理器
  "max_workers": 20
}
```

**Status APIs**
- `GET /api/tasks/status/{session_id}` - Get task split status
- `GET /api/execute/status/{session_id}` - Get execution status
- `GET /api/tasks/export/{session_id}` - Export tasks as Excel

### Results & Download
- `GET /api/download/{session_id}` - Download translated Excel
- `GET /api/download/{session_id}/info` - Get download info
- `GET /api/download/{session_id}/summary` - Get translation summary

### WebSocket
- `WS /api/websocket/progress/{session_id}` - Real-time progress updates

## Task Processing Flow

### 新架构：Multi-Stage Pipeline

每个阶段都是独立的Session，通过parent_session_id链接：

**阶段1：翻译 (Translation Stage)**
1. **Split**: 上传Excel，使用translation规则集拆分任务
   - `POST /api/tasks/split` with file + rule_set="translation"
   - 创建Session 1，生成翻译任务
2. **Execute**: 使用LLM处理器执行翻译
   - `POST /api/execute/start` with processor="llm_qwen"
   - 并发处理，实时监控
3. **Download**: 下载翻译后的Excel（数据状态1）
   - `GET /api/download/{session_id}`

**阶段2：CAPS转换 (CAPS Stage) - 可选**
1. **Split**: 使用Session 1的输出，拆分CAPS任务
   - `POST /api/tasks/split` with parent_session_id=session1 + rule_set="caps_only"
   - 创建Session 2，生成CAPS任务（此时source_text已有翻译内容）
2. **Execute**: 使用Uppercase处理器执行CAPS
   - `POST /api/execute/start` with processor="uppercase"
   - 快速处理（简单转换）
3. **Download**: 下载最终Excel（数据状态2）
   - `GET /api/download/{session_id}`

### 单个Session内的处理流程

1. **Split**: 根据规则拆分任务
2. **Batch**: Tasks grouped into batches by character count (dynamic sizing)
3. **Execute**: Batches processed concurrently by worker pool
4. **Monitor**: Real-time progress via WebSocket
5. **Complete**: Session进入COMPLETED状态，可下载或作为下一阶段输入

### Task Types (Based on Cell Colors)

- **Normal (white/no color)**: Standard translation tasks
- **Yellow**: Re-translation tasks (high priority)
- **Blue**: Text simplification tasks (medium priority)
- **CAPS**: Uppercase conversion tasks (requires translation first)

## Important Architecture Details

### Session Management (新架构)

The system uses `PipelineSessionManager` (`backend_v2/utils/pipeline_session_manager.py`) that manages session chains:

**核心变化：**
- **一个Session = 一次转换**（不再管理多个状态）
- **Parent-Child链接**：Sessions通过parent_session_id关联
- **独立可测试**：每个Session都可以独立验证
- **配置驱动**：Rules和Processors通过YAML配置

**Session结构** (`models/pipeline_session.py`):
```python
@dataclass
class PipelineSession:
    session_id: str
    stage: TransformationStage  # CREATED/SPLIT_COMPLETED/EXECUTION_COMPLETED

    # Input
    input_state: ExcelDataFrame
    input_source: str  # 'file' or 'parent_session'
    parent_session_id: Optional[str]

    # Configuration
    rules: List[str]  # 规则名称列表
    processor: Optional[str]  # 处理器名称

    # Output
    tasks: TaskDataFrameManager
    output_state: ExcelDataFrame

    # Chaining
    child_session_ids: List[str]
```

**Session生命周期：**
1. CREATED - Session创建，input_state已加载
2. SPLIT_COMPLETED - 任务拆分完成，tasks已生成
3. EXECUTION_COMPLETED - 任务执行完成，output_state已生成
4. （可选）作为parent_session被下一个Session使用

**老架构问题：**
- ❌ 一个Session管理多个状态（state_0, state_1, state_2）
- ❌ 高耦合，18+模块依赖session_manager
- ❌ 难以测试单个阶段
- ❌ CAPS任务在翻译前创建，source_text为空

**新架构优势：**
- ✅ 每个Session职责单一
- ✅ 通过parent_session_id显式链接
- ✅ 每个阶段独立测试
- ✅ CAPS任务在翻译后创建，source_text有值

### Task DataFrame Structure

Main columns in the task DataFrame (`backend_v2/models/task_dataframe.py`):
- `task_id`: Unique identifier
- `batch_id`: Batch grouping for LLM calls
- `source_text`, `target_lang`: Translation input/output
- `status`: pending/processing/completed/failed
- `result`: Translation result
- `row_idx`, `col_idx`: Excel position
- `task_type`: normal/yellow/blue

### Worker Pool Architecture

**多用户并发架构** (`backend_v2/services/executor/`):
- **WorkerPoolManager** (`worker_pool_manager.py`): 管理多个session的worker pool
  - 为每个session创建独立的WorkerPool实例
  - 提供session级别的生命周期管理
  - 支持自动清理已完成的pool
- **WorkerPool** (`worker_pool.py`): 单个session的并发执行器
  - 每个实例绑定一个session_id
  - Configurable concurrent workers (1-50 per session)
  - Automatic retry with exponential backoff
  - Rate limiting for API calls
  - Dynamic batch size adjustment
- **多用户场景**:
  - 用户A执行session_1翻译，用户B同时执行session_2的CAPS，互不干扰
  - 每个session可独立控制（start/stop/pause/resume）
  - API通过session_id路由到对应的WorkerPool实例

## Testing

### Backend Testing

```bash
# Run all unit tests
cd backend_v2
python -m pytest tests/ -v

# Run specific test scenarios
python test_api_flow.py  # Test complete API flow
python test_batch_allocator_max_chars.py  # Test batch allocation
python test_translation_flow.py  # Test translation pipeline
python test_yellow_en_reference.py  # Test yellow cell logic

# Test with real Excel files
python test_real_excel.py  # Requires sample Excel in tests/test_data/
```

### Frontend Testing

The frontend includes test pages in `frontend_v2/test_pages/`:
- Open individual HTML files to test specific features
- Check browser console for debug output
- Verify WebSocket connections and API calls

## Common Development Tasks

### Adding a New Rule (拆分规则)

1. Create rule class in `backend_v2/services/splitter/rules/`
   ```python
   class MyCustomRule:
       def match(self, cell_context) -> bool:
           # 判断是否匹配
           return True/False

       def extract_task(self, cell_context) -> Dict:
           # 提取任务信息
           return {...}
   ```
2. Add configuration in `config/rules.yaml`
   ```yaml
   rules:
     my_custom:
       class: services.splitter.rules.my_custom.MyCustomRule
       priority: 5
       enabled: true
   ```
3. Add to rule set if needed
   ```yaml
   rule_sets:
     my_workflow:
       - my_custom
       - empty
   ```
4. Use via API: `POST /api/tasks/split` with `rule_set="my_workflow"`

### Adding a New Processor (处理器)

1. Create processor class in `backend_v2/services/processors/`
   ```python
   class MyProcessor:
       def process(self, task: Dict) -> str:
           # 处理任务，返回结果
           return result
   ```
2. Add configuration in `config/processors.yaml`
   ```yaml
   processors:
     my_processor:
       class: services.processors.my_processor.MyProcessor
       type: custom
       enabled: true
   ```
3. Use via API: `POST /api/execute/start` with `processor="my_processor"`

### Adding a New LLM Provider

1. Create provider class in `backend_v2/services/llm/`
2. Extend `BaseLLMProvider`
3. Implement `translate_batch()` method
4. Add to `config/processors.yaml`
   ```yaml
   processors:
     llm_my_provider:
       class: services.llm.my_provider.MyProvider
       type: llm_translation
       config:
         model: my-model
       enabled: true
   ```
5. Use via API: `POST /api/execute/start` with `processor="llm_my_provider"`

### Modifying Translation Prompts

Edit `backend_v2/services/llm/prompt_template.py`:
- Modify prompt templates for different task types
- Adjust context extraction logic
- Change output format requirements

### Adjusting Batch Processing

Edit `backend_v2/services/batch_allocator.py`:
- Modify `max_chars_per_batch` calculation
- Adjust batch grouping logic
- Change priority assignment

### Debugging Session Issues

Common session-related files:
- `backend_v2/utils/session_manager.py` - Session storage
- `backend_v2/models/session_state.py` - Session state model
- `backend_v2/api/session_api.py` - Session API endpoints

## Performance Tuning

### Key Parameters

In `config.yaml`:
- `max_chars_per_batch`: Increase for fewer API calls, decrease for faster response
- `max_concurrent_workers`: Increase for higher throughput, watch for rate limits
- `checkpoint_interval`: Frequency of optional file checkpoints (if enabled)

### Monitoring

Access performance metrics:
- `GET /api/monitor/status/{session_id}` - Task statistics
- `GET /api/monitor/pool` - Worker pool status
- WebSocket `/api/websocket/monitor` - Real-time metrics

## Migration Guide: Old to New Architecture

### 核心变化

**Old Architecture (当前):**
```python
# 一个Session管理所有状态
POST /api/analyze/upload  # 上传并分析
POST /api/tasks/split     # 拆分（包含CAPS任务）
POST /api/execute/start   # 执行（LLM自动识别任务类型）
GET  /api/download/{session_id}
```

**New Architecture (目标):**
```python
# 阶段1：翻译
POST /api/tasks/split     # 上传+分析+拆分（合并了analyze）
  Body: {file: ..., rule_set: "translation"}
  → session_id_1

POST /api/execute/start
  Body: {session_id: session_id_1, processor: "llm_qwen"}

GET /api/download/{session_id_1}  # 翻译后的Excel

# 阶段2：CAPS（可选）
POST /api/tasks/split
  Body: {parent_session_id: session_id_1, rule_set: "caps_only"}
  → session_id_2

POST /api/execute/start
  Body: {session_id: session_id_2, processor: "uppercase"}

GET /api/download/{session_id_2}  # 最终Excel
```

### 关键差异

| 方面 | Old | New |
|------|-----|-----|
| Session职责 | 管理多个状态 | 管理一次转换 |
| CAPS任务 | 翻译前创建（source_text为空） | 翻译后创建（source_text有值） |
| 规则配置 | 硬编码在task_splitter.py | YAML配置文件 |
| 处理器选择 | 自动识别 | 显式指定 |
| 阶段链接 | 隐式（同一Session） | 显式（parent_session_id） |
| 独立测试 | 困难 | 简单 |

### 迁移检查清单

- [ ] 删除task_splitter.py中的CAPS硬编码逻辑（273-294行）
- [ ] 合并Analyze API到Split API
- [ ] 修改Split API支持file或parent_session_id
- [ ] 修改Execute API支持processor参数
- [ ] 创建RuleFactory和ProcessorFactory
- [ ] 添加config/rules.yaml和config/processors.yaml
- [ ] 实现UppercaseProcessor
- [ ] 更新前端测试页面支持两阶段流程
- [ ] 编写Session链接的单元测试
- [ ] 更新API文档

详细实施计划请查看：`.claude/PIPELINE_REFACTOR_PLAN.md`

## Known Limitations

### 当前架构限制

1. **Memory-Only Architecture**: No data persistence, sessions lost on restart
2. **No Horizontal Scaling**: Cannot distribute across multiple servers
3. **8-Hour Session Timeout**: Fixed timeout, not configurable per session
4. **CAPS任务数据完整性问题**: CAPS任务在翻译前创建，source_text为空（新架构已解决）

### 新架构改进

✅ **解决的问题:**
- Session职责单一，易于测试和维护
- CAPS任务在翻译后创建，数据完整性保证
- 配置驱动，扩展性强
- 显式依赖管理，易于理解
- **多用户并发支持** ⭐ NEW:
  - 每个session拥有独立的WorkerPool实例
  - 多个用户可以同时执行不同session的任务
  - WorkerPoolManager统一管理所有session的执行状态
  - 支持session级别的独立控制（start/stop/pause/resume）

⚠️ **仍然存在的限制:**
- Memory-Only（短期内不变）
- 8-Hour Timeout（短期内不变）
- No Horizontal Scaling（短期内不变）

## Troubleshooting

### Backend Won't Start
- Check port 8013 is available
- Verify Python 3.8+ installed
- Ensure all requirements installed: `pip install -r requirements.txt`

### Translation Fails
- Check LLM API keys in environment variables or config
- Verify network connectivity to LLM endpoints
- Review logs for rate limiting errors
- Check `max_chars_per_batch` isn't too high for model limits

### Frontend Can't Connect
- Verify backend is running on expected port
- Check CORS settings in backend config
- Ensure WebSocket connections aren't blocked
- Review browser console for errors

### Session Lost
- Sessions expire after 8 hours
- Server restart clears all sessions
- No recovery mechanism - must re-upload file