# MCP 微服务架构设计方案

## 🎯 架构目标

将三个核心服务改造为**独立的 MCP 服务器**，实现：

1. ✅ **进程级别隔离** - 每个服务独立进程运行
2. ✅ **标准化通信** - 使用 MCP stdio 协议
3. ✅ **完全解耦** - 服务间无代码依赖
4. ✅ **独立部署** - 可以单独升级/扩展
5. ✅ **语言无关** - 支持不同语言实现

---

## 🏗️ 新架构设计

```
┌─────────────────────────────────────────────────────────┐
│                 FastAPI Backend (主服务)                 │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │           MCP Client Manager                      │  │
│  │  - 管理3个MCP服务器连接                           │  │
│  │  - 处理stdio通信                                  │  │
│  │  - 请求路由与聚合                                 │  │
│  └──────────────────────────────────────────────────┘  │
│                        │                                │
│         ┌──────────────┼──────────────┐                │
│         │              │              │                 │
└─────────┼──────────────┼──────────────┼─────────────────┘
          │ stdio        │ stdio        │ stdio
          ▼              ▼              ▼
┌─────────────────┐ ┌─────────────┐ ┌──────────────────┐
│  MCP Server 1   │ │MCP Server 2 │ │  MCP Server 3    │
│                 │ │             │ │                  │
│  Excel分析服务  │ │任务拆分服务 │ │  LLM执行引擎     │
│                 │ │             │ │                  │
│  - 加载Excel    │ │- 生成任务   │ │  - Worker Pool   │
│  - 语言检测     │ │- 批次分配   │ │  - LLM调用       │
│  - 颜色提取     │ │- 上下文提取 │ │  - 进度追踪      │
│                 │ │             │ │                  │
│  独立进程       │ │独立进程     │ │  独立进程        │
└─────────────────┘ └─────────────┘ └──────────────────┘
```

---

## 📦 三个 MCP 服务器设计

### MCP Server 1: Excel分析服务

**服务名称**: `excel-analyzer-mcp`

**职责**:
- 加载 Excel 文件
- 提取元数据（颜色、注释、合并单元格）
- 语言检测
- 统计分析

**MCP Tools**:
```json
{
  "tools": [
    {
      "name": "load_excel",
      "description": "Load Excel file and extract metadata",
      "inputSchema": {
        "type": "object",
        "properties": {
          "file_path": {"type": "string"},
          "extract_colors": {"type": "boolean", "default": true},
          "extract_comments": {"type": "boolean", "default": true}
        },
        "required": ["file_path"]
      }
    },
    {
      "name": "analyze_excel",
      "description": "Analyze Excel structure and detect languages",
      "inputSchema": {
        "type": "object",
        "properties": {
          "excel_id": {"type": "string"}
        },
        "required": ["excel_id"]
      }
    },
    {
      "name": "get_sheet_data",
      "description": "Get DataFrame for specific sheet",
      "inputSchema": {
        "type": "object",
        "properties": {
          "excel_id": {"type": "string"},
          "sheet_name": {"type": "string"}
        },
        "required": ["excel_id", "sheet_name"]
      }
    }
  ]
}
```

**内部状态**:
- Excel DataFrame 缓存 (内存)
- 颜色映射
- 注释映射

**启动命令**:
```bash
python mcp_servers/excel_analyzer/server.py
```

---

### MCP Server 2: 任务拆分服务

**服务名称**: `task-splitter-mcp`

**职责**:
- 将 Excel 数据拆分为翻译任务
- 批次分配（基于字符数）
- 上下文提取
- 优先级计算

**MCP Tools**:
```json
{
  "tools": [
    {
      "name": "split_tasks",
      "description": "Split Excel data into translation tasks",
      "inputSchema": {
        "type": "object",
        "properties": {
          "excel_data": {"type": "object"},
          "source_lang": {"type": "string"},
          "target_langs": {"type": "array", "items": {"type": "string"}},
          "max_chars_per_batch": {"type": "integer", "default": 50000},
          "extract_context": {"type": "boolean", "default": true}
        },
        "required": ["excel_data", "source_lang", "target_langs"]
      }
    },
    {
      "name": "allocate_batches",
      "description": "Allocate tasks into batches",
      "inputSchema": {
        "type": "object",
        "properties": {
          "tasks": {"type": "array"},
          "max_chars_per_batch": {"type": "integer", "default": 50000}
        },
        "required": ["tasks"]
      }
    },
    {
      "name": "get_batch_statistics",
      "description": "Get batch allocation statistics",
      "inputSchema": {
        "type": "object",
        "properties": {
          "tasks": {"type": "array"}
        },
        "required": ["tasks"]
      }
    }
  ]
}
```

**内部状态**:
- 任务 DataFrame 缓存
- 批次映射

**启动命令**:
```bash
python mcp_servers/task_splitter/server.py
```

---

### MCP Server 3: LLM执行引擎

**服务名称**: `llm-executor-mcp`

**职责**:
- 并发执行翻译任务
- LLM Provider 管理
- Worker Pool 调度
- 实时进度追踪

