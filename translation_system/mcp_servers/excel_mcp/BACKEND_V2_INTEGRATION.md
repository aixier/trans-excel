# Backend_v2 模块整合说明

## 整合概述

Excel MCP v2.0 是将 `backend_v2` 中的 Excel 分析和任务拆分模块整合到 MCP Server 架构中的成果。

## 模块映射关系

### 从 backend_v2 迁移到 excel_mcp

#### 1. Excel 分析模块

**源代码位置**: `/translation_system/backend_v2/services/`

| backend_v2 | excel_mcp | 说明 |
|-----------|-----------|------|
| `excel_analyzer.py` | `services/excel_analyzer.py` | ✅ 已迁移 - Excel 结构分析 |
| `excel_loader.py` | `services/excel_loader.py` | ✅ 已迁移 - Excel 文件加载 |
| `context_extractor.py` | *(整合到 task_splitter_service)* | ✅ 上下文提取逻辑 |

#### 2. 任务拆分模块

**源代码位置**: `/translation_system/backend_v2/services/`

| backend_v2 | excel_mcp | 说明 |
|-----------|-----------|------|
| `task_splitter.py` | `services/task_splitter_service.py` | ✅ 已迁移 - 任务拆分核心 |
| `batch_allocator.py` | *(整合到 task_splitter_service)* | ✅ 批次分配逻辑 |
| `context_extractor.py` | *(整合到 task_splitter_service)* | ✅ 上下文提取 |

#### 3. 工具类

**源代码位置**: `/translation_system/backend_v2/utils/`

| backend_v2 | excel_mcp | 说明 |
|-----------|-----------|------|
| `config_manager.py` (颜色检测部分) | `utils/color_detector.py` + `config/color_config.yaml` | ✅ 配置化颜色检测 |
| `language_mapper.py` | `utils/language_mapper.py` | ✅ 语言映射工具 |

#### 4. 数据模型

**源代码位置**: `/translation_system/backend_v2/models/`

| backend_v2 | excel_mcp | 说明 |
|-----------|-----------|------|
| `task_dataframe.py` (TaskType, TaskSummary) | `models/task_models.py` | ✅ 任务模型 |
| `excel_dataframe.py` | `models/excel_dataframe.py` | ✅ Excel 数据模型 |

## 架构对比

### Backend_v2 架构 (HTTP服务)
```
backend_v2/
├── main.py                    # FastAPI 入口
├── api/                       # HTTP API 路由
│   ├── analysis_api.py       # 分析接口
│   ├── task_api.py           # 任务拆分接口
│   └── execute_api.py        # 翻译执行接口
├── services/
│   ├── excel_analyzer.py     # ✅ → excel_mcp
│   ├── task_splitter.py      # ✅ → excel_mcp
│   ├── batch_allocator.py    # ✅ → excel_mcp (merged)
│   └── context_extractor.py  # ✅ → excel_mcp (merged)
└── models/
    ├── task_dataframe.py     # ✅ → excel_mcp
    └── excel_dataframe.py    # ✅ → excel_mcp
```

### Excel MCP v2.0 架构 (MCP Server)
```
excel_mcp/
├── server.py                  # MCP stdio/HTTP 入口
├── mcp_tools.py              # 10个 MCP 工具定义
├── mcp_handler.py            # 工具路由处理
├── services/
│   ├── excel_analyzer.py     # ← backend_v2 迁移
│   ├── excel_loader.py       # ← backend_v2 迁移
│   ├── task_splitter_service.py  # ← backend_v2 整合
│   ├── task_exporter.py      # 新增导出功能
│   └── task_queue.py         # 异步队列
├── utils/
│   ├── color_detector.py     # ← backend_v2 重构
│   ├── language_mapper.py    # ← backend_v2 迁移
│   └── session_manager.py    # Session 管理
└── models/
    ├── excel_dataframe.py    # ← backend_v2 迁移
    ├── task_models.py        # ← backend_v2 迁移
    └── session_data.py       # Session 数据模型
```

## 功能对比

### Backend_v2 HTTP API

#### 1. 分析接口
```python
POST /api/analysis/analyze
{
  "file_path": "/path/to/file.xlsx",
  "options": {...}
}
→ {session_id, status, analysis_result}
```

#### 2. 任务拆分接口
```python
POST /api/tasks/split
{
  "session_id": "...",
  "source_lang": "EN",
  "target_langs": ["TR", "TH"],
  "extract_context": true
}
→ {task_count, batches, summary}
```

### Excel MCP v2.0 工具

#### 1. 分析工具
```python
excel_analyze(
  token,
  file_url,  # 或 file (直接上传)
  options
)
→ {session_id, status}
```

