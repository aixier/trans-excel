# Persistence Service - API 接口文档

## 基础信息

- **Base URL**: `http://localhost:8001`
- **Content-Type**: `application/json`
- **认证方式**: 无（内部服务）

## 1. 健康检查

### 1.1 简单健康检查

**端点**: `GET /`

**描述**: 快速检查服务是否运行

**请求示例**:
```bash
curl http://localhost:8001/
```

**响应示例**:
```json
{
  "service": "Persistence Service",
  "status": "running",
  "version": "1.0.0"
}
```

### 1.2 详细健康检查

**端点**: `GET /health`

**描述**: 获取详细的服务健康状态

**请求示例**:
```bash
curl http://localhost:8001/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "database": "healthy",
  "buffer": {
    "sessions_count": 150,
    "tasks_count": 850,
    "last_flush": "2025-09-30T16:30:00"
  }
}
```

**响应字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 服务整体状态：healthy/unhealthy |
| database | string | 数据库连接状态：healthy/unhealthy |
| buffer.sessions_count | int | 当前缓冲区中的会话数量 |
| buffer.tasks_count | int | 当前缓冲区中的任务数量 |
| buffer.last_flush | string | 上次刷新时间（ISO 8601 格式） |

## 2. 批量持久化 API

### 2.1 批量持久化会话

**端点**: `POST /api/v1/persistence/sessions/batch`

**描述**: 批量创建或更新会话记录

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "test.xlsx",
      "file_path": "/uploads/test.xlsx",
      "status": "processing",
      "game_info": {
        "game_name": "Game Title",
        "source_language": "en",
        "target_language": "zh"
      },
      "llm_provider": "openai",
      "metadata": {
        "user_id": "user123"
      },
      "total_tasks": 100,
      "completed_tasks": 0,
      "failed_tasks": 0,
      "processing_tasks": 0
    }
  ]
}
```

**请求字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sessions | array | 是 | 会话对象数组 |
| session_id | string | 是 | 会话唯一标识（UUID） |
| filename | string | 是 | 文件名 |
| file_path | string | 是 | 文件路径 |
| status | string | 是 | 状态：pending/processing/completed/failed |
| game_info | object | 否 | 游戏信息（JSON 对象） |
| llm_provider | string | 是 | LLM 提供商：openai/qwen/etc |
| metadata | object | 否 | 元数据（JSON 对象） |
| total_tasks | int | 否 | 总任务数（默认 0） |
| completed_tasks | int | 否 | 完成任务数（默认 0） |
| failed_tasks | int | 否 | 失败任务数（默认 0） |
| processing_tasks | int | 否 | 处理中任务数（默认 0） |

**响应示例**:
```json
{
  "status": "accepted",
  "count": 1,
  "timestamp": "2025-09-30T16:35:00"
}
```

**响应字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 接受状态：accepted/rejected |
| count | int | 已接受的会话数量 |
| timestamp | string | 接受时间戳 |

**错误响应**:
```json
{
  "detail": "Invalid session data format"
}
```

**调用示例**:
```bash
curl -X POST http://localhost:8001/api/v1/persistence/sessions/batch \
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

### 2.2 批量持久化任务

**端点**: `POST /api/v1/persistence/tasks/batch`

**描述**: 批量创建或更新任务记录

**请求头**:
```
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
      "sheet_name": "Sheet1",
      "row_index": 1,
      "column_name": "Text",
      "source_text": "Hello",
      "target_text": "你好",
      "context": "Greeting context",
      "status": "completed",
      "confidence": 0.95,
      "error_message": null,
      "retry_count": 0,
      "start_time": "2025-09-30T16:35:00",
      "end_time": "2025-09-30T16:35:05",
      "duration_ms": 5000
    }
  ]
}
```

**请求字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tasks | array | 是 | 任务对象数组 |
| task_id | string | 是 | 任务唯一标识 |
| session_id | string | 是 | 所属会话 ID（外键） |
| batch_id | string | 是 | 批次 ID |
| sheet_name | string | 是 | 工作表名称 |
| row_index | int | 是 | 行索引 |
| column_name | string | 是 | 列名 |
| source_text | string | 是 | 源文本 |
| target_text | string | 否 | 翻译结果 |
| context | string | 否 | 上下文信息 |
| status | string | 是 | 状态：pending/processing/completed/failed |
| confidence | float | 否 | 置信度（0-1） |
| error_message | string | 否 | 错误信息 |
| retry_count | int | 否 | 重试次数（默认 0） |
| start_time | string | 否 | 开始时间（ISO 8601） |
| end_time | string | 否 | 结束时间（ISO 8601） |
| duration_ms | int | 否 | 执行耗时（毫秒） |

**响应示例**:
```json
{
  "status": "accepted",
  "count": 1,
  "timestamp": "2025-09-30T16:35:10"
}
```

**错误响应**:
```json
{
  "detail": "Session ID not found or invalid task data"
}
```

**调用示例**:
```bash
curl -X POST http://localhost:8001/api/v1/persistence/tasks/batch \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [{
      "task_id": "task_001",
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "batch_id": "batch_001",
      "sheet_name": "Sheet1",
      "row_index": 1,
      "column_name": "Text",
      "source_text": "Hello",
      "target_text": "你好",
      "status": "completed",
      "confidence": 0.95
    }]
  }'
```

## 3. 缓冲区管理 API

### 3.1 强制刷新缓冲区

**端点**: `POST /api/v1/persistence/flush`