**MCP Tools**:
```json
{
  "tools": [
    {
      "name": "start_execution",
      "description": "Start translation execution",
      "inputSchema": {
        "type": "object",
        "properties": {
          "session_id": {"type": "string"},
          "tasks": {"type": "array"},
          "llm_provider": {"type": "string", "enum": ["openai", "qwen"]},
          "llm_config": {"type": "object"},
          "max_workers": {"type": "integer", "default": 10}
        },
        "required": ["session_id", "tasks", "llm_provider"]
      }
    },
    {
      "name": "get_execution_status",
      "description": "Get current execution status",
      "inputSchema": {
        "type": "object",
        "properties": {
          "session_id": {"type": "string"}
        },
        "required": ["session_id"]
      }
    },
    {
      "name": "pause_execution",
      "description": "Pause ongoing execution",
      "inputSchema": {
        "type": "object",
        "properties": {
          "session_id": {"type": "string"}
        },
        "required": ["session_id"]
      }
    },
    {
      "name": "resume_execution",
      "description": "Resume paused execution",
      "inputSchema": {
        "type": "object",
        "properties": {
          "session_id": {"type": "string"}
        },
        "required": ["session_id"]
      }
    },
    {
      "name": "stop_execution",
      "description": "Stop and cleanup execution",
      "inputSchema": {
        "type": "object",
        "properties": {
          "session_id": {"type": "string"}
        },
        "required": ["session_id"]
      }
    }
  ],
  "resources": [
    {
      "uri": "progress://{session_id}",
      "name": "Execution Progress",
      "description": "Real-time progress updates",
      "mimeType": "application/json"
    }
  ]
}
```

**内部状态**:
- Worker Pool (每个 session 独立)
- 任务执行状态
- 进度追踪器

**启动命令**:
```bash
python mcp_servers/llm_executor/server.py
```

---

## 🔌 MCP 通信协议

### 请求流程示例

#### 1. Excel 分析
```json
// 主服务 → Excel Analyzer MCP
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "load_excel",
    "arguments": {
      "file_path": "/path/to/file.xlsx",
      "extract_colors": true
    }
  },
  "id": 1
}

// Excel Analyzer MCP → 主服务
{
  "jsonrpc": "2.0",
  "result": {
    "excel_id": "abc-123",
    "sheets": ["Sheet1", "Sheet2"],
    "total_rows": 1000,
    "metadata": {...}
  },
  "id": 1
}
```

#### 2. 任务拆分
```json
// 主服务 → Task Splitter MCP
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "split_tasks",
    "arguments": {
      "excel_data": {...},
      "source_lang": "CH",
      "target_langs": ["PT", "TH"],
      "max_chars_per_batch": 50000
    }
  },
  "id": 2
}

// Task Splitter MCP → 主服务
{
  "jsonrpc": "2.0",
  "result": {
    "tasks": [...],  // 1000个任务
    "batch_count": 20,
    "statistics": {...}
  },
  "id": 2
}
```

#### 3. 执行翻译
```json
// 主服务 → LLM Executor MCP
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "start_execution",
    "arguments": {
      "session_id": "session-123",
      "tasks": [...],
      "llm_provider": "openai",
      "max_workers": 10
    }
  },
  "id": 3
}

// LLM Executor MCP → 主服务
{
  "jsonrpc": "2.0",
  "result": {
    "status": "started",
    "session_id": "session-123",
    "worker_count": 10
  },
  "id": 3
}
```

#### 4. 进度订阅 (SSE 方式)
```json
// 主服务 → LLM Executor MCP
{
  "jsonrpc": "2.0",
  "method": "resources/read",
  "params": {
    "uri": "progress://session-123"
  },
  "id": 4
}

// LLM Executor MCP → 主服务 (持续推送)
{
  "jsonrpc": "2.0",
  "method": "notifications/resources/updated",
  "params": {
    "uri": "progress://session-123",
    "content": {
      "completed": 500,
      "total": 1000,
      "progress": 50.0
    }
  }
}
```

---

## 📂 目录结构设计

```
translation_system/
├── backend_v2/              # FastAPI 主服务
│   ├── api/                 # REST API 层
│   ├── mcp_clients/         # MCP 客户端管理
│   │   ├── excel_analyzer_client.py
│   │   ├── task_splitter_client.py
│   │   └── llm_executor_client.py
│   └── main.py
│
├── mcp_servers/             # MCP 服务器集合
│   ├── excel_analyzer/      # MCP Server 1
│   │   ├── server.py        # MCP 服务器入口
│   │   ├── tools.py         # Tool 实现
│   │   ├── services/        # 业务逻辑
│   │   │   ├── excel_loader.py
│   │   │   └── excel_analyzer.py
│   │   └── models/
│   │       └── excel_dataframe.py
│   │
│   ├── task_splitter/       # MCP Server 2
│   │   ├── server.py
│   │   ├── tools.py
│   │   ├── services/
│   │   │   ├── task_splitter.py
│   │   │   ├── batch_allocator.py
│   │   │   └── context_extractor.py
│   │   └── models/
│   │       └── task_dataframe.py
│   │
│   └── llm_executor/        # MCP Server 3
│       ├── server.py
│       ├── tools.py
│       ├── services/
│       │   ├── worker_pool.py
│       │   ├── batch_executor.py
│       │   └── progress_tracker.py
│       └── llm/
│           ├── llm_factory.py
│           ├── openai_provider.py
│           └── qwen_provider.py
│
└── shared/                  # 共享库
    ├── models/              # 共享数据模型
    └── utils/               # 共享工具
```