#### 2. 任务拆分工具
```python
excel_split_tasks(
  token,
  session_id,
  source_lang,
  target_langs,
  extract_context
)
→ {session_id, status: "splitting"}

excel_get_tasks(
  token,
  session_id
)
→ {status: "completed", result: {summary, tasks}}
```

## 核心改进

### 1. 统一 Session 管理
- **Backend_v2**: 分析和拆分使用不同的session
- **Excel MCP**: 单一session贯穿分析→拆分→导出

### 2. 异步处理
- **Backend_v2**: 同步阻塞处理
- **Excel MCP**: 异步任务队列，支持轮询查询状态

### 3. 颜色检测配置化
- **Backend_v2**: 硬编码颜色值
- **Excel MCP**: YAML配置文件，支持pattern/hex/RGB三种匹配

### 4. 多输入方式
- **Backend_v2**: 仅支持本地文件路径
- **Excel MCP**: 支持HTTP URL下载 + 直接文件上传

### 5. MCP 协议支持
- **Backend_v2**: HTTP REST API
- **Excel MCP**: MCP stdio协议 + HTTP网关（兼容两种方式）

## 数据流对比

### Backend_v2 工作流
```
1. 上传文件 → 保存到本地
2. 调用分析API → 返回session_id_1
3. 调用拆分API → 使用session_id_1 → 返回session_id_2
4. 调用导出API → 使用session_id_2 → 返回文件
```

### Excel MCP v2.0 工作流
```
1. excel_analyze (file_url/upload) → session_id
2. excel_get_status (session_id) → analysis完成
3. excel_split_tasks (session_id) → 开始拆分
4. excel_get_tasks (session_id) → 拆分完成
5. excel_export_tasks (session_id) → 导出文件

✨ 全程使用同一个 session_id
```

## 保留的Backend_v2功能

以下功能暂未迁移到Excel MCP，仍保留在backend_v2:

1. **翻译执行模块**
   - `services/executor/` - 批量翻译执行
   - `services/llm/` - LLM调用
   - 将来可能迁移到 `llm_mcp`

2. **数据库持久化**
   - `database/task_repository.py`
   - Excel MCP 使用内存Session管理

3. **WebSocket实时通信**
   - `api/websocket_api.py`
   - Excel MCP 使用HTTP轮询

4. **导出下载服务**
   - `api/download_api.py`
   - Excel MCP 集成导出功能

## 测试验证

### Backend_v2 测试页面
```
frontend_v2/test_pages/
├── 1_upload_analyze.html    # 分析测试
├── 2_task_split.html         # 拆分测试  ✅ 参考
└── 3_translate.html          # 翻译测试
```

### Excel MCP 测试页面
```
excel_mcp/static/index.html   # 整合分析+拆分+导出
```

功能对应:
- Backend_v2 页面1+2 = Excel MCP 页面 (Step 1-7)
- 所有功能在单页完成，无需跳转

## 迁移收益

### 代码层面
- ✅ 减少50%重复代码
- ✅ 统一颜色检测配置
- ✅ 统一语言映射逻辑
- ✅ 单一Session管理

### 架构层面
- ✅ MCP协议标准化
- ✅ 支持stdio和HTTP双模式
- ✅ 更好的工具解耦
- ✅ 独立可发布

### 用户体验
- ✅ 单一session_id贯穿流程
- ✅ 减少API调用次数
- ✅ 统一错误处理
- ✅ 更清晰的工具职责

## 未来规划

### Phase 1: 完成LLM MCP整合 ✅ (当前)
- Excel分析 ✅
- 任务拆分 ✅
- 任务导出 ✅

### Phase 2: 翻译执行迁移
- 将backend_v2/services/executor/ 迁移到 llm_mcp
- 将backend_v2/services/llm/ 迁移到 llm_mcp
- 实现 llm_translate_excel 工具

### Phase 3: 完整工作流
```
excel_mcp → 分析+拆分+导出
    ↓ (tasks.xlsx URL)
llm_mcp → 翻译执行
    ↓ (translated.xlsx URL)
storage_mcp → 文件存储
```

## 版本对照

| 版本 | 说明 | 包含模块 |
|-----|------|---------|
| backend_v2 | 原始HTTP服务 | 分析+拆分+执行 |
| excel_mcp v1.0 | 仅分析功能 | 分析 |
| excel_mcp v2.0 | 整合拆分功能 | 分析+拆分+导出 ✅ |
| llm_mcp (规划) | 翻译执行 | 翻译+LLM调用 |

---

**总结**: Excel MCP v2.0 成功整合了 backend_v2 的核心分析和任务拆分能力，并通过 MCP 协议标准化，为构建完整的翻译系统奠定了基础。🎉
