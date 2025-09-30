# Persistence Service - 开发任务清单

**项目阶段**: Phase 1 - Translation Persistence MVP
**版本**: v1.0
**创建日期**: 2025-09-30
**预计工期**: 5 周

---

## 📊 任务统计

| 状态 | 数量 | 百分比 |
|------|------|--------|
| ✅ DONE | 4 | 9% |
| 🔄 IN_PROGRESS | 0 | 0% |
| ⏳ TODO | 41 | 91% |
| **总计** | **45** | **100%** |

---

## 📋 任务分组

- [阶段 1: 项目基础设施（6 个任务）](#阶段-1-项目基础设施)
- [阶段 2: 数据库层（5 个任务）](#阶段-2-数据库层)
- [阶段 3: 数据模型层（4 个任务）](#阶段-3-数据模型层)
- [阶段 4: 存储抽象层（4 个任务）](#阶段-4-存储抽象层)
- [阶段 5: 服务层（7 个任务）](#阶段-5-服务层)
- [阶段 6: API 层（8 个任务）](#阶段-6-api-层)
- [阶段 7: 测试（7 个任务）](#阶段-7-测试)
- [阶段 8: 部署和运维（4 个任务）](#阶段-8-部署和运维)

---

## 阶段 1: 项目基础设施

### 📦 1.1 项目结构初始化

**状态**: ✅ DONE

**任务目标**:
- 创建项目目录结构
- 创建 `__init__.py` 文件
- 创建 `.gitignore`

**交付物**:
```
persistence_service/
├── api/
│   └── __init__.py
├── services/
│   └── __init__.py
├── storage/
│   └── __init__.py
├── models/
│   └── __init__.py
├── config/
│   └── __init__.py
├── tests/
│   └── __init__.py
├── main.py
└── .gitignore
```

**参考文档**:
- [ARCHITECTURE_V2.md - 项目结构](ARCHITECTURE_V2.md#9-部署和运维)

**预计工时**: 0.5 小时

**依赖**: 无

---

### 📦 1.2 依赖管理

**状态**: ✅ DONE

**任务目标**:
- 创建 `requirements.txt`
- 列出所有依赖包及版本

**交付物**:
- `requirements.txt` 文件

**依赖包列表**:
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
aiomysql==0.2.0
PyMySQL==1.1.0
PyYAML==6.0.1
python-dateutil==2.8.2
httpx==0.25.2
pytest==7.4.3
pytest-asyncio==0.21.1
```

**参考文档**:
- [ARCHITECTURE_V2.md - 技术栈](ARCHITECTURE_V2.md#附录)

**预计工时**: 0.5 小时

**依赖**: 1.1

---

### 📦 1.3 配置管理

**状态**: ✅ DONE

**任务目标**:
- 创建配置文件模板 `config/config.yaml`
- 实现配置加载类 `config/settings.py`
- 支持环境变量覆盖

**交付物**:
- `config/config.yaml` - 配置文件
- `config/settings.py` - 配置管理类

**配置项**:
```yaml
service:
  host: "0.0.0.0"
  port: 8001

buffer:
  max_buffer_size: 1000
  flush_interval: 30

database:
  host: "localhost"
  port: 3306
  user: "root"
  password: ""
  database: "ai_terminal"
  pool_size: 10
```

**参考文档**:
- [DEPLOYMENT.md - 配置管理](DEPLOYMENT.md)

**预计工时**: 2 小时

**依赖**: 1.2

---

### 📦 1.4 日志配置

**状态**: ⏳ TODO

**任务目标**:
- 配置日志格式（结构化日志）
- 配置日志级别
- 配置日志轮转

**交付物**:
- `config/logging.py` - 日志配置

**日志格式**:
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/persistence_service.log'),
        logging.StreamHandler()
    ]
)
```

**参考文档**:
- [ARCHITECTURE_V2.md - 日志记录](ARCHITECTURE_V2.md#82-日志记录)

**预计工时**: 1 小时

**依赖**: 1.3

---

### 📦 1.5 主应用入口

**状态**: ⏳ TODO

**任务目标**:
- 创建 FastAPI 应用实例
- 配置 CORS
- 配置生命周期管理（启动/关闭）
- 注册路由

**交付物**:
- `main.py` - 主应用文件

**核心代码**:
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    await mysql_connector.initialize()
    asyncio.create_task(buffer_manager.start_periodic_flush())
    yield
    # 关闭时清理
    await buffer_manager.flush()
    await mysql_connector.close()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.include_router(translation_api.router)
```

**参考文档**:
- [ARCHITECTURE_V2.md - API Layer](ARCHITECTURE_V2.md#layer-1-api-layer)

**预计工时**: 2 小时

**依赖**: 1.4

---

### 📦 1.6 文档完善

**状态**: ✅ DONE

**任务目标**:
- 创建开发文档
- 创建 API 文档
- 创建任务清单（本文档）

**交付物**:
- `docs/REQUIREMENTS_V2.md`
- `docs/ARCHITECTURE_V2.md`
- `docs/TRANSLATION_API.md`
- `docs/TASKLIST.md`

**参考文档**:
- 所有已创建的文档

**预计工时**: 已完成

**依赖**: 无

---

## 阶段 2: 数据库层

### 🗄️ 2.1 数据库表设计

**状态**: ⏳ TODO

**任务目标**:
- 编写数据库建表 SQL
- 创建索引
- 设置外键约束

**交付物**:
- `database/schema.sql` - 建表 SQL

**表结构**:
```sql
CREATE TABLE translation_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    game_info JSON,
    llm_provider VARCHAR(50) NOT NULL,
    metadata JSON,
    total_tasks INT DEFAULT 0,
    completed_tasks INT DEFAULT 0,
    failed_tasks INT DEFAULT 0,
    processing_tasks INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE translation_tasks (
    task_id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    batch_id VARCHAR(64) NOT NULL,
    sheet_name VARCHAR(255) NOT NULL,
    row_index INT NOT NULL,
    column_name VARCHAR(255) NOT NULL,
    source_text TEXT NOT NULL,
    target_text TEXT,
    context TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    confidence DECIMAL(5,4),
    error_message TEXT,
    retry_count INT DEFAULT 0,
    start_time TIMESTAMP NULL,
    end_time TIMESTAMP NULL,
    duration_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES translation_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_batch_id (batch_id),
    INDEX idx_status (status),
    INDEX idx_session_status (session_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**参考文档**:
- [TRANSLATION_API.md - 数据模型](TRANSLATION_API.md#8-数据模型)

**预计工时**: 2 小时

**依赖**: 1.3

---

### 🗄️ 2.2 数据库连接池

**状态**: ⏳ TODO

**任务目标**:
- 实现 MySQL 连接池管理
- 实现连接池初始化和关闭
- 实现连接健康检查

**交付物**:
- `database/mysql_connector.py` - MySQL 连接器

**核心方法**:
```python
class MySQLConnector:
    async def initialize(self):
        """初始化连接池"""
        self.pool = await aiomysql.create_pool(
            host=config.db_host,
            port=config.db_port,
            user=config.db_user,
            password=config.db_password,
            db=config.db_database,
            minsize=5,
            maxsize=10,
            pool_recycle=3600
        )

    async def close(self):
        """关闭连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with self.pool.acquire() as conn:
                await conn.ping()
            return True
        except Exception:
            return False
```

**参考文档**:
- [ARCHITECTURE_V2.md - MySQL Plugin](ARCHITECTURE_V2.md#41-mysql-plugin)

**预计工时**: 3 小时

**依赖**: 2.1

---

### 🗄️ 2.3 批量写入实现（Upsert）

**状态**: ⏳ TODO

**任务目标**:
- 实现批量插入会话（幂等）
- 实现批量插入任务（幂等）
- 使用 `INSERT ... ON DUPLICATE KEY UPDATE`

**交付物**:
- `database/mysql_connector.py` 中的批量写入方法

**核心方法**:
```python
async def batch_upsert_sessions(self, sessions: List[Dict]) -> int:
    """批量插入/更新会话"""
    sql = """
        INSERT INTO translation_sessions
        (session_id, filename, file_path, status, game_info, llm_provider,
         metadata, total_tasks, completed_tasks, failed_tasks, processing_tasks)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            updated_at = CURRENT_TIMESTAMP,
            status = VALUES(status),
            total_tasks = GREATEST(total_tasks, VALUES(total_tasks)),
            completed_tasks = GREATEST(completed_tasks, VALUES(completed_tasks)),
            failed_tasks = GREATEST(failed_tasks, VALUES(failed_tasks)),
            processing_tasks = VALUES(processing_tasks)
    """
    values = [(s['session_id'], s['filename'], ...) for s in sessions]
    async with self.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            affected = await cursor.executemany(sql, values)
            await conn.commit()
            return affected

async def batch_upsert_tasks(self, tasks: List[Dict]) -> int:
    """批量插入/更新任务"""
    # 类似实现
```

**参考文档**:
- [ARCHITECTURE_V2.md - 批量 Upsert](ARCHITECTURE_V2.md#layer-3-data-access-layer)

**预计工时**: 4 小时

**依赖**: 2.2

---

### 🗄️ 2.4 查询实现

**状态**: ⏳ TODO

**任务目标**:
- 实现查询会话列表（分页、过滤、排序）
- 实现查询单个会话
- 实现查询任务列表
- 实现查询单个任务

**交付物**:
- `database/mysql_connector.py` 中的查询方法

**核心方法**:
```python
async def query_sessions(
    self,
    filters: Dict[str, Any],
    pagination: Pagination
) -> QueryResult:
    """查询会话列表"""
    # 构建 WHERE 子句
    where_clauses = []
    params = []
    if filters.get('status'):
        where_clauses.append("status = %s")
        params.append(filters['status'])
    # ... 更多过滤条件

    # 构建 SQL
    sql = f"""
        SELECT * FROM translation_sessions
        WHERE {' AND '.join(where_clauses) if where_clauses else '1=1'}
        ORDER BY {pagination.sort_by} {pagination.order}
        LIMIT %s OFFSET %s
    """
    params.extend([pagination.page_size, (pagination.page - 1) * pagination.page_size])

    # 执行查询
    async with self.pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(sql, params)
            items = await cursor.fetchall()
            # 查询总数
            count_sql = "SELECT COUNT(*) FROM translation_sessions WHERE ..."
            await cursor.execute(count_sql, params[:-2])
            total = (await cursor.fetchone())['COUNT(*)']
            return QueryResult(total=total, items=items)
```

**参考文档**:
- [TRANSLATION_API.md - 查询 API](TRANSLATION_API.md#4-查询-api)

**预计工时**: 5 小时

**依赖**: 2.3

---

### 🗄️ 2.5 恢复查询实现

**状态**: ⏳ TODO

**任务目标**:
- 实现查询未完成会话
- 实现恢复会话数据（包含所有未完成任务）

**交付物**:
- `database/mysql_connector.py` 中的恢复方法

**核心方法**:
```python
async def get_incomplete_sessions(self) -> List[Dict]:
    """获取未完成的会话"""
    sql = """
        SELECT * FROM translation_sessions
        WHERE status IN ('processing', 'pending')
        ORDER BY created_at DESC
    """
    async with self.pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(sql)
            return await cursor.fetchall()

async def get_session_with_tasks(self, session_id: str) -> Dict:
    """获取会话及其所有未完成任务"""
    # 查询会话
    session = await self.get_session_by_id(session_id)

    # 查询未完成任务
    sql = """
        SELECT * FROM translation_tasks
        WHERE session_id = %s AND status IN ('pending', 'processing')
    """
    async with self.pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(sql, (session_id,))
            tasks = await cursor.fetchall()

    return {
        'session': session,
        'tasks': tasks
    }
```

**参考文档**:
- [TRANSLATION_API.md - 恢复 API](TRANSLATION_API.md#5-恢复-api)

**预计工时**: 3 小时

**依赖**: 2.4

---

## 阶段 3: 数据模型层

### 📊 3.1 API 请求模型

**状态**: ⏳ TODO

**任务目标**:
- 定义会话数据模型（Pydantic）
- 定义任务数据模型（Pydantic）
- 定义批量请求模型

**交付物**:
- `models/api_models.py` - API 数据模型

**核心模型**:
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class SessionData(BaseModel):
    session_id: str = Field(..., description="会话ID")
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    status: str = Field(..., description="状态")
    game_info: Optional[Dict[str, Any]] = Field(None, description="游戏信息")
    llm_provider: str = Field(..., description="LLM提供商")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    total_tasks: int = Field(0, description="总任务数")
    completed_tasks: int = Field(0, description="完成任务数")
    failed_tasks: int = Field(0, description="失败任务数")
    processing_tasks: int = Field(0, description="处理中任务数")

class TaskData(BaseModel):
    task_id: str = Field(..., description="任务ID")
    session_id: str = Field(..., description="会话ID")
    batch_id: str = Field(..., description="批次ID")
    sheet_name: str = Field(..., description="工作表名")
    row_index: int = Field(..., description="行索引")
    column_name: str = Field(..., description="列名")
    source_text: str = Field(..., description="源文本")
    target_text: Optional[str] = Field(None, description="翻译结果")
    context: Optional[str] = Field(None, description="上下文")
    status: str = Field(..., description="状态")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="置信度")
    error_message: Optional[str] = Field(None, description="错误信息")
    retry_count: int = Field(0, description="重试次数")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration_ms: Optional[int] = Field(None, description="耗时")

class SessionBatchRequest(BaseModel):
    sessions: List[SessionData]

class TaskBatchRequest(BaseModel):
    tasks: List[TaskData]
```

**参考文档**:
- [TRANSLATION_API.md - 批量写入](TRANSLATION_API.md#3-批量写入-api)

**预计工时**: 3 小时

**依赖**: 1.3

---

### 📊 3.2 API 响应模型

**状态**: ⏳ TODO

**任务目标**:
- 定义批量响应模型
- 定义查询响应模型
- 定义错误响应模型

**交付物**:
- `models/api_models.py` - 响应模型

**核心模型**:
```python
class BatchResponse(BaseModel):
    status: str = Field(..., description="状态")
    count: int = Field(..., description="数量")
    timestamp: datetime = Field(..., description="时间戳")

class QueryResponse(BaseModel):
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")
    items: List[Dict[str, Any]] = Field(..., description="数据项")

class FlushResponse(BaseModel):
    status: str = Field(..., description="刷新状态")
    sessions_written: int = Field(..., description="写入的会话数")
    tasks_written: int = Field(..., description="写入的任务数")
    duration_ms: int = Field(..., description="耗时")
```

**参考文档**:
- [TRANSLATION_API.md - 响应格式](TRANSLATION_API.md#31-批量写入会话)

**预计工时**: 2 小时

**依赖**: 3.1

---

### 📊 3.3 内部数据结构

**状态**: ⏳ TODO

**任务目标**:
- 定义查询过滤器
- 定义分页参数
- 定义查询结果

**交付物**:
- `models/internal_models.py` - 内部模型

**核心模型**:
```python
class Pagination(BaseModel):
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")
    sort_by: str = Field("created_at", description="排序字段")
    order: str = Field("desc", description="排序方向")

class SessionFilters(BaseModel):
    status: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None

class TaskFilters(BaseModel):
    session_id: Optional[str] = None
    status: Optional[str] = None
    sheet_name: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None

class QueryResult(BaseModel):
    total: int
    items: List[Dict[str, Any]]
```

**参考文档**:
- [ARCHITECTURE_V2.md - Query Service](ARCHITECTURE_V2.md#32-query-service)

**预计工时**: 2 小时

**依赖**: 3.2

---

### 📊 3.4 数据转换工具

**状态**: ⏳ TODO

**任务目标**:
- 实现 Pydantic 模型 → Dict 转换
- 实现 Dict → Pydantic 模型转换
- 实现 JSON 序列化辅助函数

**交付物**:
- `models/converters.py` - 数据转换工具

**核心函数**:
```python
def session_to_dict(session: SessionData) -> Dict[str, Any]:
    """SessionData → Dict"""
    return session.model_dump(exclude_none=True)

def dict_to_session(data: Dict[str, Any]) -> SessionData:
    """Dict → SessionData"""
    return SessionData(**data)

def serialize_json_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """序列化 JSON 字段（game_info, metadata）"""
    import json
    result = data.copy()
    if 'game_info' in result and isinstance(result['game_info'], dict):
        result['game_info'] = json.dumps(result['game_info'])
    if 'metadata' in result and isinstance(result['metadata'], dict):
        result['metadata'] = json.dumps(result['metadata'])
    return result
```

**参考文档**:
- Pydantic 官方文档

**预计工时**: 1 小时

**依赖**: 3.3

---

## 阶段 4: 存储抽象层

### 🔌 4.1 存储后端接口定义

**状态**: ⏳ TODO

**任务目标**:
- 定义存储后端抽象基类
- 定义统一的存储接口（write/read/query/delete）

**交付物**:
- `storage/backend.py` - 存储后端接口

**核心接口**:
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    async def write(self, collection: str, data: List[Dict]) -> int:
        """批量写入数据"""
        pass

    @abstractmethod
    async def read(self, collection: str, key: str) -> Optional[Dict]:
        """读取单条数据"""
        pass

    @abstractmethod
    async def query(
        self,
        collection: str,
        filters: Dict[str, Any],
        pagination: Pagination
    ) -> QueryResult:
        """查询数据"""
        pass

    @abstractmethod
    async def delete(self, collection: str, key: str) -> bool:
        """删除数据"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
```

**参考文档**:
- [ARCHITECTURE_V2.md - Storage Abstraction Layer](ARCHITECTURE_V2.md#layer-3-storage-abstraction-layer)

**预计工时**: 2 小时

**依赖**: 3.4

---

### 🔌 4.2 MySQL 插件实现

**状态**: ⏳ TODO

**任务目标**:
- 实现 `StorageBackend` 接口
- 实现 MySQL 的 write/read/query/delete 方法
- 集成 MySQLConnector

**交付物**:
- `storage/mysql_plugin.py` - MySQL 插件

**核心实现**:
```python
from storage.backend import StorageBackend
from database.mysql_connector import mysql_connector

class MySQLPlugin(StorageBackend):
    """MySQL 存储插件"""

    async def write(self, collection: str, data: List[Dict]) -> int:
        if collection == "translation_sessions":
            return await mysql_connector.batch_upsert_sessions(data)
        elif collection == "translation_tasks":
            return await mysql_connector.batch_upsert_tasks(data)
        else:
            raise ValueError(f"Unknown collection: {collection}")

    async def read(self, collection: str, key: str) -> Optional[Dict]:
        if collection == "translation_sessions":
            return await mysql_connector.get_session_by_id(key)
        elif collection == "translation_tasks":
            return await mysql_connector.get_task_by_id(key)
        else:
            raise ValueError(f"Unknown collection: {collection}")

    # ... 其他方法
```

**参考文档**:
- [ARCHITECTURE_V2.md - MySQL Plugin](ARCHITECTURE_V2.md#41-mysql-plugin)

**预计工时**: 3 小时

**依赖**: 4.1, 2.5

---

### 🔌 4.3 存储后端注册表

**状态**: ⏳ TODO

**任务目标**:
- 实现存储后端注册机制
- 实现集合到后端的路由规则
- 实现后端获取

**交付物**:
- `storage/registry.py` - 存储后端注册表

**核心实现**:
```python
class StorageBackendRegistry:
    """存储后端注册表"""

    _backends: Dict[str, StorageBackend] = {}
    _routing_rules: Dict[str, str] = {}

    @classmethod
    def register(cls, name: str, backend: StorageBackend):
        """注册存储后端"""
        cls._backends[name] = backend

    @classmethod
    def register_collection(cls, collection: str, backend_name: str):
        """注册集合路由规则"""
        cls._routing_rules[collection] = backend_name

    @classmethod
    def get_backend(cls, collection: str) -> StorageBackend:
        """根据集合获取存储后端"""
        backend_name = cls._routing_rules.get(collection)
        if not backend_name:
            raise ValueError(f"No backend registered for collection: {collection}")
        backend = cls._backends.get(backend_name)
        if not backend:
            raise ValueError(f"Backend not found: {backend_name}")
        return backend

# 初始化时注册
mysql_plugin = MySQLPlugin()
StorageBackendRegistry.register("mysql", mysql_plugin)
StorageBackendRegistry.register_collection("translation_sessions", "mysql")
StorageBackendRegistry.register_collection("translation_tasks", "mysql")
```

**参考文档**:
- [ARCHITECTURE_V2.md - 插件注册机制](ARCHITECTURE_V2.md#34-storage-backend-plugin-system)

**预计工时**: 2 小时

**依赖**: 4.2

---

### 🔌 4.4 存储层测试

**状态**: ⏳ TODO

**任务目标**:
- 测试 MySQL 插件的基本功能
- 测试存储后端注册表

**交付物**:
- `tests/unit/test_storage.py` - 存储层测试

**测试用例**:
```python
async def test_mysql_plugin_write():
    """测试 MySQL 写入"""
    plugin = MySQLPlugin()
    data = [{"session_id": "test", ...}]
    result = await plugin.write("translation_sessions", data)
    assert result > 0

async def test_storage_registry():
    """测试存储注册表"""
    backend = StorageBackendRegistry.get_backend("translation_sessions")
    assert isinstance(backend, MySQLPlugin)
```

**参考文档**:
- pytest-asyncio 文档

**预计工时**: 2 小时

**依赖**: 4.3

---

## 阶段 5: 服务层

### ⚙️ 5.1 Buffer Manager 实现

**状态**: ⏳ TODO

**任务目标**:
- 实现内存缓冲区管理
- 实现刷新条件检查（大小/时间）
- 实现批量刷新逻辑
- 实现定期刷新任务

**交付物**:
- `services/buffer_manager.py` - 缓冲管理器

**核心实现**:
```python
class BufferManager:
    """缓冲管理器"""

    def __init__(self, max_buffer_size: int = 1000, flush_interval: int = 30):
        self.session_buffer: List[Dict] = []
        self.task_buffer: List[Dict] = []
        self.max_buffer_size = max_buffer_size
        self.flush_interval = flush_interval
        self.last_flush_time = time.time()

    async def add_sessions(self, sessions: List[Dict]):
        """添加会话到缓冲区"""
        self.session_buffer.extend(sessions)
        await self._check_and_flush()

    async def add_tasks(self, tasks: List[Dict]):
        """添加任务到缓冲区"""
        self.task_buffer.extend(tasks)
        await self._check_and_flush()

    async def _check_and_flush(self):
        """检查是否需要刷新"""
        if self._should_flush():
            await self.flush()

    def _should_flush(self) -> bool:
        """判断是否应该刷新"""
        buffer_full = (len(self.session_buffer) >= self.max_buffer_size or
                      len(self.task_buffer) >= self.max_buffer_size)
        time_expired = (time.time() - self.last_flush_time) >= self.flush_interval
        return buffer_full or time_expired

    async def flush(self) -> Dict[str, int]:
        """刷新缓冲区到数据库"""
        if not self.session_buffer and not self.task_buffer:
            return {"sessions": 0, "tasks": 0}

        start_time = time.time()

        # 复制快照
        sessions_to_write = self.session_buffer.copy()
        tasks_to_write = self.task_buffer.copy()

        try:
            # 获取存储后端
            backend = StorageBackendRegistry.get_backend("translation_sessions")

            # 批量写入
            sessions_written = 0
            tasks_written = 0

            if sessions_to_write:
                sessions_written = await backend.write("translation_sessions", sessions_to_write)

            if tasks_to_write:
                tasks_written = await backend.write("translation_tasks", tasks_to_write)

            # 清空缓冲区
            self.session_buffer.clear()
            self.task_buffer.clear()
            self.last_flush_time = time.time()

            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Flushed: {sessions_written} sessions, {tasks_written} tasks in {duration_ms}ms")

            return {
                "sessions": sessions_written,
                "tasks": tasks_written,
                "duration_ms": duration_ms
            }

        except Exception as e:
            logger.error(f"Flush failed: {e}")
            # 失败时也清空缓冲区（接受数据丢失）
            self.session_buffer.clear()
            self.task_buffer.clear()
            raise

    async def start_periodic_flush(self):
        """启动定期刷新任务"""
        while True:
            await asyncio.sleep(self.flush_interval)
            if self.session_buffer or self.task_buffer:
                try:
                    await self.flush()
                except Exception as e:
                    logger.error(f"Periodic flush failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓冲区统计"""
        return {
            "sessions_count": len(self.session_buffer),
            "tasks_count": len(self.task_buffer),
            "total_count": len(self.session_buffer) + len(self.task_buffer),
            "capacity": self.max_buffer_size,
            "usage_percent": (len(self.task_buffer) / self.max_buffer_size) * 100,
            "last_flush_time": datetime.fromtimestamp(self.last_flush_time).isoformat()
        }

# 全局实例
buffer_manager = BufferManager()
```

**参考文档**:
- [ARCHITECTURE_V2.md - Buffer Manager](ARCHITECTURE_V2.md#31-buffer-manager)
- [TRANSLATION_API.md - 强制刷新](TRANSLATION_API.md#33-强制刷新缓冲区)

**预计工时**: 4 小时

**依赖**: 4.4

---

### ⚙️ 5.2 Query Service 实现

**状态**: ⏳ TODO

**任务目标**:
- 实现查询会话列表
- 实现查询单个会话
- 实现查询任务列表
- 实现查询单个任务
- 实现查询构建器

**交付物**:
- `services/query_service.py` - 查询服务

**核心实现**:
```python
class QueryService:
    """查询服务"""

    async def query_sessions(
        self,
        filters: SessionFilters,
        pagination: Pagination
    ) -> QueryResponse:
        """查询会话列表"""
        backend = StorageBackendRegistry.get_backend("translation_sessions")
        result = await backend.query(
            "translation_sessions",
            filters.model_dump(exclude_none=True),
            pagination
        )

        total_pages = (result.total + pagination.page_size - 1) // pagination.page_size

        return QueryResponse(
            total=result.total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            items=result.items
        )

    async def get_session(self, session_id: str) -> Optional[Dict]:
        """获取单个会话"""
        backend = StorageBackendRegistry.get_backend("translation_sessions")
        return await backend.read("translation_sessions", session_id)

    async def get_session_tasks(
        self,
        session_id: str,
        filters: TaskFilters,
        pagination: Pagination
    ) -> QueryResponse:
        """获取会话的任务列表"""
        filters.session_id = session_id
        backend = StorageBackendRegistry.get_backend("translation_tasks")
        result = await backend.query(
            "translation_tasks",
            filters.model_dump(exclude_none=True),
            pagination
        )

        total_pages = (result.total + pagination.page_size - 1) // pagination.page_size

        return QueryResponse(
            total=result.total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            items=result.items
        )

# 全局实例
query_service = QueryService()
```

**参考文档**:
- [ARCHITECTURE_V2.md - Query Service](ARCHITECTURE_V2.md#32-query-service)
- [TRANSLATION_API.md - 查询 API](TRANSLATION_API.md#4-查询-api)

**预计工时**: 4 小时

**依赖**: 5.1

---

### ⚙️ 5.3 Recovery Service 实现

**状态**: ⏳ TODO

**任务目标**:
- 实现获取未完成会话
- 实现恢复会话数据

**交付物**:
- `services/recovery_service.py` - 恢复服务

**核心实现**:
```python
class RecoveryService:
    """数据恢复服务"""

    async def get_incomplete_sessions(self) -> List[Dict]:
        """获取所有未完成的会话"""
        backend = StorageBackendRegistry.get_backend("translation_sessions")
        # 使用特殊查询
        result = await mysql_connector.get_incomplete_sessions()
        return result

    async def restore_session(self, session_id: str) -> Dict:
        """恢复指定会话的完整数据"""
        # 获取会话详情
        session = await query_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # 获取所有未完成任务
        result = await mysql_connector.get_session_with_tasks(session_id)

        return {
            "session_id": session_id,
            "session": result['session'],
            "tasks_count": len(result['tasks']),
            "tasks": result['tasks'],
            "restored_at": datetime.now().isoformat()
        }

# 全局实例
recovery_service = RecoveryService()
```

**参考文档**:
- [ARCHITECTURE_V2.md - Recovery Service](ARCHITECTURE_V2.md#33-recovery-service)
- [TRANSLATION_API.md - 恢复 API](TRANSLATION_API.md#5-恢复-api)

**预计工时**: 3 小时

**依赖**: 5.2

---

### ⚙️ 5.4 Statistics Service 实现

**状态**: ⏳ TODO

**任务目标**:
- 实现统计信息计算
- 实现性能指标收集

**交付物**:
- `services/stats_service.py` - 统计服务

**核心实现**:
```python
class StatsService:
    """统计服务"""

    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        # 会话统计
        sessions_stats = await mysql_connector.get_sessions_stats()

        # 任务统计
        tasks_stats = await mysql_connector.get_tasks_stats()

        # 数据库大小
        db_stats = await mysql_connector.get_database_stats()

        return {
            "sessions": sessions_stats,
            "tasks": tasks_stats,
            "storage": db_stats
        }

# 全局实例
stats_service = StatsService()
```

**参考文档**:
- [TRANSLATION_API.md - 统计信息](TRANSLATION_API.md#63-获取统计信息)

**预计工时**: 2 小时

**依赖**: 5.3

---

### ⚙️ 5.5 Cleanup Service 实现

**状态**: ⏳ TODO

**任务目标**:
- 实现清理过期数据
- 支持 dry-run 模式

**交付物**:
- `services/cleanup_service.py` - 清理服务

**核心实现**:
```python
class CleanupService:
    """数据清理服务"""

    async def cleanup(
        self,
        completed_days: int = 90,
        failed_days: int = 30,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """清理过期数据"""
        # 查找需要清理的会话
        sql = """
            SELECT session_id FROM translation_sessions
            WHERE (status = 'completed' AND created_at < DATE_SUB(NOW(), INTERVAL %s DAY))
               OR (status = 'failed' AND created_at < DATE_SUB(NOW(), INTERVAL %s DAY))
        """
        sessions_to_delete = await mysql_connector.query(sql, (completed_days, failed_days))

        if dry_run:
            # 只计数，不删除
            tasks_count = await mysql_connector.count_tasks_by_sessions(sessions_to_delete)
            return {
                "deleted_sessions": len(sessions_to_delete),
                "deleted_tasks": tasks_count,
                "dry_run": True
            }

        # 实际删除（级联删除任务）
        deleted_tasks = 0
        for session in sessions_to_delete:
            deleted_tasks += await mysql_connector.delete_session(session['session_id'])

        return {
            "deleted_sessions": len(sessions_to_delete),
            "deleted_tasks": deleted_tasks,
            "dry_run": False
        }

# 全局实例
cleanup_service = CleanupService()
```

**参考文档**:
- [TRANSLATION_API.md - 清理过期数据](TRANSLATION_API.md#62-清理过期数据)

**预计工时**: 2 小时

**依赖**: 5.4

---

### ⚙️ 5.6 服务层集成测试

**状态**: ⏳ TODO

**任务目标**:
- 测试 BufferManager 的刷新逻辑
- 测试 QueryService 的查询功能
- 测试 RecoveryService 的恢复功能

**交付物**:
- `tests/unit/test_services.py` - 服务层测试

**测试用例**:
```python
async def test_buffer_manager_flush():
    """测试缓冲管理器刷新"""
    bm = BufferManager(max_buffer_size=10, flush_interval=60)
    sessions = [{"session_id": f"s_{i}", ...} for i in range(5)]
    await bm.add_sessions(sessions)
    assert len(bm.session_buffer) == 5

    tasks = [{"task_id": f"t_{i}", ...} for i in range(10)]
    await bm.add_tasks(tasks)
    # 应该触发刷新（超过 max_buffer_size）
    assert len(bm.task_buffer) == 0

async def test_query_service():
    """测试查询服务"""
    filters = SessionFilters(status="processing")
    pagination = Pagination(page=1, page_size=20)
    result = await query_service.query_sessions(filters, pagination)
    assert result.total >= 0
    assert len(result.items) <= 20
```

**参考文档**:
- pytest-asyncio 文档

**预计工时**: 3 小时

**依赖**: 5.5

---

### ⚙️ 5.7 性能优化

**状态**: ⏳ TODO

**任务目标**:
- 优化批量写入性能
- 优化查询性能（索引使用）
- 添加查询缓存（可选）

**交付物**:
- 优化后的服务代码
- 性能测试报告

**优化点**:
- 批量写入使用事务
- 查询使用覆盖索引
- 添加 Redis 缓存热点数据（可选）

**参考文档**:
- [ARCHITECTURE_V2.md - 性能优化](ARCHITECTURE_V2.md#6-性能优化策略)

**预计工时**: 3 小时

**依赖**: 5.6

---

## 阶段 6: API 层

### 🌐 6.1 批量写入 API

**状态**: ⏳ TODO

**任务目标**:
- 实现 `POST /api/v1/translation/sessions/batch`
- 实现 `POST /api/v1/translation/tasks/batch`
- 实现 `POST /api/v1/translation/flush`

**交付物**:
- `api/v1/translation_api.py` - 翻译 API（批量写入部分）

**核心实现**:
```python
from fastapi import APIRouter, HTTPException
from models.api_models import SessionBatchRequest, TaskBatchRequest, BatchResponse, FlushResponse
from services.buffer_manager import buffer_manager
import logging

router = APIRouter(prefix="/api/v1/translation", tags=["translation"])
logger = logging.getLogger(__name__)

@router.post("/sessions/batch", response_model=BatchResponse)
async def batch_persist_sessions(request: SessionBatchRequest):
    """批量持久化会话"""
    try:
        # 转换为字典列表
        sessions_dict = [s.model_dump(exclude_none=True) for s in request.sessions]

        # 添加到缓冲区
        await buffer_manager.add_sessions(sessions_dict)

        return BatchResponse(
            status="accepted",
            count=len(request.sessions),
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Failed to persist sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tasks/batch", response_model=BatchResponse)
async def batch_persist_tasks(request: TaskBatchRequest):
    """批量持久化任务"""
    try:
        tasks_dict = [t.model_dump(exclude_none=True) for t in request.tasks]
        await buffer_manager.add_tasks(tasks_dict)

        return BatchResponse(
            status="accepted",
            count=len(request.tasks),
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Failed to persist tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/flush", response_model=FlushResponse)
async def force_flush():
    """强制刷新缓冲区"""
    try:
        result = await buffer_manager.flush()
        return FlushResponse(
            status="flushed",
            sessions_written=result['sessions'],
            tasks_written=result['tasks'],
            duration_ms=result['duration_ms']
        )
    except Exception as e:
        logger.error(f"Failed to flush: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**参考文档**:
- [TRANSLATION_API.md - 批量写入 API](TRANSLATION_API.md#3-批量写入-api)

**预计工时**: 3 小时

**依赖**: 5.7

---

### 🌐 6.2 查询 API

**状态**: ⏳ TODO

**任务目标**:
- 实现 `GET /api/v1/translation/sessions`
- 实现 `GET /api/v1/translation/sessions/{id}`
- 实现 `GET /api/v1/translation/sessions/{id}/tasks`
- 实现 `GET /api/v1/translation/tasks/{id}`
- 实现 `GET /api/v1/translation/tasks`

**交付物**:
- `api/v1/translation_api.py` - 翻译 API（查询部分）

**核心实现**:
```python
@router.get("/sessions", response_model=QueryResponse)
async def query_sessions(
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    order: str = "desc"
):
    """查询会话列表"""
    try:
        filters = SessionFilters(
            status=status,
            from_date=datetime.fromisoformat(from_date) if from_date else None,
            to_date=datetime.fromisoformat(to_date) if to_date else None
        )
        pagination = Pagination(
            page=page,
            page_size=min(page_size, 100),
            sort_by=sort_by,
            order=order
        )
        return await query_service.query_sessions(filters, pagination)
    except Exception as e:
        logger.error(f"Failed to query sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """查询单个会话"""
    session = await query_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.get("/sessions/{session_id}/tasks", response_model=QueryResponse)
async def get_session_tasks(
    session_id: str,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """查询会话的任务列表"""
    try:
        filters = TaskFilters(status=status)
        pagination = Pagination(page=page, page_size=min(page_size, 100))
        return await query_service.get_session_tasks(session_id, filters, pagination)
    except Exception as e:
        logger.error(f"Failed to query session tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**参考文档**:
- [TRANSLATION_API.md - 查询 API](TRANSLATION_API.md#4-查询-api)

**预计工时**: 4 小时

**依赖**: 6.1

---

### 🌐 6.3 恢复 API

**状态**: ⏳ TODO

**任务目标**:
- 实现 `GET /api/v1/translation/recovery/incomplete-sessions`
- 实现 `POST /api/v1/translation/recovery/restore/{id}`

**交付物**:
- `api/v1/translation_api.py` - 翻译 API（恢复部分）

**核心实现**:
```python
@router.get("/recovery/incomplete-sessions")
async def get_incomplete_sessions():
    """获取未完成的会话列表"""
    try:
        sessions = await recovery_service.get_incomplete_sessions()
        return {
            "count": len(sessions),
            "sessions": sessions
        }
    except Exception as e:
        logger.error(f"Failed to get incomplete sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recovery/restore/{session_id}")
async def restore_session(session_id: str):
    """恢复指定会话的数据"""
    try:
        result = await recovery_service.restore_session(session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to restore session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**参考文档**:
- [TRANSLATION_API.md - 恢复 API](TRANSLATION_API.md#5-恢复-api)

**预计工时**: 2 小时

**依赖**: 6.2

---

### 🌐 6.4 管理 API

**状态**: ⏳ TODO

**任务目标**:
- 实现 `DELETE /api/v1/translation/sessions/{id}`
- 实现 `POST /api/v1/translation/sessions/cleanup`
- 实现 `GET /api/v1/translation/stats`

**交付物**:
- `api/v1/translation_api.py` - 翻译 API（管理部分）

**核心实现**:
```python
@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        result = await mysql_connector.delete_session(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "status": "deleted",
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/cleanup")
async def cleanup_sessions(
    completed_days: int = 90,
    failed_days: int = 30,
    dry_run: bool = False
):
    """清理过期数据"""
    try:
        result = await cleanup_service.cleanup(completed_days, failed_days, dry_run)
        return result
    except Exception as e:
        logger.error(f"Failed to cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats():
    """获取统计信息"""
    try:
        return await stats_service.get_stats()
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**参考文档**:
- [TRANSLATION_API.md - 管理 API](TRANSLATION_API.md#6-管理-api)

**预计工时**: 2 小时

**依赖**: 6.3

---

### 🌐 6.5 系统 API

**状态**: ⏳ TODO

**任务目标**:
- 实现 `GET /health`
- 实现 `GET /api/v1/system/metrics`

**交付物**:
- `api/v1/system_api.py` - 系统 API

**核心实现**:
```python
from fastapi import APIRouter

router = APIRouter(tags=["system"])

@router.get("/health")
async def health_check():
    """健康检查"""
    db_healthy = await mysql_connector.health_check()
    buffer_stats = buffer_manager.get_stats()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "healthy" if db_healthy else "unhealthy",
        "buffer": buffer_stats,
        "version": "1.0.0"
    }

@router.get("/api/v1/system/metrics")
async def get_metrics():
    """获取性能指标（Prometheus 格式）"""
    # TODO: 实现 Prometheus 指标暴露
    return {
        "message": "Metrics endpoint (Prometheus format)"
    }
```

**参考文档**:
- [TRANSLATION_API.md - 系统 API](TRANSLATION_API.md#7-系统-api)

**预计工时**: 2 小时

**依赖**: 6.4

---

### 🌐 6.6 错误处理

**状态**: ⏳ TODO

**任务目标**:
- 统一错误响应格式
- 实现全局异常处理器
- 添加请求验证错误处理

**交付物**:
- `api/middleware/error_handler.py` - 错误处理中间件

**核心实现**:
```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": f"HTTP_{exc.status_code}"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
    )
```

**参考文档**:
- [TRANSLATION_API.md - 错误码](TRANSLATION_API.md#9-错误码)

**预计工时**: 2 小时

**依赖**: 6.5

---

### 🌐 6.7 API 文档生成

**状态**: ⏳ TODO

**任务目标**:
- 配置 FastAPI 自动文档（Swagger UI）
- 添加 API 描述和示例
- 配置 OpenAPI schema

**交付物**:
- 自动生成的 API 文档（访问 `/docs`）

**配置**:
```python
app = FastAPI(
    title="Persistence Service API",
    description="翻译数据持久化服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
```

**参考文档**:
- FastAPI 官方文档

**预计工时**: 1 小时

**依赖**: 6.6

---

### 🌐 6.8 API 层集成测试

**状态**: ⏳ TODO

**任务目标**:
- 测试所有 API 端点
- 测试请求验证
- 测试错误处理

**交付物**:
- `tests/integration/test_api.py` - API 集成测试

**测试用例**:
```python
from httpx import AsyncClient

async def test_batch_persist_sessions():
    """测试批量写入会话"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/translation/sessions/batch",
            json={
                "sessions": [{
                    "session_id": "test-session",
                    "filename": "test.xlsx",
                    "file_path": "/test.xlsx",
                    "status": "processing",
                    "llm_provider": "openai"
                }]
            }
        )
        assert response.status_code == 200
        assert response.json()['status'] == 'accepted'

async def test_query_sessions():
    """测试查询会话"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/translation/sessions")
        assert response.status_code == 200
        assert 'items' in response.json()
```

**参考文档**:
- httpx 文档
- pytest-asyncio 文档

**预计工时**: 4 小时

**依赖**: 6.7

---

## 阶段 7: 测试

### 🧪 7.1 单元测试完善

**状态**: ⏳ TODO

**任务目标**:
- 补充所有模块的单元测试
- 达到 80%+ 代码覆盖率

**交付物**:
- `tests/unit/` 下的所有测试文件
- 代码覆盖率报告

**测试范围**:
- 数据模型转换
- 存储后端
- 服务层逻辑
- 工具函数

**参考文档**:
- pytest 文档

**预计工时**: 6 小时

**依赖**: 6.8

---

### 🧪 7.2 集成测试完善

**状态**: ⏳ TODO

**任务目标**:
- 端到端测试（API → Service → Database）
- 测试完整的业务流程

**交付物**:
- `tests/integration/test_e2e.py` - 端到端测试

**测试场景**:
```python
async def test_full_workflow():
    """测试完整工作流"""
    # 1. 写入会话
    await client.post("/api/v1/translation/sessions/batch", json={...})

    # 2. 写入任务
    await client.post("/api/v1/translation/tasks/batch", json={...})

    # 3. 强制刷新
    await client.post("/api/v1/translation/flush")

    # 4. 查询会话
    response = await client.get("/api/v1/translation/sessions/{id}")
    assert response.status_code == 200

    # 5. 查询任务
    response = await client.get("/api/v1/translation/sessions/{id}/tasks")
    assert len(response.json()['items']) > 0
```

**参考文档**:
- pytest 文档

**预计工时**: 4 小时

**依赖**: 7.1

---

### 🧪 7.3 性能测试

**状态**: ⏳ TODO

**任务目标**:
- 测试 API 响应时间
- 测试批量写入吞吐量
- 测试查询性能

**交付物**:
- `tests/performance/test_performance.py` - 性能测试
- 性能测试报告

**测试指标**:
- API 响应时间 < 10ms (P95)
- 批量写入吞吐量 > 5000 条/分钟
- 查询响应时间 < 50ms (P95)

**工具**:
- locust 或 pytest-benchmark

**参考文档**:
- [REQUIREMENTS_V2.md - 性能要求](REQUIREMENTS_V2.md)

**预计工时**: 4 小时

**依赖**: 7.2

---

### 🧪 7.4 压力测试

**状态**: ⏳ TODO

**任务目标**:
- 测试系统在高负载下的表现
- 测试并发写入和查询

**交付物**:
- `tests/performance/test_stress.py` - 压力测试
- 压力测试报告

**测试场景**:
- 10 个并发客户端持续写入 1 小时
- 每秒 100 次查询请求
- 缓冲区满载情况

**参考文档**:
- locust 文档

**预计工时**: 3 小时

**依赖**: 7.3

---

### 🧪 7.5 恢复功能测试

**状态**: ⏳ TODO

**任务目标**:
- 测试服务崩溃后的数据恢复
- 测试未完成会话的恢复

**交付物**:
- `tests/integration/test_recovery.py` - 恢复测试

**测试场景**:
```python
async def test_recovery():
    """测试恢复功能"""
    # 1. 创建未完成会话
    # 2. 模拟服务重启
    # 3. 调用恢复接口
    # 4. 验证数据完整性
```

**参考文档**:
- [TRANSLATION_API.md - 恢复 API](TRANSLATION_API.md#5-恢复-api)

**预计工时**: 3 小时

**依赖**: 7.4

---

### 🧪 7.6 数据丢失测试

**状态**: ⏳ TODO

**任务目标**:
- 测试服务崩溃时的数据丢失量
- 验证数据丢失在可接受范围内

**交付物**:
- `tests/integration/test_data_loss.py` - 数据丢失测试

**测试场景**:
- 模拟服务崩溃（缓冲区有数据）
- 统计丢失的数据量
- 验证 ≤ 1000 条或 30 秒

**参考文档**:
- [REQUIREMENTS_V2.md - 可接受的权衡](REQUIREMENTS_V2.md)

**预计工时**: 2 小时

**依赖**: 7.5

---

### 🧪 7.7 测试报告

**状态**: ⏳ TODO

**任务目标**:
- 生成测试覆盖率报告
- 生成性能测试报告
- 编写测试总结文档

**交付物**:
- `tests/reports/coverage_report.html` - 覆盖率报告
- `tests/reports/performance_report.md` - 性能报告
- `tests/reports/test_summary.md` - 测试总结

**工具**:
- pytest-cov
- pytest-html

**参考文档**:
- pytest 文档

**预计工时**: 2 小时

**依赖**: 7.6

---

## 阶段 8: 部署和运维

### 🚀 8.1 部署脚本

**状态**: ⏳ TODO

**任务目标**:
- 编写部署脚本
- 编写启动脚本
- 编写停止脚本

**交付物**:
- `scripts/deploy.sh` - 部署脚本
- `scripts/start.sh` - 启动脚本
- `scripts/stop.sh` - 停止脚本

**脚本内容**:
```bash
#!/bin/bash
# deploy.sh

# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库
mysql -u root -p < database/schema.sql

# 3. 启动服务
uvicorn main:app --host 0.0.0.0 --port 8001
```

**参考文档**:
- [DEPLOYMENT.md](DEPLOYMENT.md)

**预计工时**: 2 小时

**依赖**: 7.7

---

### 🚀 8.2 systemd 服务配置

**状态**: ⏳ TODO

**任务目标**:
- 创建 systemd 服务文件
- 配置自动重启
- 配置日志管理

**交付物**:
- `deployment/persistence-service.service` - systemd 服务文件

**服务文件**:
```ini
[Unit]
Description=Persistence Service
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/persistence_service
Environment="PATH=/opt/persistence_service/venv/bin"
ExecStart=/opt/persistence_service/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**参考文档**:
- [DEPLOYMENT.md - systemd 部署](DEPLOYMENT.md)

**预计工时**: 2 小时

**依赖**: 8.1

---

### 🚀 8.3 监控配置

**状态**: ⏳ TODO

**任务目标**:
- 配置 Prometheus 指标暴露
- 配置 Grafana 仪表盘（可选）
- 配置告警规则（可选）

**交付物**:
- `monitoring/prometheus.yml` - Prometheus 配置
- `monitoring/grafana_dashboard.json` - Grafana 仪表盘（可选）

**指标暴露**:
```python
from prometheus_client import Counter, Histogram, Gauge

api_requests = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method'])
api_duration = Histogram('api_duration_seconds', 'API request duration', ['endpoint'])
buffer_size = Gauge('buffer_size', 'Current buffer size', ['type'])
```

**参考文档**:
- [ARCHITECTURE_V2.md - 监控指标](ARCHITECTURE_V2.md#81-监控指标)

**预计工时**: 3 小时

**依赖**: 8.2

---

### 🚀 8.4 部署文档完善

**状态**: ⏳ TODO

**任务目标**:
- 完善部署文档
- 编写运维手册
- 编写故障排查指南

**交付物**:
- `docs/DEPLOYMENT_GUIDE.md` - 部署指南
- `docs/OPS_MANUAL.md` - 运维手册
- `docs/TROUBLESHOOTING.md` - 故障排查

**文档内容**:
- 详细的部署步骤
- 配置说明
- 常见问题和解决方案

**参考文档**:
- [DEPLOYMENT.md](DEPLOYMENT.md)

**预计工时**: 3 小时

**依赖**: 8.3

---

## 📅 里程碑

### Milestone 1: 基础设施完成（Week 1）
- ✅ 1.1 - 1.6 完成
- 🎯 目标：项目框架搭建完成

### Milestone 2: 数据库和存储层完成（Week 2）
- ⏳ 2.1 - 2.5, 3.1 - 3.4, 4.1 - 4.4 完成
- 🎯 目标：数据持久化能力完成

### Milestone 3: 服务层完成（Week 3）
- ⏳ 5.1 - 5.7 完成
- 🎯 目标：业务逻辑完成

### Milestone 4: API 层完成（Week 3-4）
- ⏳ 6.1 - 6.8 完成
- 🎯 目标：所有 API 可用

### Milestone 5: 测试完成（Week 4）
- ⏳ 7.1 - 7.7 完成
- 🎯 目标：质量保证完成

### Milestone 6: 上线部署（Week 5）
- ⏳ 8.1 - 8.4 完成
- 🎯 目标：生产环境运行

---

## 📊 工时统计

| 阶段 | 任务数 | 预计工时 | 实际工时 |
|------|--------|----------|----------|
| 阶段 1: 基础设施 | 6 | 6 小时 | - |
| 阶段 2: 数据库层 | 5 | 17 小时 | - |
| 阶段 3: 数据模型层 | 4 | 8 小时 | - |
| 阶段 4: 存储抽象层 | 4 | 9 小时 | - |
| 阶段 5: 服务层 | 7 | 23 小时 | - |
| 阶段 6: API 层 | 8 | 20 小时 | - |
| 阶段 7: 测试 | 7 | 24 小时 | - |
| 阶段 8: 部署和运维 | 4 | 10 小时 | - |
| **总计** | **45** | **117 小时** | **-** |

**预计工期**: 5 周（每周 24 小时，约 3 天/周）

---

## 📝 备注

### 任务优先级

- **P0（必须）**：阶段 1-6 的所有任务
- **P1（重要）**：阶段 7 的测试任务
- **P2（可选）**：阶段 8 的部署优化

### 并行任务

以下任务可以并行开发：
- 3.1-3.4（数据模型）与 2.1-2.5（数据库层）
- 6.1-6.4（API 不同模块）

### 风险提示

⚠️ **高风险任务**：
- 5.1 Buffer Manager（核心逻辑复杂）
- 7.3 性能测试（可能需要调优）
- 7.6 数据丢失测试（需要验证设计）

### 文档引用

所有任务的详细规格请参考：
- [REQUIREMENTS_V2.md](REQUIREMENTS_V2.md) - 需求规格
- [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md) - 架构设计
- [TRANSLATION_API.md](TRANSLATION_API.md) - API 规格
- [ROADMAP.md](ROADMAP.md) - 项目路线图

---

**最后更新**: 2025-09-30
**维护者**: Development Team
**下次更新**: 每周更新任务状态