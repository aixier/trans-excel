# API 快速参考手册

**基础URL**: `http://localhost:8013`

---

## 快速开始

### 典型翻译工作流

```bash
# 1. 上传文件并拆分任务
curl -X POST http://localhost:8013/api/tasks/split \
  -F "file=@game.xlsx" \
  -F "source_lang=CH" \
  -F "target_langs=EN,TH" \
  -F "rule_set=translation"
# → 返回 session_id

# 2. 开始翻译
curl -X POST http://localhost:8013/api/execute/start \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "xxx",
    "processor": "llm_qwen",
    "glossary_config": {"enabled": true, "id": "default"}
  }'

# 3. 查询状态
curl http://localhost:8013/api/execute/status/{session_id}

# 4. 下载结果
curl http://localhost:8013/api/download/{session_id} -o translated.xlsx
```

---

## 核心API端点

### 1. 任务拆分 API

#### POST `/api/tasks/split`

上传Excel文件并拆分任务

**请求 (multipart/form-data)**:
```
file: Excel文件
source_lang: 源语言 (CH/EN/TH等)
target_langs: 目标语言列表，逗号分隔 (EN,TH,PT)
rule_set: 规则集 (translation | caps_only)
parent_session_id: 父Session ID (可选，用于链式调用)
extract_context: 是否提取上下文 (true/false，默认true)
max_chars_per_batch: 每批最大字符数 (默认1000)
```

**响应**:
```json
{
  "status": "success",
  "session_id": "uuid",
  "stage": "split_complete",
  "total_tasks": 100,
  "statistics": {
    "by_type": {"normal": 80, "yellow": 15, "blue": 5},
    "by_sheet": {"Sheet1": 100},
    "by_target_lang": {"EN": 50, "TH": 50}
  }
}
```

#### GET `/api/tasks/split/status/{session_id}`

获取拆分状态

**响应**:
```json
{
  "session_id": "uuid",
  "status": "split_complete",
  "progress": 100,
  "total_tasks": 100,
  "statistics": {...}
}
```

#### GET `/api/tasks/export/{session_id}?export_type=tasks`

导出任务表或DataFrame

**参数**:
- `export_type`:
  - `tasks`: 导出任务分解表 (TaskDataFrame)
  - `dataframe`: 导出完整数据框架 (包含color_*和comment_*列)

**响应**: Excel文件下载

---

### 2. 执行控制 API

#### POST `/api/execute/start`

开始执行任务

**请求**:
```json
{
  "session_id": "uuid",
  "processor": "llm_qwen",              // 或 "uppercase"
  "max_workers": 10,                    // 并发数（可选）
  "glossary_config": {                  // 术语表配置（可选）
    "enabled": true,
    "id": "default"
  }
}
```

**响应**:
```json
{
  "status": "started",
  "total_batches": 10,
  "total_tasks": 100,
  "workers": 10
}
```

#### GET `/api/execute/status/{session_id}`

获取执行状态

**响应**:
```json
{
  "status": "executing",              // idle | running | completed | failed
  "session_id": "uuid",
  "progress": {
    "total": 100,
    "completed": 60,
    "failed": 2,
    "pending": 38
  },
  "batches": {
    "total": 10,
    "completed": 6,
    "failed": 0
  },
  "completion_rate": 60.0,
  "estimated_remaining_seconds": 120,
  "active_workers": 10,
  "start_time": "2025-10-17T00:00:00",
  "end_time": null
}
```

#### POST `/api/execute/stop/{session_id}`

停止执行

**响应**:
```json
{
  "status": "stopped",
  "completed_batches": 6,
  "completed_tasks": 60
}
```

#### POST `/api/execute/pause/{session_id}`

暂停执行

#### POST `/api/execute/resume/{session_id}`

恢复执行

---

### 3. 下载导出 API

#### GET `/api/download/{session_id}`

下载翻译结果（最终Excel文件）

**前置条件**:
- `session.stage == "completed"`
- `output_state != null`

**响应**: Excel文件下载

**错误**:
```json
{
  "detail": "Cannot download: execution not completed (current stage: executing)"
}
```

#### GET `/api/download/{session_id}/info`

获取下载信息（检查是否可下载）

**响应**:
```json
{
  "session_id": "uuid",
  "status": "completed",                    // 或 "executing" / "not_started"
  "message": "翻译已完成，可以下载结果",
  "ready_for_download": true,
  "can_download": true,
  "execution_status": {
    "stage": "completed",
    "ready_for_download": true,
    "has_output": true
  },
  "task_statistics": {
    "total": 100,
    "completed": 100,
    "failed": 0,
    "processing": 0,
    "pending": 0
  },
  "export_info": {
    "has_export": true,
    "exported_file": "/path/to/file.xlsx",
    "export_timestamp": "2025-10-17T01:00:00",
    "file_exists": true,
    "file_size": 102400
  }
}
```

