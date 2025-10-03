# Excel MCP v2.0 Architecture Documentation

## 目录
1. [系统概述](#系统概述)
2. [核心架构](#核心架构)
3. [模块设计](#模块设计)
4. [数据流](#数据流)
5. [工具设计](#工具设计)
6. [会话管理](#会话管理)
7. [异步处理](#异步处理)
8. [错误处理](#错误处理)

## 系统概述

Excel MCP v2.0 是一个基于 Model Context Protocol (MCP) 的 Excel 处理和翻译任务管理服务器。它提供了完整的 Excel 文件分析、任务拆分、批次分配和导出功能。

### 主要特性
- **双协议支持**：同时支持 MCP stdio 和 HTTP 协议
- **异步处理**：基于任务队列的异步处理架构
- **颜色识别**：支持黄色（重翻译）和蓝色（缩短）任务类型识别
- **智能批次分配**：自动将任务分配到合理大小的批次
- **会话管理**：内存会话管理，单一 session_id 贯穿全流程
- **多格式导出**：支持 Excel、JSON、CSV 格式导出

## 核心架构

```
┌─────────────────────────────────────────────────────────┐
│                     Excel MCP v2.0                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐        ┌──────────────┐               │
│  │   HTTP API   │        │  MCP stdio   │               │
│  │  (port 8021) │        │   Protocol   │               │
│  └──────┬───────┘        └──────┬───────┘               │
│         │                        │                        │
│         └────────────┬───────────┘                       │
│                      │                                    │
│            ┌─────────▼──────────┐                        │
│            │    MCP Handler     │                        │
│            │  (路由和验证层)     │                        │
│            └─────────┬──────────┘                        │
│                      │                                    │
│     ┌────────────────┼────────────────┐                  │
│     │                │                │                  │
│ ┌───▼────┐    ┌─────▼─────┐   ┌─────▼─────┐           │
│ │Session │    │   Task    │   │   Task    │           │
│ │Manager │    │   Queue   │   │  Exporter │           │
│ └────────┘    └───────────┘   └───────────┘           │
│                      │                                    │
│     ┌────────────────┼────────────────┐                  │
│     │                │                │                  │
│ ┌───▼────┐    ┌─────▼─────┐   ┌─────▼─────┐           │
│ │ Excel  │    │   Task    │   │  Excel   │           │
│ │Analyzer│    │ Splitter  │   │  Loader  │           │
│ └────────┘    └───────────┘   └──────────┘           │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## 模块设计

### 1. 入口层 (`server.py`)
- **职责**：启动服务器，处理命令行参数
- **功能**：
  - MCP stdio 服务器（标准模式）
  - HTTP 服务器（`--http` 模式）
  - 静态文件服务
  - CORS 配置

### 2. 处理层 (`mcp_handler.py`)
- **职责**：处理 MCP 工具调用，路由到具体服务
- **主要方法**：
  ```python
  handle_tool_call(tool_name, arguments) -> Dict
  _handle_excel_analyze(arguments, payload)
  _handle_excel_split_tasks(arguments, payload)
  _handle_excel_export_tasks(arguments, payload)
  # ... 其他工具处理方法
  ```

### 3. 服务层

#### 3.1 任务队列服务 (`services/task_queue.py`)
```python
class TaskQueue:
    async def submit_analysis_task(session_id, file_data, file_url, filename, options)
    async def submit_task_split(session_id, source_lang, target_langs, extract_context, context_options)
    async def submit_export_task(session_id, export_format, include_context)
    async def _process_queue()
    async def _process_task(task)
```

**任务类型**：
- `analysis` - Excel 分析任务
- `split` - 任务拆分任务
- `export` - 导出任务

#### 3.2 Excel 分析服务 (`services/excel_analyzer.py`)
```python
class ExcelAnalyzer:
    def analyze(excel_df, options) -> AnalysisResult
    def _analyze_language_detection(excel_df)
    def _analyze_statistics(excel_df)
    def _analyze_format(excel_df)
```

**分析内容**：
- 语言检测（源语言和目标语言）
- 统计信息（行数、列数、单元格数）
- 任务预估（normal/yellow/blue 任务数）
- 格式分析（颜色分布、注释）

#### 3.3 任务拆分服务 (`services/task_splitter_service.py`)
```python
class TaskSplitterService:
    def split_excel(excel_df, source_lang, target_langs, extract_context, context_options) -> Dict
    def _identify_columns(lang_columns, source_lang, target_langs)
    def _extract_tasks(df, sheet_name, source_col, target_cols, ...)
    def allocate_batches(tasks, max_chars_per_batch=50000)
    def _generate_summary(tasks)
```

**任务类型判定逻辑**：
1. **蓝色任务 (BLUE)**：源单元格或目标单元格为蓝色，需要缩短
2. **黄色任务 (YELLOW)**：源单元格或目标单元格为黄色，需要重翻译
3. **普通任务 (NORMAL)**：目标单元格为空，需要新翻译

#### 3.4 导出服务 (`services/task_exporter.py`)
```python
class TaskExporter:
    def export(tasks, session_id, format='excel', filename=None) -> str
    def export_to_excel(tasks, session_id, filename)
    def export_to_json(tasks, session_id, filename)
    def export_to_csv(tasks, session_id, filename)
```

### 4. 工具层

#### 4.1 颜色检测 (`utils/color_detector.py`)
- 基于 YAML 配置文件 (`config/color_config.yaml`)
- 支持三种匹配模式：pattern、hex、RGB

#### 4.2 语言映射 (`utils/language_mapper.py`)
```python
class LanguageMapper:
    def map_language(column_name) -> Optional[str]
    def detect_languages(columns) -> Dict[str, str]
```

支持的语言代码：
- CH/CN (中文)
- EN (英文)
- TR (土耳其语)
- TH (泰语)
- PT (葡萄牙语)
- VN (越南语)
- IND (印尼语)
- ES (西班牙语)

#### 4.3 会话管理 (`utils/session_manager.py`)
```python
class SessionManager:
    def create_session(session_type='excel') -> SessionData
    def get_session(session_id) -> Optional[SessionData]
    def update_session(session_id, **kwargs)
    def cleanup_expired_sessions()
```

### 5. 数据模型

#### 5.1 会话数据 (`models/session_data.py`)
```python
class SessionData:
    session_id: str
    status: SessionStatus
    progress: int
    excel_df: Optional[ExcelDataFrame]
    analysis: Optional[Dict]
    tasks: List[Dict]
    tasks_summary: Dict
    has_analysis: bool
    has_tasks: bool
    metadata: Dict
    error: Optional[Dict]
```

#### 5.2 Excel 数据框架 (`models/excel_dataframe.py`)
```python
class ExcelDataFrame:
    filename: str
    excel_id: str
    sheets: Dict[str, pd.DataFrame]
    color_map: Dict[str, Dict[Tuple[int, int], str]]
    comment_map: Dict[str, Dict[Tuple[int, int], str]]
```

#### 5.3 任务模型 (`models/task_models.py`)
```python
class TaskType(Enum):
    NORMAL = "normal"
    YELLOW = "yellow"
    BLUE = "blue"

class TaskSummary:
    total_tasks: int
    batch_count: int
    total_chars: int
    task_breakdown: Dict[str, int]
    language_distribution: Dict[str, int]
    estimated_cost: float
```

## 数据流

### 1. 分析流程
```
User Upload → excel_analyze → Task Queue → Excel Loader → Excel Analyzer → Session Update → Response
```

### 2. 拆分流程
```
Split Request → excel_split_tasks → Task Queue → Task Splitter → Batch Allocator → Session Update → Response
```

### 3. 导出流程
```
Export Request → excel_export_tasks → Task Queue → Task Exporter → File Generation → Session Update → Download URL
```

## 工具设计

### 分析工具组 (6个)

#### 1. excel_analyze
**功能**：分析 Excel 文件结构和内容
**输入**：
- token: 认证令牌
- file_url/file: 文件源
- options: 分析选项

**输出**：
- session_id: 会话ID
- status: 状态
- message: 消息

#### 2. excel_get_status
**功能**：获取会话状态
**输入**：
- token: 认证令牌
- session_id: 会话ID

**输出**：
- status: 当前状态
- progress: 进度百分比
- has_analysis: 是否完成分析
- has_tasks: 是否有任务
- result: 分析结果（如果完成）

#### 3. excel_get_sheets
**功能**：获取工作表列表
**输入**：
- token: 认证令牌
- session_id: 会话ID

**输出**：
- sheets: 工作表信息列表

#### 4. excel_parse_sheet
**功能**：解析特定工作表
**输入**：
- token: 认证令牌
- session_id: 会话ID
- sheet_name: 工作表名称
- rows: 行数限制

**输出**：
- data: 工作表数据
- metadata: 元数据

#### 5. excel_convert_to_json
**功能**：转换为 JSON 格式
**输入**：
- token: 认证令牌
- session_id: 会话ID
- sheet_name: 工作表名称

**输出**：
- data: JSON 数据
- row_count: 行数
- col_count: 列数

#### 6. excel_convert_to_csv
**功能**：转换为 CSV 格式
**输入**：
- token: 认证令牌
- session_id: 会话ID
- sheet_name: 工作表名称

**输出**：
- csv_content: CSV 内容
- row_count: 行数
- col_count: 列数

### 任务工具组 (4个)

#### 7. excel_split_tasks
**功能**：拆分翻译任务
**输入**：
- token: 认证令牌
- session_id: 会话ID
- source_lang: 源语言
- target_langs: 目标语言列表
- extract_context: 是否提取上下文
- context_options: 上下文选项

**输出**：
- session_id: 会话ID
- status: 状态
- message: 消息

#### 8. excel_get_tasks
**功能**：获取任务列表
**输入**：
- token: 认证令牌
- session_id: 会话ID
- preview_limit: 预览数量限制

**输出**：
- status: 状态
- result: 任务结果
  - summary: 任务摘要
  - preview_tasks: 任务预览

#### 9. excel_get_batches
**功能**：获取批次信息
**输入**：
- token: 认证令牌
- session_id: 会话ID

**输出**：
- session_id: 会话ID
- batches: 批次列表

#### 10. excel_export_tasks
**功能**：导出任务
**输入**：
- token: 认证令牌
- session_id: 会话ID
- format: 导出格式 (excel/json/csv)
- include_context: 是否包含上下文

**输出**：
- session_id: 会话ID
- status: 状态
- download_url: 下载链接（完成后）
- export_path: 导出路径（完成后）

## 会话管理

### 会话生命周期
```
Created → Processing/Analyzing → Completed → [Splitting] → Completed → [Exporting] → Completed
                ↓                     ↓                        ↓                        ↓
             Failed               Failed                   Failed                  Failed
```

### 会话状态 (SessionStatus)
- **CREATED**: 会话创建
- **PROCESSING**: 处理中（通用）
- **ANALYZING**: 分析中
- **SPLITTING**: 拆分中
- **COMPLETED**: 完成
- **FAILED**: 失败

### 会话清理
- 默认过期时间：8小时
- 自动清理：每小时执行一次
- 手动清理：通过 `cleanup_expired_sessions()` 方法

## 异步处理

### 任务队列机制
```python
# 提交任务
await task_queue.submit_analysis_task(...)

# 异步处理
asyncio.create_task(self._process_queue())

# 任务执行
await asyncio.to_thread(blocking_function, ...)
```

### 轮询机制
前端通过定时轮询获取任务状态：
1. 分析任务：轮询 `excel_get_status`
2. 拆分任务：轮询 `excel_get_status` 检查 `has_tasks`
3. 导出任务：轮询 `excel_export_tasks` 检查 `download_url`

## 错误处理

### 错误级别
1. **工具级错误**：返回错误响应
   ```json
   {
     "error": {
       "code": "INVALID_TOKEN",
       "message": "Token validation failed"
     }
   }
   ```

2. **任务级错误**：更新会话状态为 FAILED
   ```python
   session.status = SessionStatus.FAILED
   session.error = {
       'code': 'ANALYSIS_FAILED',
       'message': str(e)
   }
   ```

3. **系统级错误**：记录日志并返回 500 错误
   ```python
   logger.error(f"Error: {e}", exc_info=True)
   return web.json_response({'error': str(e)}, status=500)
   ```

### 错误恢复
- 任务失败不影响其他任务
- 会话失败可以重新创建
- 队列处理失败会记录并继续

## 性能优化

### 内存管理
- 会话数据使用内存存储
- 定期清理过期会话
- 大文件使用流式处理

### 并发处理
- 异步任务队列
- 多任务并行处理
- IO 密集操作使用 `asyncio.to_thread`

### 批次优化
- 默认批次大小：50,000 字符
- 按语言分组批次
- 按任务类型独立分批

## 配置管理

### 颜色配置 (`config/color_config.yaml`)
```yaml
yellow_colors:
  patterns:
    - "FFFF*"
    - "FF*00"
  hex_values:
    - "FFFF00"
    - "FFFFFF00"
  rgb_ranges:
    - red: [200, 255]
      green: [200, 255]
      blue: [0, 100]

blue_colors:
  hex_values:
    - "00B0F0"
    - "0070C0"
```

### 环境配置
- HTTP 端口：8021（默认）
- 会话过期：8小时
- 批次大小：50,000 字符
- 导出目录：`./exports/`

## 安全考虑

### 认证机制
- JWT Token 验证
- 与 backend_service 集成验证
- 权限检查（excel:analyze, task:split 等）

### 输入验证
- 文件格式验证
- 参数类型检查
- 大小限制

### 访问控制
- Session 隔离
- Token 权限控制
- CORS 配置

## 扩展性

### 新增语言支持
1. 更新 `language_mapper.py` 的 `LANGUAGE_MAPPINGS`
2. 添加新的语言代码映射
3. 更新前端语言选择列表

### 新增任务类型
1. 更新 `TaskType` 枚举
2. 修改颜色检测逻辑
3. 更新任务类型判定规则

### 新增导出格式
1. 在 `TaskExporter` 添加新方法
2. 更新 `export()` 方法路由
3. 添加前端格式选项

## 测试策略

### 单元测试
- 服务层方法测试
- 工具函数测试
- 模型验证测试

### 集成测试
- 完整流程测试
- 异步任务测试
- 错误处理测试

### 性能测试
- 大文件处理
- 并发请求
- 内存使用

## 部署建议

### 生产环境
1. 使用环境变量配置敏感信息
2. 启用日志记录
3. 配置监控和告警
4. 使用负载均衡
5. 配置持久化存储（可选）

### 开发环境
1. 使用 `--http` 模式方便调试
2. 启用详细日志
3. 使用测试 token
4. 配置 CORS 允许本地访问

---

**版本**: v2.0.0
**更新日期**: 2025-10-03
**作者**: Excel MCP Team