# 后端逻辑和数据流程完整文档

## 📋 目录
1. [核心架构](#核心架构)
2. [数据模型](#数据模型)
3. [完整数据流程](#完整数据流程)
4. [API端点映射](#api端点映射)
5. [状态转换机制](#状态转换机制)
6. [错误处理](#错误处理)
7. [关键设计决策](#关键设计决策)

---

## 核心架构

### DataFrame Pipeline 架构

系统采用 **DataFrame Pipeline** 架构，每个Session代表一次转换：

```
input_state (ExcelDataFrame)
    → [rules] → tasks (TaskDataFrame)
    → [processor] → output_state (ExcelDataFrame)
```

### 关键设计原则

1. **数据状态连续性** - 每个Session管理一次完整的转换
2. **Session链式调用** - 通过parent_session_id实现多次转换串联
3. **懒加载机制** - DataFrame存储在文件，需要时才加载到内存
4. **时间戳追踪** - 每个关键操作都记录时间戳，用于缓存失效

---

## 数据模型

### 1. PipelineSession (核心Session模型)

**文件**: `models/pipeline_session.py`

```python
@dataclass
class PipelineSession:
    # 标识和时间
    session_id: str                         # UUID
    created_at: datetime
    last_accessed: datetime
    stage: TransformationStage              # 状态枚举

    # 输入
    input_state: ExcelDataFrame            # 输入数据（内存中）
    input_source: str                      # 'file' | 'parent_session'
    parent_session_id: str                 # 父Session ID（用于链式调用）

    # 配置
    rules: List[str]                       # ['empty', 'yellow', 'blue', 'caps']
    processor: str                         # 'llm_qwen' | 'uppercase' 等

    # 输出
    tasks: TaskDataFrameManager            # 拆分的任务表
    task_statistics: Dict                  # 任务统计
    output_state: ExcelDataFrame           # 输出数据（内存中）
    execution_statistics: Dict             # 执行统计

    # 元数据
    metadata: Dict                         # 文件路径、时间戳等
    child_session_ids: List[str]           # 子Session列表
```

**状态枚举**:
```python
class TransformationStage(Enum):
    CREATED = "created"                    # 刚创建
    INPUT_LOADED = "input_loaded"          # 输入已加载
    SPLIT_COMPLETE = "split_complete"      # 任务已拆分
    EXECUTING = "executing"                # 执行中
    COMPLETED = "completed"                # 完成
    FAILED = "failed"                      # 失败
```

### 2. ExcelDataFrame (统一的Excel数据结构)

**文件**: `models/excel_dataframe.py`

```python
class ExcelDataFrame:
    sheets: Dict[str, pd.DataFrame]        # {sheet_name: DataFrame}
    filename: str                          # 原始文件名
    excel_id: str                          # UUID
```

**DataFrame结构**（每个sheet）:
```
| key | CH | EN | TH | TW | color_key | comment_key | color_CH | comment_CH | ... |
|-----|----|----|----|----|-----------|-------------|----------|------------|-----|
```

- **数据列**: key, CH, EN, TH, TW 等
- **元数据列**: color_*, comment_* (存储颜色和注释信息)

### 3. TaskDataFrame (任务表结构)

**文件**: `models/task_dataframe.py`

```python
class TaskDataFrameManager:
    df: pd.DataFrame                       # 任务表
```

**任务表结构**:
```
| task_id | batch_id | sheet_name | row_idx | col_idx | col_name | task_type |
| source_text | target_lang | context | status | result | error | priority |
|---------|----------|------------|---------|---------|----------|-----------|
```

**任务类型**:
- `normal`: 普通翻译（空单元格）
- `yellow`: 黄色强制重译
- `blue`: 蓝色自我缩短
- `caps`: 大写转换

**任务状态**:
- `pending`: 待处理
- `processing`: 处理中
- `completed`: 已完成
- `failed`: 失败

---

## 完整数据流程

### 流程1: 翻译工作流 (Translation)

#### 阶段1: 上传和拆分

**请求**: `POST /api/tasks/split`

```json
{
  "file": <Excel文件>,
  "source_lang": "CH",
  "target_langs": ["EN", "TH"],
  "rule_set": "translation",           // 或 "caps_only"
  "parent_session_id": null,           // 首次为null
  "extract_context": true,
  "max_chars_per_batch": 1000
}
```

**后端流程**:

```
1. task_api.py: split()
   ├─ 创建Session: pipeline_session_manager.create_session()
   │  └─ stage = CREATED
   │
   ├─ 模式A (文件上传):
   │  ├─ excel_loader.load_excel() → ExcelDataFrame
   │  ├─ session.input_state = excel_df
   │  ├─ 保存到文件: input_file_path
   │  └─ stage = INPUT_LOADED
   │
   ├─ 模式B (继承父Session):
   │  ├─ 获取父Session的output_state
   │  ├─ session.input_state = parent.output_state
   │  └─ stage = INPUT_LOADED
   │
   ├─ 加载规则配置:
   │  ├─ config/rules.yaml
   │  └─ session.rules = ['empty', 'yellow', 'blue']  // 根据rule_set
   │
   ├─ 任务拆分: task_splitter.split_tasks()
   │  ├─ 遍历每个sheet和每个单元格
   │  ├─ 根据enabled_rules判断是否生成任务
   │  ├─ 生成TaskDataFrame
   │  └─ 批次分配: batch_allocator.allocate()
   │
   ├─ 保存任务:
   │  ├─ task_manager.df.to_parquet(task_file_path)
   │  ├─ session.tasks = task_manager
   │  ├─ session.metadata['task_file_path'] = task_file_path
   │  └─ stage = SPLIT_COMPLETE
   │
   └─ 返回响应:
      {
        "session_id": "xxx",
        "stage": "split_complete",
        "total_tasks": 100,
        "statistics": {...}
      }
```

**规则应用逻辑** (`task_splitter.py`):

```python
# 根据规则集确定enabled_rules
if rule_set == "translation":
    enabled_rules = ['empty', 'yellow', 'blue']
elif rule_set == "caps_only":
    enabled_rules = ['caps']

# 遍历每个单元格
for target_lang in target_langs:
    for row_idx, row in df.iterrows():
        # 优先级1: 目标单元格是蓝色 → blue任务
        if target_is_blue and 'blue' in enabled_rules:
            create_task(task_type='blue')

        # 优先级2: 源或EN是黄色 → yellow任务
        elif (source_is_yellow or en_is_yellow) and 'yellow' in enabled_rules:
            create_task(task_type='yellow')

        # 优先级3: 目标单元格为空 → normal任务
        elif target_is_empty and 'empty' in enabled_rules:
            create_task(task_type='normal')

        # 优先级4: CAPS sheet → caps任务
        if 'CAPS' in sheet_name and 'caps' in enabled_rules:
            create_task(task_type='caps')
```

#### 阶段2: 执行转换

**请求**: `POST /api/execute/start`

```json
{
  "session_id": "xxx",
  "processor": "llm_qwen",             // 或 "uppercase"
  "max_workers": 10,
  "glossary_config": {
    "enabled": true,
    "id": "default"
  }
}
```

**后端流程**:

```
1. execute_api.py: start_execution()
   ├─ 验证session存在且stage == SPLIT_COMPLETE
   ├─ session.processor = "llm_qwen"
   ├─ stage = EXECUTING
   │
   ├─ 创建LLM Provider:
   │  └─ llm_factory.create_provider(processor)
   │
   └─ 启动Worker Pool: worker_pool.start_execution()
      │
      ├─ 分组任务:
      │  ├─ 按batch_id分组
      │  ├─ 分离normal_batches和caps_batches
      │  └─ caps任务需要等normal完成后执行
      │
      ├─ 创建Worker:
      │  ├─ 创建10个normal workers
      │  └─ 从queue中取任务并发执行
      │
      ├─ Worker处理流程:
      │  └─ batch_executor.execute_batch()
      │     │
      │     ├─ 根据processor选择处理器:
      │     │  ├─ LLM Processor: llm_processor.process_batch()
      │     │  │  ├─ batch_translator.translate_batch_optimized()
      │     │  │  ├─ prompt_template.build_prompt()
      │     │  │  │  ├─ 检查glossary_config.enabled
      │     │  │  │  ├─ 匹配术语: glossary_manager.match_terms()
      │     │  │  │  └─ 注入术语到提示词
      │     │  │  └─ provider.translate_single()
      │     │  │
      │     │  └─ Uppercase Processor: uppercase_processor.process_batch()
      │     │     └─ text.upper()  // 仅处理ASCII字符
      │     │
      │     ├─ 更新任务状态:
      │     │  ├─ task.status = 'completed'
      │     │  ├─ task.result = translated_text
      │     │  └─ 保存到task_file_path
      │     │
      │     └─ WebSocket推送进度:
      │        └─ websocket_manager.send_progress()
      │
      ├─ 监控执行: _monitor_execution_with_caps()
      │  ├─ 等待normal workers完成
      │  ├─ 启动caps workers处理caps任务
      │  └─ 等待所有workers完成
      │
      └─ 完成后合并结果:
         ├─ 创建output_excel_df = copy.deepcopy(input_state)
         ├─ 遍历completed_tasks
         ├─ output_excel_df.sheets[sheet][row_idx, col_idx] = result
         │
         ├─ 保存到文件 (重要顺序):
         │  ├─ 1. 保存output_state到output_file_path
         │  ├─ 2. metadata['output_file_path'] = path
         │  ├─ 3. metadata['output_state_timestamp'] = ISO时间
         │  ├─ 4. session.output_state = output_excel_df (内存)
         │  └─ 5. stage = COMPLETED
         │
         └─ 记录完成时间
```

**关键时序修复** (解决缓存问题):

```python
# worker_pool.py:417-440
# ✅ 先保存文件，再设置内存，再更新状态
# 确保export请求到达时，文件路径和时间戳已存在

1. 保存到pickle文件
2. 记录output_file_path到metadata
3. 记录output_state_timestamp (ISO格式)
4. 设置到内存 session.output_state
5. 更新 stage = COMPLETED
```

#### 阶段3: 下载结果

**请求**: `GET /api/download/{session_id}`

**后端流程**:

```
1. download_api.py: download_translated_excel()
   │
   ├─ 验证session存在
   │
   ├─ ✅ 检查1: 执行完成
   │  └─ if stage != "completed": 返回错误
   │
   ├─ ✅ 检查2: output_state存在
   │  └─ if not output_state: 返回错误
   │
   ├─ ✅ 检查3: 缓存是否有效
   │  ├─ 获取export_timestamp和output_state_timestamp
   │  ├─ 比较时间: export_time >= output_time
   │  ├─ 如果缓存有效: 返回缓存文件
   │  └─ 如果缓存过期: 删除缓存文件
   │
   └─ 生成新导出:
      └─ excel_exporter.export_final_excel()
         │
         ├─ 获取output_state (懒加载)
         ├─ 获取task_manager (懒加载)
         │
         ├─ 创建Workbook
         ├─ 遍历每个sheet:
         │  ├─ 写入数据 (仅数据列，不含color_*/comment_*)
         │  ├─ 从translation_map替换翻译结果
         │  ├─ 应用格式 (颜色、注释)
         │  └─ 自动调整列宽
         │
         ├─ 保存到output/目录
         ├─ 记录metadata:
         │  ├─ exported_file = file_path
         │  └─ export_timestamp = ISO时间
         │
         └─ 返回FileResponse
```

**导出时的翻译结果优先级**:

```python
# excel_exporter.py:158-168
# 按task_type排序，caps任务会覆盖normal任务

sheet_tasks = sheet_tasks.sort_values('task_type', ascending=True)
# 'caps' < 'normal' 按字母序

translation_map = {}
for task in sheet_tasks:
    # 后处理的任务会覆盖先处理的
    translation_map[(row_idx, col_name)] = task['result']
```

### 流程2: 大写转换工作流 (CAPS)

**完整链路**:

```
1. 翻译阶段 (session_A):
   POST /api/tasks/split  (rule_set="translation")
   POST /api/execute/start (processor="llm_qwen")
   → session_A.output_state (包含翻译结果)

2. 大写转换阶段 (session_B):
   POST /api/tasks/split
     {
       "parent_session_id": "session_A",  // 继承session_A的output
       "rule_set": "caps_only"            // 仅生成caps任务
     }
   POST /api/execute/start (processor="uppercase")
   → session_B.output_state (EN列大写)

3. 下载:
   GET /api/download/session_B
```

**Session链关系**:

```
session_A (翻译)
  ├─ parent_session_id: null
  ├─ input_state: 上传的Excel
  ├─ output_state: 翻译结果
  └─ child_session_ids: ["session_B"]

session_B (大写)
  ├─ parent_session_id: "session_A"
  ├─ input_state: session_A.output_state
  ├─ output_state: 大写转换结果
  └─ child_session_ids: []
```

---

## API端点映射

### 核心API (按功能分类)

#### 1. Session管理

| 端点 | 方法 | 功能 | 返回 |
|-----|-----|-----|-----|
| `/api/sessions/list` | GET | 列出所有session | session列表 |
| `/api/sessions/detail/{id}` | GET | 获取session详情 | session完整信息 |
| `/api/sessions/{id}` | DELETE | 删除session | 成功/失败 |

#### 2. 任务拆分

| 端点 | 方法 | 功能 | 关键参数 |
|-----|-----|-----|---------|
| `/api/tasks/split` | POST | 上传+拆分 | file, rule_set, parent_session_id |
| `/api/tasks/split/status/{id}` | GET | 拆分状态 | - |
| `/api/tasks/export/{id}` | GET | 导出任务表 | export_type (tasks/dataframe) |

**export_type区别**:
- `tasks`: 导出TaskDataFrame (任务分解表)
- `dataframe`: 导出完整ExcelDataFrame (包含元数据列)

#### 3. 执行控制

| 端点 | 方法 | 功能 | 关键参数 |
|-----|-----|-----|---------|
| `/api/execute/start` | POST | 开始执行 | processor, glossary_config |
| `/api/execute/status/{id}` | GET | 执行状态 | - |
| `/api/execute/stop/{id}` | POST | 停止执行 | - |
| `/api/execute/pause/{id}` | POST | 暂停执行 | - |
| `/api/execute/resume/{id}` | POST | 恢复执行 | - |

#### 4. 下载导出

| 端点 | 方法 | 功能 | 说明 |
|-----|-----|-----|-----|
| `/api/download/{id}` | GET | 下载最终结果 | 仅数据列 |
| `/api/download/{id}/info` | GET | 下载信息 | 检查是否可下载 |
| `/api/download/{id}/files` | DELETE | 清理缓存 | 删除导出文件 |

#### 5. 术语表管理

| 端点 | 方法 | 功能 | 说明 |
|-----|-----|-----|-----|
| `/api/glossaries/list` | GET | 列出术语表 | - |
| `/api/glossaries/{id}` | GET | 获取术语表 | - |
| `/api/glossaries/upload` | POST | 上传术语表 | 支持JSON |
| `/api/glossaries/{id}` | DELETE | 删除术语表 | - |

#### 6. 监控和调试

| 端点 | 方法 | 功能 |
|-----|-----|-----|
| `/api/monitor/status/{id}` | GET | 监控执行状态 |
| `/api/monitor/summary/{id}` | GET | 执行摘要 |
| `/api/debug/session/{id}/info` | GET | 调试信息 |
| `/api/logs/query` | GET | 查询日志 |

---

## 状态转换机制

### TransformationStage 状态图

```
CREATED
  ↓ (上传文件或继承父Session)
INPUT_LOADED
  ↓ (任务拆分)
SPLIT_COMPLETE
  ↓ (开始执行)
EXECUTING
  ↓ (执行完成)
COMPLETED

任何阶段可能 → FAILED
```

### 关键状态检查点

1. **拆分前**: `stage == CREATED && input_state != null`
2. **执行前**: `stage == SPLIT_COMPLETE && tasks != null`
3. **下载前**: `stage == COMPLETED && output_state != null`

---

## 错误处理

### 1. Session不存在

```python
if not session:
    raise HTTPException(404, "Session not found")
```

### 2. 状态不匹配

```python
if session.stage != TransformationStage.SPLIT_COMPLETE:
    raise HTTPException(400, f"Cannot execute: stage is {stage}, expected split_complete")
```

### 3. 数据缺失

```python
if not session.output_state:
    raise HTTPException(400, "No output data available")
```

### 4. 缓存过期

```python
if export_time < output_time:
    # 自动删除过期缓存
    os.remove(cached_file)
    # 重新生成
```

### 5. 文件加载失败

```python
try:
    excel_df = ExcelDataFrame.load_from_pickle(path)
except Exception as e:
    logger.error(f"Failed to load: {e}")
    return None
```

---

## 关键设计决策

### 1. 为什么使用DataFrame Pipeline？

**问题**: 之前的架构混合了多种数据结构，难以维护

**解决**: 统一使用ExcelDataFrame，元数据存储在DataFrame列中

**优势**:
- 数据和元数据一体化
- 易于序列化和持久化
- 支持Pandas强大的数据操作

### 2. 为什么Session=一次转换？

**问题**: 之前的Session试图管理多个阶段，状态复杂

**解决**: 每个Session只负责一次转换，通过parent_session_id链接

**优势**:
- 状态清晰，易于理解
- 支持灵活的工作流组合
- 失败时影响范围小

### 3. 为什么需要懒加载？

**问题**: ExcelDataFrame可能很大，全部加载到内存浪费资源

**解决**: DataFrame存储在文件，metadata记录路径，需要时才加载

**优势**:
- 内存占用小
- 支持大文件处理
- Session可以长期保存

### 4. 为什么需要时间戳缓存失效？

**问题**: 执行完成前的导出请求会生成错误的缓存文件

**解决**:
- 记录output_state_timestamp（数据完成时间）
- 记录export_timestamp（导出时间）
- 比较两者判断缓存是否有效

**优势**:
- 彻底解决缓存问题
- 自动清理过期缓存
- 用户体验好（不需要手动清理）

### 5. 为什么caps任务要等normal任务？

**问题**: caps任务需要基于翻译结果进行大写转换

**解决**: Worker Pool使用两个队列，caps_queue等normal_queue清空后才处理

**优势**:
- 保证依赖关系
- 结果覆盖顺序正确
- 逻辑清晰

---

## 完整性检查清单

✅ **数据流完整**:
- [x] 上传 → 拆分 → 执行 → 导出 全流程打通
- [x] 支持文件上传和Session继承两种输入方式
- [x] 支持翻译和大写两种处理器

✅ **状态管理完整**:
- [x] 6种状态清晰定义
- [x] 状态转换有验证
- [x] 支持状态查询

✅ **Session管理完整**:
- [x] 创建、获取、删除
- [x] 父子关系管理
- [x] 缓存持久化

✅ **错误处理完整**:
- [x] Session不存在
- [x] 状态不匹配
- [x] 数据缺失
- [x] 文件加载失败
- [x] 缓存过期处理

✅ **性能优化完整**:
- [x] 懒加载机制
- [x] 批次并发执行
- [x] 导出文件缓存
- [x] WebSocket实时推送

✅ **功能扩展完整**:
- [x] 术语表管理
- [x] 规则系统
- [x] 多处理器支持
- [x] 监控和日志

---

## 结论

后端逻辑和数据流程**已完整**，涵盖：

1. ✅ 完整的数据流程（上传→拆分→执行→导出）
2. ✅ 清晰的Session生命周期管理
3. ✅ 完善的状态转换机制
4. ✅ 健全的错误处理
5. ✅ 灵活的功能扩展接口

**已解决的关键问题**:
- ✅ 缓存时序问题（通过时间戳比较）
- ✅ Session链式调用（通过parent_session_id）
- ✅ 规则动态控制（通过enabled_rules）
- ✅ 任务依赖执行（通过双队列机制）

**可以开始前端开发**，后端提供完整的API支持！
