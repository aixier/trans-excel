# Persistence Service - 数据模型设计

## 1. API 数据模型（Pydantic）

### 1.1 会话模型

#### SessionData（请求模型）

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class SessionData(BaseModel):
    """会话数据模型"""
    session_id: str = Field(..., description="会话唯一标识（UUID）")
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    status: str = Field(..., description="状态：pending/processing/completed/failed")
    game_info: Optional[Dict[str, Any]] = Field(None, description="游戏信息（JSON）")
    llm_provider: str = Field(..., description="LLM提供商：openai/qwen")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据（JSON）")
    total_tasks: int = Field(0, description="总任务数")
    completed_tasks: int = Field(0, description="完成任务数")
    failed_tasks: int = Field(0, description="失败任务数")
    processing_tasks: int = Field(0, description="处理中任务数")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "game_translation.xlsx",
                "file_path": "/uploads/game_translation.xlsx",
                "status": "processing",
                "game_info": {
                    "game_name": "Fantasy RPG",
                    "source_language": "en",
                    "target_language": "zh"
                },
                "llm_provider": "openai",
                "total_tasks": 1000
            }
        }
```

#### SessionBatchRequest（批量请求）

```python
class SessionBatchRequest(BaseModel):
    """会话批量持久化请求"""
    sessions: List[SessionData] = Field(..., description="会话列表")

    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [
                    {
                        "session_id": "550e8400-e29b-41d4-a716-446655440000",
                        "filename": "test.xlsx",
                        "file_path": "/uploads/test.xlsx",
                        "status": "processing",
                        "llm_provider": "openai"
                    }
                ]
            }
        }
```

#### SessionBatchResponse（批量响应）

```python
class SessionBatchResponse(BaseModel):
    """会话批量持久化响应"""
    status: str = Field(..., description="接受状态：accepted/rejected")
    count: int = Field(..., description="已接受的会话数量")
    timestamp: datetime = Field(..., description="接受时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "accepted",
                "count": 1,
                "timestamp": "2025-09-30T16:35:00"
            }
        }
```

### 1.2 任务模型

#### TaskData（请求模型）

```python
class TaskData(BaseModel):
    """任务数据模型"""
    task_id: str = Field(..., description="任务唯一标识")
    session_id: str = Field(..., description="所属会话ID")
    batch_id: str = Field(..., description="批次ID")
    sheet_name: str = Field(..., description="工作表名称")
    row_index: int = Field(..., description="行索引")
    column_name: str = Field(..., description="列名")
    source_text: str = Field(..., description="源文本")
    target_text: Optional[str] = Field(None, description="翻译结果")
    context: Optional[str] = Field(None, description="上下文信息")
    status: str = Field(..., description="状态：pending/processing/completed/failed")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="置信度（0-1）")
    error_message: Optional[str] = Field(None, description="错误信息")
    retry_count: int = Field(0, description="重试次数")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration_ms: Optional[int] = Field(None, description="执行耗时（毫秒）")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_001",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "batch_id": "batch_001",
                "sheet_name": "Dialogue",
                "row_index": 10,
                "column_name": "Text",
                "source_text": "Hello, adventurer!",
                "target_text": "你好，冒险者！",
                "status": "completed",
                "confidence": 0.95,
                "duration_ms": 1200
            }
        }
```

#### TaskBatchRequest（批量请求）

```python
class TaskBatchRequest(BaseModel):
    """任务批量持久化请求"""
    tasks: List[TaskData] = Field(..., description="任务列表")

    class Config:
        json_schema_extra = {
            "example": {
                "tasks": [
                    {
                        "task_id": "task_001",
                        "session_id": "550e8400-e29b-41d4-a716-446655440000",
                        "batch_id": "batch_001",
                        "sheet_name": "Dialogue",
                        "row_index": 10,
                        "column_name": "Text",
                        "source_text": "Hello",
                        "status": "pending"
                    }
                ]
            }
        }
```

#### TaskBatchResponse（批量响应）

```python
class TaskBatchResponse(BaseModel):
    """任务批量持久化响应"""
    status: str = Field(..., description="接受状态：accepted/rejected")
    count: int = Field(..., description="已接受的任务数量")
    timestamp: datetime = Field(..., description="接受时间戳")