---

## 🚀 实施方案

### Phase 1: 基础设施搭建 (2天)

**任务**:
1. 创建 MCP 服务器基础框架
2. 实现 MCP stdio 通信层
3. 创建 MCP 客户端管理器

**产出**:
```python
# mcp_servers/base/mcp_server.py
class MCPServer:
    """Base MCP Server implementation"""
    
    async def handle_request(self, request: dict) -> dict:
        """Handle MCP JSON-RPC request"""
        ...

# backend_v2/mcp_clients/base_client.py
class MCPClient:
    """Base MCP Client with stdio communication"""
    
    async def call_tool(self, tool_name: str, args: dict) -> dict:
        """Call MCP server tool"""
        ...
```

### Phase 2: Excel分析服务 MCP 化 (2天)

**任务**:
1. 将 Excel 相关代码迁移到 `mcp_servers/excel_analyzer/`
2. 实现 MCP Tools: `load_excel`, `analyze_excel`, `get_sheet_data`
3. 主服务集成 Excel Analyzer Client

**验证**:
```bash
# 启动 MCP 服务器
python mcp_servers/excel_analyzer/server.py

# 主服务调用
curl -X POST http://localhost:8000/api/analyze/upload
```

### Phase 3: 任务拆分服务 MCP 化 (2天)

**任务**:
1. 将任务拆分代码迁移到 `mcp_servers/task_splitter/`
2. 实现 MCP Tools: `split_tasks`, `allocate_batches`
3. 主服务集成 Task Splitter Client

### Phase 4: LLM执行引擎 MCP 化 (3天)

**任务**:
1. 将 LLM 执行代码迁移到 `mcp_servers/llm_executor/`
2. 实现 MCP Tools: `start_execution`, `get_status`, `pause/resume/stop`
3. 实现进度订阅（MCP Resources）
4. 主服务集成 LLM Executor Client

### Phase 5: 集成测试与优化 (2天)

**任务**:
1. 端到端测试
2. 性能优化（进程通信开销）
3. 错误处理与重试机制
4. 文档完善

**总计**: 11天

---

## 📊 对比：MCP 微服务 vs 依赖注入

| 维度 | MCP 微服务 | 依赖注入解耦 |
|------|-----------|-------------|
| **隔离级别** | 进程级别 | 代码级别 |
| **独立部署** | ✅ 完全独立 | ❌ 需要一起部署 |
| **语言支持** | ✅ 可用不同语言 | ❌ 需要同一语言 |
| **通信方式** | MCP stdio | 函数调用 |
| **性能开销** | 中等（进程通信） | 低（内存调用） |
| **扩展性** | ✅ 可独立扩展 | ⚠️ 整体扩展 |
| **复杂度** | 高 | 低 |
| **工作量** | 11天 | 5.5天 |
| **适用场景** | 生产环境、多团队 | 开发环境、单团队 |

---

## ✅ MCP 方案的优势

1. **完全独立** - 每个服务可以独立开发、测试、部署
2. **技术栈灵活** - Excel分析用Python，LLM执行可以用Go/Rust
3. **水平扩展** - 可以启动多个 LLM Executor 实例
4. **故障隔离** - 一个服务崩溃不影响其他服务
5. **版本管理** - 服务可以独立升级
6. **标准化** - 使用 MCP 协议，与 Claude Desktop 等工具兼容

---

## ⚠️ 需要注意的挑战

1. **进程通信开销** - stdio 传输大数据（Excel DataFrame）可能较慢
2. **状态管理** - 跨进程的会话状态需要额外管理
3. **调试复杂度** - 多进程调试比单进程困难
4. **部署复杂度** - 需要管理多个进程的启动/监控

---

## 🎯 建议

**推荐方案**: MCP 微服务架构

**理由**:
1. 符合你的长期目标（微服务化）
2. 可以逐步迁移（一个服务一个服务改造）
3. 为未来的分布式部署打下基础
4. 利用 MCP 生态（与 Claude Desktop 等集成）

**执行策略**:
- 先做 Phase 1（基础设施）
- 然后 Phase 2（Excel分析，最独立）
- 验证可行性后，继续 Phase 3、4

准备好开始了吗？我可以：
1. 🚀 先实现 Phase 1 的 MCP 基础框架
2. 📖 详细展示每个 MCP Server 的代码结构
3. 🤔 讨论具体的技术细节

你想从哪里开始？