#### DELETE `/api/download/{session_id}/files`

清理导出缓存文件

**响应**:
```json
{
  "session_id": "uuid",
  "files_removed": 1,
  "errors": [],
  "success": true
}
```

---

### 4. Session 管理 API

#### GET `/api/sessions/list`

列出所有Session

**响应**:
```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "stage": "completed",
      "created_at": "2025-10-17T00:00:00",
      "input_source": "file",
      "parent_session_id": null,
      "rules": ["empty", "yellow", "blue"],
      "processor": "llm_qwen",
      "task_count": 100,
      "has_output": true,
      "child_sessions": 1
    }
  ],
  "total": 10
}
```

#### GET `/api/sessions/detail/{session_id}`

获取Session详情

**响应**:
```json
{
  "session_id": "uuid",
  "created_at": "2025-10-17T00:00:00",
  "last_accessed": "2025-10-17T01:00:00",
  "stage": "completed",
  "input_source": "file",
  "parent_session_id": null,
  "rules": ["empty", "yellow", "blue"],
  "processor": "llm_qwen",
  "task_statistics": {
    "total": 100,
    "by_type": {"normal": 80, "yellow": 15, "blue": 5}
  },
  "execution_statistics": {
    "total_time": 120,
    "avg_time_per_task": 1.2
  },
  "metadata": {
    "input_file_path": "/path/to/input.pkl",
    "task_file_path": "/path/to/tasks.parquet",
    "output_file_path": "/path/to/output.pkl",
    "output_state_timestamp": "2025-10-17T01:00:00"
  },
  "child_session_ids": ["uuid2"]
}
```

#### DELETE `/api/sessions/{session_id}`

删除Session

**响应**:
```json
{
  "status": "success",
  "message": "Session deleted successfully"
}
```

---

### 5. 术语表 API

#### GET `/api/glossaries/list`

列出所有术语表

**响应**:
```json
{
  "glossaries": [
    {
      "id": "default",
      "name": "通用游戏术语",
      "description": "包含常见RPG游戏术语",
      "version": "1.0",
      "term_count": 20,
      "languages": ["EN", "TH", "PT", "VN"]
    }
  ],
  "count": 1
}
```

#### GET `/api/glossaries/{glossary_id}`

获取术语表详情

**响应**:
```json
{
  "id": "default",
  "name": "通用游戏术语",
  "description": "包含常见RPG游戏术语",
  "version": "1.0",
  "languages": ["EN", "TH"],
  "terms": [
    {
      "id": "term_001",
      "source": "攻击力",
      "category": "属性",
      "priority": 10,
      "translations": {
        "EN": "ATK",
        "TH": "พลังโจมตี"
      }
    }
  ]
}
```

#### POST `/api/glossaries/upload`

上传术语表

**请求 (multipart/form-data)**:
```
file: JSON文件
glossary_id: 术语表ID（可选）
```

**支持的JSON格式**:

1. **标准格式**:
```json
{
  "id": "my_glossary",
  "name": "我的术语表",
  "description": "描述",
  "version": "1.0",
  "languages": ["EN"],
  "terms": [
    {
      "id": "term_001",
      "source": "攻击力",
      "category": "属性",
      "priority": 10,
      "translations": {"EN": "ATK"}
    }
  ]
}
```

2. **简化格式** (自动转换):
```json
{
  "攻击力": "ATK",
  "生命值": "HP"
}
```

**响应**:
```json
{
  "status": "success",
  "glossary_id": "my_glossary",
  "term_count": 2,
  "message": "Glossary uploaded successfully"
}
```

#### DELETE `/api/glossaries/{glossary_id}`

删除术语表

**响应**:
```json
{
  "status": "success",
  "glossary_id": "my_glossary",
  "message": "Glossary deleted successfully"
}
```

---

### 6. 监控 API

#### GET `/api/monitor/status/{session_id}`

监控执行状态（更详细）

**响应**: 类似 `/api/execute/status`，但包含更多内部指标

#### GET `/api/monitor/summary/{session_id}`

执行摘要

**响应**:
```json
{
  "session_id": "uuid",
  "total_tasks": 100,
  "completed_tasks": 100,
  "failed_tasks": 0,
  "success_rate": 100.0,
  "total_time_seconds": 120,
  "avg_time_per_task": 1.2
}
```