```

### 1.3 缓冲区统计模型

#### BufferStats（缓冲区统计）

```python
class BufferStats(BaseModel):
    """缓冲区统计信息"""
    sessions_count: int = Field(..., description="会话缓冲区大小")
    tasks_count: int = Field(..., description="任务缓冲区大小")
    total_count: int = Field(..., description="总缓冲区大小")
    capacity: int = Field(..., description="缓冲区容量")
    usage_percent: float = Field(..., description="使用百分比")
```

#### FlushInfo（刷新信息）

```python
class FlushInfo(BaseModel):
    """刷新信息"""
    last_flush_time: datetime = Field(..., description="上次刷新时间")
    next_flush_time: datetime = Field(..., description="下次刷新时间")
    flush_count_today: int = Field(..., description="今日刷新次数")
    average_flush_duration_ms: int = Field(..., description="平均刷新耗时")
```

#### PerformanceStats（性能统计）

```python
class PerformanceStats(BaseModel):
    """性能统计信息"""
    total_sessions_written: int = Field(..., description="总写入会话数")
    total_tasks_written: int = Field(..., description="总写入任务数")
    total_flush_count: int = Field(..., description="总刷新次数")
    average_batch_size: int = Field(..., description="平均批次大小")
    uptime_seconds: int = Field(..., description="运行时间（秒）")
```

#### StatsResponse（统计响应）

```python
class StatsResponse(BaseModel):
    """统计信息响应"""
    buffer: BufferStats
    flush_info: FlushInfo
    performance: PerformanceStats
```

### 1.4 刷新响应模型

#### FlushResponse（刷新响应）

```python
class FlushResponse(BaseModel):
    """强制刷新响应"""
    status: str = Field(..., description="刷新状态：flushed/error")
    sessions_written: int = Field(..., description="写入的会话数量")
    tasks_written: int = Field(..., description="写入的任务数量")
    duration_ms: int = Field(..., description="刷新耗时（毫秒）")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "flushed",
                "sessions_written": 150,
                "tasks_written": 850,
                "duration_ms": 1200
            }
        }
```

### 1.5 健康检查模型

#### HealthResponse（健康检查响应）

```python
class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态：healthy/unhealthy")
    database: str = Field(..., description="数据库状态：healthy/unhealthy")
    buffer: Dict[str, Any] = Field(..., description="缓冲区信息")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "database": "healthy",
                "buffer": {
                    "sessions_count": 150,
                    "tasks_count": 850,
                    "last_flush": "2025-09-30T16:30:00"
                }
            }
        }