**描述**: 立即将缓冲区中的所有数据写入数据库（用于关键节点如暂停/停止执行）

**请求示例**:
```bash
curl -X POST http://localhost:8001/api/v1/persistence/flush
```

**响应示例**:
```json
{
  "status": "flushed",
  "sessions_written": 150,
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

### 3.2 获取缓冲区统计

**端点**: `GET /api/v1/persistence/stats`

**描述**: 获取缓冲区的详细统计信息

**请求示例**:
```bash
curl http://localhost:8001/api/v1/persistence/stats
```

**响应示例**:
```json
{
  "buffer": {
    "sessions_count": 150,
    "tasks_count": 850,
    "total_count": 1000,
    "capacity": 1000,
    "usage_percent": 100.0
  },
  "flush_info": {
    "last_flush_time": "2025-09-30T16:30:00",
    "next_flush_time": "2025-09-30T16:30:30",
    "flush_count_today": 45,
    "average_flush_duration_ms": 800
  },
  "performance": {
    "total_sessions_written": 6750,
    "total_tasks_written": 38250,
    "total_flush_count": 45,
    "average_batch_size": 1000,
    "uptime_seconds": 86400
  }
}
```

## 4. 调用模式

### 4.1 Fire-and-Forget（推荐）

客户端发送请求后立即继续执行，不等待响应：

```python
import httpx

async def persist_tasks_async(tasks):
    """异步持久化（不等待结果）"""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            # 发送请求，超时 2 秒
            response = await client.post(
                "http://localhost:8001/api/v1/persistence/tasks/batch",
                json={"tasks": tasks}
            )
            # 不检查响应，直接返回
    except Exception as e:
        logger.warning(f"Persistence request failed: {e}")
        # 接受失败，不重试
```

### 4.2 同步确认（关键操作）

对于关键操作（如停止执行），可以等待确认：

```python
async def flush_on_stop():
    """停止时强制刷新"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "http://localhost:8001/api/v1/persistence/flush"
            )
            result = response.json()
            logger.info(f"Flushed: {result['tasks_written']} tasks")
    except Exception as e:
        logger.error(f"Flush failed: {e}")
```

## 5. 错误码

| HTTP 状态码 | 说明 | 处理建议 |
|------------|------|----------|
| 200 | 成功接受 | 无需处理 |
| 400 | 请求格式错误 | 检查数据格式 |
| 422 | 数据验证失败 | 检查必填字段 |
| 500 | 服务内部错误 | 记录日志，不重试 |
| 503 | 服务不可用 | 记录日志，不重试 |

## 6. 性能建议

### 6.1 批量大小

- **推荐**: 100-500 条/批次
- **最大**: 1000 条/批次
- **原因**: 平衡网络传输和内存占用

### 6.2 调用频率

- **推荐**: 每 10-30 秒调用一次
- **避免**: 每秒多次调用
- **原因**: 减少网络开销

### 6.3 超时设置

- **普通操作**: 2 秒超时
- **刷新操作**: 10 秒超时
- **健康检查**: 1 秒超时

### 6.4 错误处理

```python
# ✅ 推荐：简单记录，不重试
try:
    await persist_client.send_batch(tasks)
except Exception as e:
    logger.warning(f"Persistence failed: {e}")
    # 继续执行业务逻辑

# ❌ 不推荐：复杂重试逻辑
try:
    await persist_client.send_batch(tasks)
except Exception:
    for i in range(3):  # 不要这样做
        time.sleep(5)
        await persist_client.send_batch(tasks)
```

## 7. 示例：完整客户端实现

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

    async def add_session(self, session: Dict):
        """添加会话到缓冲区"""
        self.session_buffer.append(session)
        if len(self.session_buffer) >= self.batch_size:
            await self._flush_sessions()

    async def add_task(self, task: Dict):
        """添加任务到缓冲区"""
        self.task_buffer.append(task)
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
                await client.post(
                    f"{self.base_url}/api/v1/persistence/sessions/batch",
                    json={"sessions": batch}
                )
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
                await client.post(
                    f"{self.base_url}/api/v1/persistence/tasks/batch",
                    json={"tasks": batch}
                )
        except Exception as e:
            logger.warning(f"Failed to persist tasks: {e}")

    async def flush_all(self):
        """强制刷新所有缓冲区"""
        await self._flush_sessions()
        await self._flush_tasks()

        # 触发服务端刷新
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/persistence/flush"
                )
                return response.json()
        except Exception as e:
            logger.error(f"Failed to flush on server: {e}")
            return None
```

## 8. 测试

### 8.1 健康检查测试

```bash
# 测试服务是否运行
curl http://localhost:8001/health

# 预期输出
{
  "status": "healthy",
  "database": "healthy",
  "buffer": {...}
}
```

### 8.2 批量持久化测试

```bash
# 测试任务持久化
curl -X POST http://localhost:8001/api/v1/persistence/tasks/batch \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "task_id": "test_001",
        "session_id": "test_session",
        "batch_id": "test_batch",
        "sheet_name": "Sheet1",
        "row_index": 1,
        "column_name": "Text",
        "source_text": "Test",
        "status": "pending"
      }
    ]
  }'

# 预期输出
{
  "status": "accepted",
  "count": 1,
  "timestamp": "..."
}
```

### 8.3 强制刷新测试

```bash
# 测试强制刷新
curl -X POST http://localhost:8001/api/v1/persistence/flush

# 预期输出
{
  "status": "flushed",
  "sessions_written": 0,
  "tasks_written": 1,
  "duration_ms": 50
}
```