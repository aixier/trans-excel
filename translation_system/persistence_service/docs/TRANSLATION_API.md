# Translation Persistence API - 翻译数据持久化 API 文档

**API 版本**: v1.0
**适用范围**: 翻译系统（Backend V2）
**存储后端**: MySQL
**Base URL**: `http://localhost:8001`

---

## 📋 目录

- [1. 概述](#1-概述)
- [2. 认证](#2-认证)
- [3. 批量写入 API](#3-批量写入-api)
- [4. 查询 API](#4-查询-api)
- [5. 恢复 API](#5-恢复-api)
- [6. 管理 API](#6-管理-api)
- [7. 系统 API](#7-系统-api)
- [8. 数据模型](#8-数据模型)
- [9. 错误码](#9-错误码)
- [10. 客户端示例](#10-客户端示例)

---

## 1. 概述

### 1.1 服务说明

Translation Persistence API 提供翻译系统的数据持久化能力，包括：
- **批量写入**：批量持久化会话和任务数据
- **数据查询**：查询历史会话和任务数据
- **数据恢复**：服务重启后恢复未完成的翻译会话
- **数据管理**：删除、清理、统计

### 1.2 核心特性

| 特性 | 说明 |
|------|------|
| **批量处理** | 一次请求最多 1000 条数据 |
| **异步非阻塞** | API 立即返回，数据异步写入 |
| **幂等性** | 重复调用不会产生重复数据 |
| **高性能** | 响应时间 < 10ms (写入), < 50ms (查询) |

### 1.3 API 端点列表

| 分类 | 端点 | 方法 | 功能 |
|------|------|------|------|
| **批量写入** | `/api/v1/translation/sessions/batch` | POST | 批量写入会话 |
| **批量写入** | `/api/v1/translation/tasks/batch` | POST | 批量写入任务 |
| **批量写入** | `/api/v1/translation/flush` | POST | 强制刷新缓冲区 |
| **查询** | `/api/v1/translation/sessions` | GET | 查询会话列表 |
| **查询** | `/api/v1/translation/sessions/{id}` | GET | 查询单个会话 |
| **查询** | `/api/v1/translation/sessions/{id}/tasks` | GET | 查询会话的任务 |
| **查询** | `/api/v1/translation/tasks/{id}` | GET | 查询单个任务 |
| **查询** | `/api/v1/translation/tasks` | GET | 查询任务列表 |
| **恢复** | `/api/v1/translation/recovery/incomplete-sessions` | GET | 获取未完成会话 |
| **恢复** | `/api/v1/translation/recovery/restore/{id}` | POST | 恢复会话数据 |
| **管理** | `/api/v1/translation/sessions/{id}` | DELETE | 删除会话 |
| **管理** | `/api/v1/translation/sessions/cleanup` | POST | 清理过期数据 |
| **管理** | `/api/v1/translation/stats` | GET | 获取统计信息 |
| **系统** | `/health` | GET | 健康检查 |
| **系统** | `/api/v1/system/metrics` | GET | 性能指标 |

---

## 2. 认证

### 2.1 当前版本（Phase 1）

当前版本**不需要认证**，仅供内网访问。

### 2.2 未来版本（Phase 2+）

将支持以下认证方式：
- API Key 认证
- JWT 令牌认证

---

## 3. 批量写入 API

### 3.1 批量写入会话

批量创建或更新翻译会话记录。

**端点**: `POST /api/v1/translation/sessions/batch`

**请求头**:
```http
Content-Type: application/json
```

**请求体**:
```json
{
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "game_translation.xlsx",
      "file_path": "/uploads/game_translation.xlsx",
      "status": "processing",
      "game_info": {
        "game_name": "Fantasy RPG",
        "source_language": "en",
        "target_language": "zh",
        "game_type": "RPG"
      },
      "llm_provider": "openai",
      "metadata": {
        "user_id": "user_123",
        "project_id": "proj_456"
      },
      "total_tasks": 1000,
      "completed_tasks": 0,
      "failed_tasks": 0,
      "processing_tasks": 0
    }
  ]
}
```

**请求字段说明**:

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| sessions | array | 是 | 会话对象数组 | - |
| session_id | string | 是 | 会话唯一标识（UUID） | "550e8400-..." |
| filename | string | 是 | 文件名 | "game.xlsx" |
| file_path | string | 是 | 文件路径 | "/uploads/game.xlsx" |
| status | string | 是 | 状态：pending/processing/completed/failed | "processing" |
| game_info | object | 否 | 游戏信息（JSON） | {...} |
| llm_provider | string | 是 | LLM 提供商：openai/qwen | "openai" |
| metadata | object | 否 | 元数据（JSON） | {...} |
| total_tasks | int | 否 | 总任务数 | 1000 |
| completed_tasks | int | 否 | 完成任务数 | 0 |
| failed_tasks | int | 否 | 失败任务数 | 0 |
| processing_tasks | int | 否 | 处理中任务数 | 0 |

**响应示例**:
```json
{
  "status": "accepted",
  "count": 1,
  "timestamp": "2025-09-30T10:15:30Z"
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 接受状态：accepted/rejected |
| count | int | 已接受的会话数量 |
| timestamp | string | 接受时间戳（ISO 8601） |

**调用示例**:
```bash
curl -X POST http://localhost:8001/api/v1/translation/sessions/batch \
  -H "Content-Type: application/json" \
  -d '{
    "sessions": [{
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "test.xlsx",
      "file_path": "/uploads/test.xlsx",
      "status": "processing",
      "llm_provider": "openai",
      "total_tasks": 100
    }]
  }'
```

**错误响应**:
```json
{
  "detail": "Invalid session data format",
  "errors": [
    {
      "field": "session_id",
      "message": "session_id is required"
    }
  ]
}
```

**业务规则**:
- 单次请求最多 1000 个会话
- 支持幂等操作（重复调用使用 session_id 去重）
- 立即返回（不等待数据库写入完成）
- 数据会在最多 30 秒后写入数据库

---

### 3.2 批量写入任务

批量创建或更新翻译任务记录。

**端点**: `POST /api/v1/translation/tasks/batch`

**请求头**:
```http
Content-Type: application/json
```

**请求体**:
```json
{
  "tasks": [
    {
      "task_id": "task_001",
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "batch_id": "batch_001",
      "sheet_name": "Dialogue",
      "row_index": 10,
      "column_name": "Text",
      "source_text": "Hello, adventurer!",
      "target_text": "你好，冒险者！",
      "context": "NPC greeting dialogue",
      "status": "completed",
      "confidence": 0.95,
      "error_message": null,
      "retry_count": 0,
      "start_time": "2025-09-30T10:10:00Z",
      "end_time": "2025-09-30T10:10:05Z",
      "duration_ms": 5000
    }
  ]
}
```

**请求字段说明**:

| 字段 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| tasks | array | 是 | 任务对象数组 | - |
| task_id | string | 是 | 任务唯一标识 | "task_001" |
| session_id | string | 是 | 所属会话 ID | "550e8400-..." |
| batch_id | string | 是 | 批次 ID | "batch_001" |
| sheet_name | string | 是 | 工作表名称 | "Dialogue" |
| row_index | int | 是 | 行索引（从 0 开始） | 10 |
| column_name | string | 是 | 列名 | "Text" |
| source_text | string | 是 | 源文本 | "Hello, adventurer!" |
| target_text | string | 否 | 翻译结果 | "你好，冒险者！" |
| context | string | 否 | 上下文信息 | "NPC greeting" |
| status | string | 是 | 状态：pending/processing/completed/failed | "completed" |
| confidence | float | 否 | 置信度（0-1） | 0.95 |
| error_message | string | 否 | 错误信息 | null |
| retry_count | int | 否 | 重试次数 | 0 |
| start_time | string | 否 | 开始时间（ISO 8601） | "2025-09-30T10:10:00Z" |
| end_time | string | 否 | 结束时间（ISO 8601） | "2025-09-30T10:10:05Z" |
| duration_ms | int | 否 | 执行耗时（毫秒） | 5000 |

**响应示例**:
```json
{
  "status": "accepted",
  "count": 1,
  "timestamp": "2025-09-30T10:15:30Z"
}
```

**调用示例**:
```bash
curl -X POST http://localhost:8001/api/v1/translation/tasks/batch \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [{
      "task_id": "task_001",
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "batch_id": "batch_001",
      "sheet_name": "Dialogue",
      "row_index": 10,
      "column_name": "Text",
      "source_text": "Hello",
      "status": "pending"
    }]
  }'
```

**业务规则**:
- 单次请求最多 1000 个任务
- 必须关联到已存在的会话（session_id）
- 支持幂等操作（重复调用使用 task_id 去重）
- 立即返回（不等待数据库写入完成）

---

### 3.3 强制刷新缓冲区

立即将缓冲区中的所有数据写入数据库。

**端点**: `POST /api/v1/translation/flush`

**使用场景**:
- 用户点击"停止"按钮时
- 用户点击"暂停"按钮时
- 系统关闭前
- 需要立即查询刚写入的数据时

**请求体**: 无

**响应示例**:
```json
{
  "status": "flushed",
  "sessions_written": 10,
  "tasks_written": 850,
  "duration_ms": 1200
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 刷新状态：flushed/error |
| sessions_written | int | 写入的会话数量 |
| tasks_written | int | 写入的任务数量 |
| duration_ms | int | 刷新耗时（毫秒） |

**调用示例**:
```bash
curl -X POST http://localhost:8001/api/v1/translation/flush
```

**业务规则**:
- 同步等待刷新完成（最多 10 秒）
- 失败时返回明确错误信息
- 建议在停止/暂停执行时调用

---

## 4. 查询 API

### 4.1 查询会话列表

查询翻译会话列表，支持分页、过滤、排序。

**端点**: `GET /api/v1/translation/sessions`

**查询参数**:

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| status | string | 否 | 过滤状态：pending/processing/completed/failed | processing |
| from_date | string | 否 | 起始日期（ISO 8601） | 2025-09-01T00:00:00Z |
| to_date | string | 否 | 结束日期（ISO 8601） | 2025-09-30T23:59:59Z |
| page | int | 否 | 页码（从 1 开始） | 1 |
| page_size | int | 否 | 每页大小（默认 20，最大 100） | 20 |
| sort_by | string | 否 | 排序字段：created_at/updated_at | created_at |
| order | string | 否 | 排序方向：asc/desc | desc |

**请求示例**:
```bash
GET /api/v1/translation/sessions?status=processing&page=1&page_size=20&sort_by=created_at&order=desc
```

**响应示例**:
```json
{
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "items": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "game.xlsx",
      "status": "processing",
      "total_tasks": 1000,
      "completed_tasks": 350,
      "failed_tasks": 5,
      "processing_tasks": 10,
      "pending_tasks": 635,
      "progress": 35.0,
      "created_at": "2025-09-30T10:00:00Z",
      "updated_at": "2025-09-30T10:05:00Z"
    }
  ]
}
```

**调用示例**:
```bash
curl "http://localhost:8001/api/v1/translation/sessions?status=processing&page=1&page_size=20"
```

---

### 4.2 查询单个会话

查询指定会话的详细信息。

**端点**: `GET /api/v1/translation/sessions/{session_id}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |

**响应示例**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "game.xlsx",
  "file_path": "/uploads/game.xlsx",
  "status": "processing",
  "game_info": {
    "game_name": "Fantasy RPG",
    "source_language": "en",
    "target_language": "zh"
  },
  "llm_provider": "openai",
  "metadata": {
    "user_id": "user_123"
  },
  "total_tasks": 1000,
  "completed_tasks": 350,
  "failed_tasks": 5,
  "processing_tasks": 10,
  "pending_tasks": 635,
  "progress": 35.0,
  "created_at": "2025-09-30T10:00:00Z",
  "updated_at": "2025-09-30T10:05:00Z",
  "estimated_completion": "2025-09-30T10:20:00Z"
}
```

**调用示例**:
```bash
curl http://localhost:8001/api/v1/translation/sessions/550e8400-e29b-41d4-a716-446655440000
```

**错误响应（会话不存在）**:
```json
{
  "detail": "Session not found",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 4.3 查询会话的任务列表

查询指定会话的所有任务，支持分页和过滤。

**端点**: `GET /api/v1/translation/sessions/{session_id}/tasks`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 过滤状态：pending/processing/completed/failed |
| sheet_name | string | 否 | 过滤工作表名称 |
| page | int | 否 | 页码（从 1 开始） |
| page_size | int | 否 | 每页大小（默认 20，最大 100） |

**请求示例**:
```bash
GET /api/v1/translation/sessions/550e8400-e29b-41d4-a716-446655440000/tasks?status=failed&page=1
```

**响应示例**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "total": 5,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "items": [
    {
      "task_id": "task_001",
      "batch_id": "batch_001",
      "sheet_name": "Dialogue",
      "row_index": 10,
      "column_name": "Text",
      "source_text": "Hello, adventurer!",
      "target_text": null,
      "status": "failed",
      "error_message": "API rate limit exceeded",
      "retry_count": 3,
      "confidence": null,
      "created_at": "2025-09-30T10:01:00Z",
      "updated_at": "2025-09-30T10:03:00Z"
    }
  ]
}
```

**调用示例**:
```bash
curl "http://localhost:8001/api/v1/translation/sessions/550e8400-e29b-41d4-a716-446655440000/tasks?status=failed"
```

---

### 4.4 查询单个任务

查询指定任务的详细信息。

**端点**: `GET /api/v1/translation/tasks/{task_id}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| task_id | string | 任务 ID |

**响应示例**:
```json
{
  "task_id": "task_001",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "batch_id": "batch_001",
  "sheet_name": "Dialogue",
  "row_index": 10,
  "column_name": "Text",
  "source_text": "Hello, adventurer!",
  "target_text": "你好，冒险者！",
  "context": "NPC greeting dialogue",
  "status": "completed",
  "confidence": 0.95,
  "error_message": null,
  "retry_count": 0,
  "start_time": "2025-09-30T10:10:00Z",
  "end_time": "2025-09-30T10:10:05Z",
  "duration_ms": 5000,
  "created_at": "2025-09-30T10:09:00Z",
  "updated_at": "2025-09-30T10:10:05Z"
}
```

**调用示例**:
```bash
curl http://localhost:8001/api/v1/translation/tasks/task_001
```

---

### 4.5 查询任务列表

查询所有任务列表（跨会话），支持分页和过滤。

**端点**: `GET /api/v1/translation/tasks`

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | string | 否 | 过滤会话 ID |
| status | string | 否 | 过滤状态 |
| from_date | string | 否 | 起始日期 |
| to_date | string | 否 | 结束日期 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页大小 |

**请求示例**:
```bash
GET /api/v1/translation/tasks?status=completed&page=1&page_size=50
```

**响应示例**:
```json
{
  "total": 10000,
  "page": 1,
  "page_size": 50,
  "total_pages": 200,
  "items": [...]
}
```

---

## 5. 恢复 API

### 5.1 获取未完成会话列表

获取所有状态为 processing 或 pending 的会话，用于服务重启后恢复。

**端点**: `GET /api/v1/translation/recovery/incomplete-sessions`

**请求参数**: 无

**响应示例**:
```json
{
  "count": 3,
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "game.xlsx",
      "status": "processing",
      "total_tasks": 1000,
      "completed_tasks": 350,
      "pending_tasks": 640,
      "failed_tasks": 10,
      "created_at": "2025-09-30T10:00:00Z",
      "updated_at": "2025-09-30T10:05:00Z"
    },
    {
      "session_id": "660f9511-f3ac-52e5-b827-557766551111",
      "filename": "game2.xlsx",
      "status": "pending",
      "total_tasks": 500,
      "completed_tasks": 0,
      "pending_tasks": 500,
      "failed_tasks": 0,
      "created_at": "2025-09-30T09:50:00Z",
      "updated_at": "2025-09-30T09:50:00Z"
    }
  ]
}
```

**调用示例**:
```bash
curl http://localhost:8001/api/v1/translation/recovery/incomplete-sessions
```

**使用场景**:
```python
# Backend V2 启动时调用
async def on_startup():
    # 1. 获取未完成会话
    response = await client.get("/api/v1/translation/recovery/incomplete-sessions")
    sessions = response.json()['sessions']

    logger.info(f"Found {len(sessions)} incomplete sessions")

    # 2. 对每个会话执行恢复
    for session in sessions:
        await restore_session(session['session_id'])
```

---

### 5.2 恢复会话数据

恢复指定会话的完整数据（会话信息 + 所有未完成任务）。

**端点**: `POST /api/v1/translation/recovery/restore/{session_id}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |

**请求体**: 无

**响应示例**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "session": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "game.xlsx",
    "file_path": "/uploads/game.xlsx",
    "status": "processing",
    "game_info": {...},
    "llm_provider": "openai",
    "total_tasks": 1000,
    "completed_tasks": 350,
    "failed_tasks": 10,
    "pending_tasks": 640
  },
  "tasks_count": 640,
  "tasks": [
    {
      "task_id": "task_351",
      "batch_id": "batch_036",
      "sheet_name": "Dialogue",
      "row_index": 350,
      "column_name": "Text",
      "source_text": "...",
      "status": "pending",
      "created_at": "2025-09-30T10:01:00Z"
    },
    // ... 更多任务（只返回 pending 和 processing 状态）
  ],
  "restored_at": "2025-09-30T10:30:00Z"
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| session | object | 会话详细信息 |
| tasks_count | int | 恢复的任务数量 |
| tasks | array | 未完成的任务列表 |
| restored_at | string | 恢复时间戳 |

**调用示例**:
```bash
curl -X POST http://localhost:8001/api/v1/translation/recovery/restore/550e8400-e29b-41d4-a716-446655440000
```

**使用场景**:
```python
async def restore_session(session_id: str):
    """恢复会话到内存"""
    # 1. 调用恢复 API
    response = await client.post(f"/api/v1/translation/recovery/restore/{session_id}")
    data = response.json()

    # 2. 重建 TaskDataFrame
    task_manager = TaskDataFrameManager()
    task_manager.load_from_dict({
        'session_id': data['session']['session_id'],
        'filename': data['session']['filename'],
        'tasks': data['tasks']
    })

    # 3. 注册到 session_manager
    session_manager.register(session_id, task_manager)

    logger.info(f"Restored session {session_id} with {data['tasks_count']} tasks")
```

---

## 6. 管理 API

### 6.1 删除会话

删除指定会话及其所有任务（级联删除）。

**端点**: `DELETE /api/v1/translation/sessions/{session_id}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话 ID |

**响应示例**:
```json
{
  "status": "deleted",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "deleted_tasks": 1000
}
```

**调用示例**:
```bash
curl -X DELETE http://localhost:8001/api/v1/translation/sessions/550e8400-e29b-41d4-a716-446655440000
```

**业务规则**:
- 级联删除所有相关任务
- 不可恢复
- 建议仅删除已完成或失败的会话

---

### 6.2 清理过期数据

根据配置的保留期清理过期数据。

**端点**: `POST /api/v1/translation/sessions/cleanup`

**请求体**:
```json
{
  "completed_days": 90,
  "failed_days": 30,
  "dry_run": false
}
```

**请求字段说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| completed_days | int | 否 | 已完成会话保留天数（默认 90） |
| failed_days | int | 否 | 失败会话保留天数（默认 30） |
| dry_run | bool | 否 | 是否仅模拟（不实际删除） |

**响应示例**:
```json
{
  "status": "completed",
  "deleted_sessions": 150,
  "deleted_tasks": 150000,
  "dry_run": false
}
```

**调用示例**:
```bash
# 模拟清理（查看会删除多少）
curl -X POST http://localhost:8001/api/v1/translation/sessions/cleanup \
  -H "Content-Type: application/json" \
  -d '{"dry_run": true}'

# 实际清理
curl -X POST http://localhost:8001/api/v1/translation/sessions/cleanup \
  -H "Content-Type: application/json" \
  -d '{"completed_days": 90, "failed_days": 30, "dry_run": false}'
```

---

### 6.3 获取统计信息

获取翻译数据的统计信息。

**端点**: `GET /api/v1/translation/stats`

**响应示例**:
```json
{
  "sessions": {
    "total": 1000,
    "pending": 50,
    "processing": 30,
    "completed": 900,
    "failed": 20
  },
  "tasks": {
    "total": 1000000,
    "pending": 5000,
    "processing": 3000,
    "completed": 980000,
    "failed": 12000
  },
  "performance": {
    "average_session_time": 1800,
    "average_task_time": 5.2,
    "success_rate": 98.8
  },
  "storage": {
    "database_size_mb": 2048,
    "sessions_table_rows": 1000,
    "tasks_table_rows": 1000000
  }
}
```

**调用示例**:
```bash
curl http://localhost:8001/api/v1/translation/stats
```

---

## 7. 系统 API

### 7.1 健康检查

检查服务健康状态。

**端点**: `GET /health`

**响应示例**:
```json
{
  "status": "healthy",
  "database": "healthy",
  "buffer": {
    "sessions_count": 150,
    "tasks_count": 850,
    "total_count": 1000,
    "capacity": 1000,
    "usage_percent": 100.0,
    "last_flush": "2025-09-30T10:15:00Z"
  },
  "uptime_seconds": 86400,
  "version": "1.0.0"
}
```

**调用示例**:
```bash
curl http://localhost:8001/health
```

---

### 7.2 性能指标

获取服务性能指标（Prometheus 格式）。

**端点**: `GET /api/v1/system/metrics`

**响应示例**:
```
# HELP persistence_api_requests_total Total API requests
# TYPE persistence_api_requests_total counter
persistence_api_requests_total{endpoint="/api/v1/translation/sessions/batch",method="POST"} 1000

# HELP persistence_api_duration_seconds API request duration
# TYPE persistence_api_duration_seconds histogram
persistence_api_duration_seconds_bucket{endpoint="/api/v1/translation/sessions/batch",le="0.005"} 800
persistence_api_duration_seconds_bucket{endpoint="/api/v1/translation/sessions/batch",le="0.01"} 950
persistence_api_duration_seconds_bucket{endpoint="/api/v1/translation/sessions/batch",le="+Inf"} 1000

# HELP persistence_buffer_size Current buffer size
# TYPE persistence_buffer_size gauge
persistence_buffer_size{type="session"} 150
persistence_buffer_size{type="task"} 850

# HELP persistence_flush_total Total flush operations
# TYPE persistence_flush_total counter
persistence_flush_total 45
```

---

## 8. 数据模型

### 8.1 数据库表结构

#### translation_sessions 表

```sql
CREATE TABLE translation_sessions (
    session_id VARCHAR(36) PRIMARY KEY COMMENT '会话ID',
    filename VARCHAR(255) NOT NULL COMMENT '文件名',
    file_path VARCHAR(512) NOT NULL COMMENT '文件路径',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态',
    game_info JSON COMMENT '游戏信息',
    llm_provider VARCHAR(50) NOT NULL COMMENT 'LLM提供商',
    metadata JSON COMMENT '元数据',
    total_tasks INT DEFAULT 0 COMMENT '总任务数',
    completed_tasks INT DEFAULT 0 COMMENT '完成任务数',
    failed_tasks INT DEFAULT 0 COMMENT '失败任务数',
    processing_tasks INT DEFAULT 0 COMMENT '处理中任务数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### translation_tasks 表

```sql
CREATE TABLE translation_tasks (
    task_id VARCHAR(64) PRIMARY KEY COMMENT '任务ID',
    session_id VARCHAR(36) NOT NULL COMMENT '会话ID',
    batch_id VARCHAR(64) NOT NULL COMMENT '批次ID',
    sheet_name VARCHAR(255) NOT NULL COMMENT '工作表名',
    row_index INT NOT NULL COMMENT '行索引',
    column_name VARCHAR(255) NOT NULL COMMENT '列名',
    source_text TEXT NOT NULL COMMENT '源文本',
    target_text TEXT COMMENT '翻译结果',
    context TEXT COMMENT '上下文',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态',
    confidence DECIMAL(5,4) COMMENT '置信度',
    error_message TEXT COMMENT '错误信息',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    start_time TIMESTAMP NULL COMMENT '开始时间',
    end_time TIMESTAMP NULL COMMENT '结束时间',
    duration_ms INT COMMENT '耗时（毫秒）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (session_id) REFERENCES translation_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_batch_id (batch_id),
    INDEX idx_status (status),
    INDEX idx_session_status (session_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 8.2 状态枚举

#### 会话状态（status）

| 值 | 说明 |
|----|------|
| pending | 待开始 |
| processing | 处理中 |
| completed | 已完成 |
| failed | 失败 |
| cancelled | 已取消 |

#### 任务状态（status）

| 值 | 说明 |
|----|------|
| pending | 待处理 |
| processing | 处理中 |
| completed | 已完成 |
| failed | 失败 |

---

## 9. 错误码

### HTTP 状态码

| 状态码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | 无需处理 |
| 202 | 已接受（异步处理） | 无需处理 |
| 400 | 请求格式错误 | 检查请求参数 |
| 404 | 资源不存在 | 检查 ID 是否正确 |
| 422 | 数据验证失败 | 检查必填字段 |
| 500 | 服务内部错误 | 记录日志，联系管理员 |
| 503 | 服务不可用 | 稍后重试 |

### 错误响应格式

```json
{
  "detail": "错误描述",
  "error_code": "ERROR_CODE",
  "errors": [
    {
      "field": "字段名",
      "message": "错误信息"
    }
  ]
}
```

---

## 10. 客户端示例

### 10.1 Python 客户端

```python
import httpx
import asyncio
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class PersistenceClient:
    """持久化服务客户端"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session_buffer = []
        self.task_buffer = []
        self.batch_size = 100

    async def persist_session(self, session: Dict):
        """持久化单个会话"""
        self.session_buffer.append(session)
        if len(self.session_buffer) >= self.batch_size:
            await self._flush_sessions()

    async def persist_tasks(self, tasks: List[Dict]):
        """持久化任务列表"""
        self.task_buffer.extend(tasks)
        if len(self.task_buffer) >= self.batch_size:
            await self._flush_tasks()

    async def _flush_sessions(self):
        """发送会话批次"""
        if not self.session_buffer:
            return

        batch = self.session_buffer[:self.batch_size]
        self.session_buffer = self.session_buffer[self.batch_size:]

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/translation/sessions/batch",
                    json={"sessions": batch}
                )
                response.raise_for_status()
                logger.info(f"Persisted {len(batch)} sessions")
        except Exception as e:
            logger.warning(f"Failed to persist sessions: {e}")

    async def _flush_tasks(self):
        """发送任务批次"""
        if not self.task_buffer:
            return

        batch = self.task_buffer[:self.batch_size]
        self.task_buffer = self.task_buffer[self.batch_size:]

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/translation/tasks/batch",
                    json={"tasks": batch}
                )
                response.raise_for_status()
                logger.info(f"Persisted {len(batch)} tasks")
        except Exception as e:
            logger.warning(f"Failed to persist tasks: {e}")

    async def flush_all(self):
        """强制刷新所有缓冲区"""
        await self._flush_sessions()
        await self._flush_tasks()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{self.base_url}/api/v1/translation/flush")
                result = response.json()
                logger.info(f"Server flushed: {result}")
                return result
        except Exception as e:
            logger.error(f"Failed to flush on server: {e}")
            return None

    async def get_incomplete_sessions(self) -> List[Dict]:
        """获取未完成的会话"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/translation/recovery/incomplete-sessions"
                )
                response.raise_for_status()
                return response.json()['sessions']
        except Exception as e:
            logger.error(f"Failed to get incomplete sessions: {e}")
            return []

    async def restore_session(self, session_id: str) -> Dict:
        """恢复会话数据"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/translation/recovery/restore/{session_id}"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to restore session {session_id}: {e}")
            raise

    async def query_session(self, session_id: str) -> Dict:
        """查询会话详情"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/translation/sessions/{session_id}"
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to query session {session_id}: {e}")
            return None


# 全局客户端实例
persistence_client = PersistenceClient()
```

### 10.2 使用示例

```python
# 示例 1: 持久化会话
session_data = {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "game.xlsx",
    "file_path": "/uploads/game.xlsx",
    "status": "processing",
    "llm_provider": "openai",
    "total_tasks": 1000
}
await persistence_client.persist_session(session_data)

# 示例 2: 持久化任务
tasks_data = [
    {
        "task_id": f"task_{i}",
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "batch_id": "batch_001",
        "sheet_name": "Dialogue",
        "row_index": i,
        "column_name": "Text",
        "source_text": f"Text {i}",
        "status": "pending"
    }
    for i in range(100)
]
await persistence_client.persist_tasks(tasks_data)

# 示例 3: 停止时强制刷新
await persistence_client.flush_all()

# 示例 4: 启动时恢复会话
incomplete_sessions = await persistence_client.get_incomplete_sessions()
for session in incomplete_sessions:
    restored_data = await persistence_client.restore_session(session['session_id'])
    # 重建内存状态...
```

---

## 附录

### A. 性能建议

1. **批量大小**：建议每批 100-500 条，不超过 1000 条
2. **调用频率**：建议每 10-30 秒调用一次
3. **超时设置**：
   - 写入操作：2 秒
   - 查询操作：5 秒
   - 刷新操作：10 秒
   - 恢复操作：30 秒

### B. 最佳实践

1. **停止/暂停时必须调用 flush**：确保数据立即写入
2. **启动时必须调用恢复接口**：恢复未完成会话
3. **不要重试失败的写入**：接受数据丢失
4. **定期调用清理接口**：避免数据库膨胀

### C. 常见问题

**Q: 数据多久会写入数据库？**
A: 最多 30 秒或 1000 条，取决于哪个条件先满足。

**Q: 写入失败怎么办？**
A: 客户端不需要重试，接受数据丢失（进度跟踪场景）。

**Q: 如何确保数据立即写入？**
A: 调用 `/api/v1/translation/flush` 强制刷新。

**Q: 恢复接口返回所有任务吗？**
A: 只返回状态为 pending 和 processing 的任务。

---

**最后更新**: 2025-09-30
**API 版本**: v1.0
**维护者**: Architecture Team