```

## 2. 数据库模型（MySQL 表结构）

### 2.1 translation_sessions 表

```sql
CREATE TABLE translation_sessions (
    session_id VARCHAR(36) PRIMARY KEY COMMENT '会话唯一标识（UUID）',
    filename VARCHAR(255) NOT NULL COMMENT '文件名',
    file_path VARCHAR(512) NOT NULL COMMENT '文件路径',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态：pending/processing/completed/failed/cancelled',
    game_info JSON COMMENT '游戏信息',
    llm_provider VARCHAR(50) NOT NULL COMMENT 'LLM提供商：openai/qwen',
    metadata JSON COMMENT '元数据',
    total_tasks INT DEFAULT 0 COMMENT '总任务数',
    completed_tasks INT DEFAULT 0 COMMENT '完成任务数',
    failed_tasks INT DEFAULT 0 COMMENT '失败任务数',
    processing_tasks INT DEFAULT 0 COMMENT '处理中任务数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_llm_provider (llm_provider)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='翻译会话表';
```

**字段说明：**

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| session_id | VARCHAR(36) | 会话唯一标识（UUID格式） | 主键 |
| filename | VARCHAR(255) | 上传的文件名 | 非空 |
| file_path | VARCHAR(512) | 文件在服务器的路径 | 非空 |
| status | VARCHAR(20) | 会话状态 | 非空，默认pending |
| game_info | JSON | 游戏元信息（名称、语言对等） | 可空 |
| llm_provider | VARCHAR(50) | 使用的LLM服务商 | 非空 |
| metadata | JSON | 其他元数据 | 可空 |
| total_tasks | INT | 总任务数 | 默认0 |
| completed_tasks | INT | 已完成任务数 | 默认0 |
| failed_tasks | INT | 失败任务数 | 默认0 |
| processing_tasks | INT | 处理中任务数 | 默认0 |
| created_at | TIMESTAMP | 创建时间 | 自动设置 |
| updated_at | TIMESTAMP | 更新时间 | 自动更新 |

### 2.2 translation_tasks 表

```sql
CREATE TABLE translation_tasks (
    task_id VARCHAR(64) PRIMARY KEY COMMENT '任务唯一标识',
    session_id VARCHAR(36) NOT NULL COMMENT '所属会话ID',
    batch_id VARCHAR(64) NOT NULL COMMENT '批次ID',
    sheet_name VARCHAR(255) NOT NULL COMMENT '工作表名称',
    row_index INT NOT NULL COMMENT '行索引',
    column_name VARCHAR(255) NOT NULL COMMENT '列名',
    source_text TEXT NOT NULL COMMENT '源文本',
    target_text TEXT COMMENT '翻译结果',
    context TEXT COMMENT '上下文信息',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态：pending/processing/completed/failed',
    confidence DECIMAL(5,4) COMMENT '置信度（0-1）',
    error_message TEXT COMMENT '错误信息',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    start_time TIMESTAMP NULL COMMENT '开始时间',
    end_time TIMESTAMP NULL COMMENT '结束时间',
    duration_ms INT COMMENT '执行耗时（毫秒）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (session_id) REFERENCES translation_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_batch_id (batch_id),
    INDEX idx_status (status),
    INDEX idx_sheet_row (sheet_name, row_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='翻译任务表';
```

**字段说明：**

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| task_id | VARCHAR(64) | 任务唯一标识 | 主键 |
| session_id | VARCHAR(36) | 所属会话ID | 外键，级联删除 |
| batch_id | VARCHAR(64) | 批次标识 | 非空 |
| sheet_name | VARCHAR(255) | Excel工作表名称 | 非空 |
| row_index | INT | Excel行索引 | 非空 |
| column_name | VARCHAR(255) | Excel列名 | 非空 |
| source_text | TEXT | 原文 | 非空 |
| target_text | TEXT | 译文 | 可空 |
| context | TEXT | 上下文信息 | 可空 |
| status | VARCHAR(20) | 任务状态 | 非空，默认pending |
| confidence | DECIMAL(5,4) | 翻译置信度（0-1） | 可空 |
| error_message | TEXT | 错误信息 | 可空 |
| retry_count | INT | 重试次数 | 默认0 |
| start_time | TIMESTAMP | 任务开始时间 | 可空 |
| end_time | TIMESTAMP | 任务结束时间 | 可空 |
| duration_ms | INT | 执行耗时（毫秒） | 可空 |
| created_at | TIMESTAMP | 创建时间 | 自动设置 |
| updated_at | TIMESTAMP | 更新时间 | 自动更新 |

## 3. 内部数据结构

### 3.1 缓冲区结构

```python
class BufferManager:
    """缓冲区管理器的内部数据结构"""

    # 会话缓冲区（列表）
    session_buffer: List[Dict[str, Any]] = []

    # 任务缓冲区（列表）
    task_buffer: List[Dict[str, Any]] = []

    # 统计信息
    stats: Dict[str, Any] = {
        'total_sessions_written': 0,
        'total_tasks_written': 0,
        'total_flush_count': 0,
        'last_flush_time': None,
        'start_time': None
    }
```

**缓冲区示例：**

```python
# session_buffer 示例
[
    {
        'session_id': 'xxx-xxx-xxx',
        'filename': 'test.xlsx',
        'status': 'processing',
        # ... 其他字段
    },
    # ... 更多会话
]

# task_buffer 示例
[
    {
        'task_id': 'task_001',
        'session_id': 'xxx-xxx-xxx',
        'source_text': 'Hello',
        'status': 'completed',
        # ... 其他字段
    },
    # ... 更多任务
]
```

## 4. 数据转换流程

### 4.1 API → 缓冲区

```
客户端 JSON
    ↓
Pydantic 模型验证
    ↓
转换为 Dict
    ↓
添加到缓冲区 List
```

### 4.2 缓冲区 → 数据库

```
缓冲区 List[Dict]
    ↓
批量构建 SQL（INSERT ... ON DUPLICATE KEY UPDATE）
    ↓
执行数据库批量写入
    ↓
清空缓冲区
```

### 4.3 幂等性保证

**会话表 Upsert 语句：**

```sql
INSERT INTO translation_sessions
    (session_id, filename, file_path, status, ...)
VALUES
    (%s, %s, %s, %s, ...)
ON DUPLICATE KEY UPDATE
    updated_at = CURRENT_TIMESTAMP,
    status = VALUES(status),
    total_tasks = GREATEST(total_tasks, VALUES(total_tasks)),
    completed_tasks = GREATEST(completed_tasks, VALUES(completed_tasks)),
    failed_tasks = GREATEST(failed_tasks, VALUES(failed_tasks)),
    processing_tasks = VALUES(processing_tasks);
```

**任务表 Upsert 语句：**

```sql
INSERT INTO translation_tasks
    (task_id, session_id, batch_id, source_text, ...)
VALUES
    (%s, %s, %s, %s, ...)
ON DUPLICATE KEY UPDATE
    updated_at = CURRENT_TIMESTAMP,
    status = VALUES(status),
    target_text = VALUES(target_text),
    confidence = VALUES(confidence),
    end_time = VALUES(end_time),
    duration_ms = VALUES(duration_ms);
```

## 5. 数据验证规则

### 5.1 必填字段验证

**会话：**
- session_id: 必填，UUID 格式
- filename: 必填，非空字符串
- file_path: 必填，非空字符串
- status: 必填，枚举值（pending/processing/completed/failed）
- llm_provider: 必填，非空字符串

**任务：**
- task_id: 必填，非空字符串
- session_id: 必填，UUID 格式
- batch_id: 必填，非空字符串
- sheet_name: 必填，非空字符串
- row_index: 必填，整数
- column_name: 必填，非空字符串
- source_text: 必填，非空字符串
- status: 必填，枚举值（pending/processing/completed/failed）

### 5.2 数据类型验证

```python
# Pydantic 自动验证
- str: 字符串类型
- int: 整数类型（自动转换）
- float: 浮点数类型（自动转换）
- datetime: 日期时间（支持 ISO 8601 字符串）
- Dict[str, Any]: JSON 对象
- Optional[T]: 可选字段

# 自定义验证
- confidence: 0 <= value <= 1
- status: 必须在枚举值中
```

### 5.3 数据大小限制

```python
# API 请求限制
MAX_BATCH_SIZE = 1000           # 单次请求最多 1000 条
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB

# 字段长度限制（与数据库对应）
filename: 255 字符
file_path: 512 字符
session_id: 36 字符（UUID）
task_id: 64 字符
column_name: 255 字符
sheet_name: 255 字符
source_text: 65535 字符（TEXT 类型）
```

## 6. 数据模型文件组织

```
models/
├── __init__.py              # 导出所有模型
├── api_models.py            # API 请求/响应模型
│   ├── SessionData
│   ├── SessionBatchRequest
│   ├── TaskData
│   ├── TaskBatchRequest
│   └── ...
├── db_models.py             # 数据库表模型（可选）
└── internal_models.py       # 内部数据结构
```

## 7. 使用示例

### 7.1 创建 API 请求

```python
from models.api_models import SessionData, SessionBatchRequest

# 创建单个会话
session = SessionData(
    session_id="550e8400-e29b-41d4-a716-446655440000",
    filename="game.xlsx",
    file_path="/uploads/game.xlsx",
    status="processing",
    llm_provider="openai",
    total_tasks=1000
)

# 创建批量请求
request = SessionBatchRequest(
    sessions=[session]
)

# 转换为 JSON
json_data = request.model_dump_json()
```

### 7.2 解析 API 响应

```python
from models.api_models import SessionBatchResponse

# 解析响应
response_data = {"status": "accepted", "count": 1, "timestamp": "2025-09-30T16:35:00"}
response = SessionBatchResponse(**response_data)

print(f"Status: {response.status}")
print(f"Count: {response.count}")
```