---

## WebSocket API

### 连接

```javascript
const ws = new WebSocket('ws://localhost:8013/ws/{session_id}');
```

### 接收消息

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'progress':
      // 进度更新
      console.log(`${data.completed}/${data.total}`);
      break;

    case 'batch_complete':
      // 批次完成
      console.log(`Batch ${data.batch_id} completed`);
      break;

    case 'execution_complete':
      // 执行完成
      console.log('All tasks completed');
      break;

    case 'error':
      // 错误
      console.error(data.message);
      break;
  }
};
```

---

## 错误代码

| HTTP状态码 | 含义 | 示例 |
|-----------|-----|-----|
| 200 | 成功 | 正常响应 |
| 400 | 请求错误 | 参数缺失、状态不匹配 |
| 404 | 资源不存在 | Session不存在、术语表不存在 |
| 500 | 服务器错误 | 内部错误 |

**错误响应格式**:
```json
{
  "detail": "Error message here"
}
```

---

## 规则集配置

### translation (翻译规则集)

启用规则: `['empty', 'yellow', 'blue']`

**任务类型**:
- `normal`: 空单元格翻译
- `yellow`: 黄色单元格强制重译
- `blue`: 蓝色单元格自我缩短

### caps_only (大写转换规则集)

启用规则: `['caps']`

**任务类型**:
- `caps`: CAPS sheet的大写转换

---

## 处理器类型

| Processor | 功能 | 备注 |
|-----------|-----|-----|
| `llm_qwen` | 通义千问翻译 | 需要API密钥 |
| `llm_openai` | OpenAI翻译 | 需要API密钥 |
| `uppercase` | 大写转换 | 仅处理ASCII字符 |

---

## 典型使用场景

### 场景1: 简单翻译

```bash
# 1. 上传并拆分
curl -X POST http://localhost:8013/api/tasks/split \
  -F "file=@game.xlsx" \
  -F "source_lang=CH" \
  -F "target_langs=EN" \
  -F "rule_set=translation"

# 2. 开始翻译
curl -X POST http://localhost:8013/api/execute/start \
  -H "Content-Type: application/json" \
  -d '{"session_id": "xxx", "processor": "llm_qwen"}'

# 3. 下载
curl http://localhost:8013/api/download/xxx -o result.xlsx
```

### 场景2: 翻译 + 大写转换（链式）

```bash
# Stage 1: 翻译
curl -X POST http://localhost:8013/api/tasks/split \
  -F "file=@game.xlsx" \
  -F "rule_set=translation" \
  -F "target_langs=EN,TH"
# → session_A

curl -X POST http://localhost:8013/api/execute/start \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session_A", "processor": "llm_qwen"}'
# 等待完成

# Stage 2: 大写转换
curl -X POST http://localhost:8013/api/tasks/split \
  -F "parent_session_id=session_A" \
  -F "rule_set=caps_only"
# → session_B

curl -X POST http://localhost:8013/api/execute/start \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session_B", "processor": "uppercase"}'

# 下载最终结果
curl http://localhost:8013/api/download/session_B -o final.xlsx
```

### 场景3: 使用术语表

```bash
# 1. 上传术语表
curl -X POST http://localhost:8013/api/glossaries/upload \
  -F "file=@terms.json" \
  -F "glossary_id=my_terms"

# 2. 翻译时启用术语表
curl -X POST http://localhost:8013/api/execute/start \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "xxx",
    "processor": "llm_qwen",
    "glossary_config": {
      "enabled": true,
      "id": "my_terms"
    }
  }'
```

---

## 前端开发建议

### 推荐的状态轮询间隔

- 拆分状态: 1秒
- 执行状态: 2秒
- 下载信息: 3秒

### WebSocket vs 轮询

**推荐使用WebSocket**，优势：
- 实时推送，无延迟
- 减少服务器负载
- 更好的用户体验

**轮询适用于**：
- 不需要实时更新的场景
- WebSocket不可用的环境

### 缓存策略

- Session列表: 缓存30秒
- 术语表列表: 缓存5分钟
- 执行状态: 不缓存（实时查询）

---

## 附录：常用命令

```bash
# 查看所有Session
curl http://localhost:8013/api/sessions/list

# 清理旧Session
curl -X DELETE http://localhost:8013/api/sessions/{old_session_id}

# 查看术语表
curl http://localhost:8013/api/glossaries/list

# 查看执行配置
curl http://localhost:8013/api/execute/config

# 健康检查
curl http://localhost:8013/api/database/health
```
