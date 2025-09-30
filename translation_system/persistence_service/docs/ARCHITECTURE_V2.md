# Persistence Service - 完整架构设计文档 V2.0

**文档版本**: v2.0
**创建日期**: 2025-09-30
**更新日期**: 2025-09-30
**架构师**: Architecture Team
**审核状态**: 待评审

---

## 1. 架构愿景

### 1.1 服务定位

Persistence Service 是一个**通用的、可扩展的数据持久化微服务**，提供统一的数据访问层，屏蔽底层存储细节。

**核心理念**：
```
One Service, Multiple Backends, Unified API
(一个服务，多个后端，统一接口)
```

### 1.2 架构目标

| 目标 | 实现方式 | Phase |
|------|----------|-------|
| **存储抽象** | 插件式存储后端架构 | Phase 1 |
| **高性能** | 批量处理 + 缓存策略 | Phase 1 |
| **高可用** | 无状态设计 + 多实例部署 | Phase 2 |
| **可扩展** | 支持动态添加存储类型 | Phase 3 |
| **可观测** | 完整的监控和追踪 | Phase 4 |

## 2. 系统架构全景

### 2.1 整体架构图

```
┌────────────────────────────────────────────────────────────────────┐
│                        Client Applications                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐    │
│  │ Backend V2   │  │  Frontend    │  │   Admin Dashboard    │    │
│  └──────────────┘  └──────────────┘  └──────────────────────┘    │
└────────────────────────────┬───────────────────────────────────────┘
                             │ HTTP/HTTPS + JSON
                             │
┌────────────────────────────▼───────────────────────────────────────┐
│                    API Gateway (Optional)                          │
│                 Load Balancing + Rate Limiting                     │
└────────────────────────────┬───────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Instance #1  │     │ Instance #2  │     │ Instance #3  │
│ (Primary)    │     │ (Secondary)  │     │ (Secondary)  │
└──────────────┘     └──────────────┘     └──────────────┘

       │                    │                    │
       └────────────────────┴────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────────┐
│               Persistence Service Architecture                     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │               API Layer (FastAPI)                            │ │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐ │ │
│  │  │Translation│  │  Storage  │  │   Users   │  │  Admin   │ │ │
│  │  │    API    │  │    API    │  │    API    │  │   API    │ │ │
│  │  └───────────┘  └───────────┘  └───────────┘  └──────────┘ │ │
│  └──────────────────┬────────────────────────────────────────── │ │
│                     │                                             │
│  ┌──────────────────▼───────────────────────────────────────────┐│
│  │            Service Layer (Business Logic)                    ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  ││
│  │  │   Buffer     │  │    Query     │  │    Recovery      │  ││
│  │  │   Manager    │  │   Service    │  │    Service       │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  ││
│  └──────────────────┬───────────────────────────────────────────┘│
│                     │                                             │
│  ┌──────────────────▼───────────────────────────────────────────┐│
│  │       Storage Abstraction Layer (Plugin System)              ││
│  │  ┌────────────────────────────────────────────────────────┐ ││
│  │  │         StorageBackend Interface                       │ ││
│  │  │  - write()  - read()  - query()  - delete()           │ ││
│  │  └────────────────────────────────────────────────────────┘ ││
│  └──────────────────┬───────────────────────────────────────────┘│
└─────────────────────┼────────────────────────────────────────────┘
                      │
      ┌───────────────┼───────────────┬────────────────┐
      │               │               │                │
      ▼               ▼               ▼                ▼
┌──────────┐   ┌──────────┐   ┌──────────┐    ┌──────────────┐
│  MySQL   │   │   OSS    │   │  Redis   │    │Elasticsearch │
│  Plugin  │   │  Plugin  │   │  Plugin  │    │   Plugin     │
└────┬─────┘   └────┬─────┘   └────┬─────┘    └──────┬───────┘
     │              │              │                   │
     ▼              ▼              ▼                   ▼
┌──────────┐   ┌──────────┐   ┌──────────┐    ┌──────────────┐
│  MySQL   │   │Aliyun OSS│   │  Redis   │    │Elasticsearch │
│ Database │   │   / S3   │   │  Cluster │    │   Cluster    │
└──────────┘   └──────────┘   └──────────┘    └──────────────┘
```

### 2.2 分层架构详解

#### Layer 1: API Layer（API 层）

**职责**：
- HTTP 端点暴露
- 请求/响应处理
- 数据验证（Pydantic）
- 认证和授权（未来）

**技术栈**：FastAPI + Pydantic

**模块组织**：
```
api/
├── v1/
│   ├── translation_api.py    # 翻译数据 API
│   ├── storage_api.py         # 文件存储 API
│   ├── users_api.py           # 用户数据 API
│   └── system_api.py          # 系统管理 API
└── middleware/
    ├── auth.py                # 认证中间件
    ├── rate_limit.py          # 限流中间件
    └── logging.py             # 日志中间件
```

#### Layer 2: Service Layer（服务层）

**职责**：
- 业务逻辑处理
- 缓冲区管理
- 查询构建
- 数据恢复逻辑

**核心服务**：

1. **BufferManager**：批量写入缓冲管理
```python
class BufferManager:
    """批量写入缓冲管理器"""
    - 管理内存缓冲区
    - 检查刷新条件
    - 批量触发写入
```

2. **QueryService**：查询服务
```python
class QueryService:
    """查询服务"""
    - 构建查询条件
    - 分页处理
    - 结果聚合
```

3. **RecoveryService**：数据恢复服务
```python
class RecoveryService:
    """数据恢复服务"""
    - 检测未完成会话
    - 恢复会话数据
    - 重建任务队列
```

#### Layer 3: Storage Abstraction Layer（存储抽象层）

**职责**：
- 定义统一的存储接口
- 管理存储后端插件
- 路由数据到正确的存储后端

**接口定义**：
```python
class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    async def write(self, collection: str, data: List[Dict]) -> WriteResult:
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
        pagination: Pagination,
        sort: Optional[Sort] = None
    ) -> QueryResult:
        """查询数据（支持过滤、分页、排序）"""
        pass

    @abstractmethod
    async def delete(self, collection: str, key: str) -> bool:
        """删除数据"""
        pass

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """健康检查"""
        pass
```

#### Layer 4: Storage Plugins（存储插件层）

**插件列表**：

| 插件 | 用途 | Phase | 优先级 |
|------|------|-------|--------|
| **MySQLPlugin** | 结构化数据持久化 | Phase 1 | P0 |
| **OSSPlugin** | 文件对象存储 | Phase 2 | P1 |
| **RedisPlugin** | 缓存和会话存储 | Phase 3 | P1 |
| **ElasticsearchPlugin** | 日志和全文搜索 | Phase 4 | P2 |

## 3. 核心组件设计

### 3.1 Buffer Manager（缓冲管理器）

**架构图**：
```
┌──────────────────────────────────────────────────────────┐
│                    BufferManager                         │
│                                                           │
│  ┌────────────────────┐      ┌────────────────────────┐ │
│  │  session_buffer    │      │   task_buffer          │ │
│  │  List[SessionDict] │      │   List[TaskDict]       │ │
│  │  Max: 1000         │      │   Max: 1000            │ │
│  └────────────────────┘      └────────────────────────┘ │
│                                                           │
│  Flush Conditions:                                        │
│  - Size >= max_buffer_size (1000)                        │
│  - Time >= flush_interval (30s)                          │
│  - Manual flush() call                                    │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐│
│  │              Flush Strategy                          ││
│  │  1. Copy buffer (atomic snapshot)                   ││
│  │  2. Trigger storage backend write                   ││
│  │  3. Wait for completion                             ││
│  │  4. Clear buffer on success                         ││
│  │  5. Log error on failure (discard batch)            ││
│  └─────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

**关键方法**：
```python
class BufferManager:
    async def add_sessions(self, sessions: List[Dict]):
        """添加会话到缓冲区"""
        self.session_buffer.extend(sessions)
        await self._check_and_flush()

    async def add_tasks(self, tasks: List[Dict]):
        """添加任务到缓冲区"""
        self.task_buffer.extend(tasks)
        await self._check_and_flush()

    async def flush(self) -> FlushResult:
        """强制刷新缓冲区"""
        # 1. 获取快照
        sessions_snapshot = self.session_buffer.copy()
        tasks_snapshot = self.task_buffer.copy()

        # 2. 写入存储
        try:
            result = await storage.write_batch(
                sessions_snapshot,
                tasks_snapshot
            )

            # 3. 清空缓冲区
            self.session_buffer.clear()
            self.task_buffer.clear()

            return result
        except Exception as e:
            logger.error(f"Flush failed: {e}")
            # 可接受数据丢失
            self.session_buffer.clear()
            self.task_buffer.clear()
            raise

    async def start_periodic_flush(self):
        """后台定期刷新任务"""
        while True:
            await asyncio.sleep(self.flush_interval)
            if self._has_data():
                await self.flush()
```

### 3.2 Query Service（查询服务）

**架构图**：
```
┌────────────────────────────────────────────────────────────┐
│                      QueryService                          │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │          Query Builder                               │ │
│  │  - Parse filters                                     │ │
│  │  - Build WHERE clauses                               │ │
│  │  - Add pagination (LIMIT/OFFSET)                     │ │
│  │  - Add sorting (ORDER BY)                            │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │          Query Executor                              │ │
│  │  - Route to correct storage backend                 │ │
│  │  - Execute query                                     │ │
│  │  - Transform results                                 │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │          Query Cache (Optional)                      │ │
│  │  - Cache frequent queries                            │ │
│  │  - TTL management                                    │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

**查询示例**：
```python
class QueryService:
    async def query_sessions(
        self,
        filters: SessionFilters,
        pagination: Pagination
    ) -> QueryResult:
        """查询会话列表"""
        # 1. 构建查询
        query = QueryBuilder()
        query.from_table("translation_sessions")

        # 2. 添加过滤条件
        if filters.status:
            query.where("status", "=", filters.status)
        if filters.from_date:
            query.where("created_at", ">=", filters.from_date)

        # 3. 添加分页和排序
        query.limit(pagination.page_size)
        query.offset((pagination.page - 1) * pagination.page_size)
        query.order_by(filters.sort_by, filters.order)

        # 4. 执行查询
        backend = self.get_backend("translation_sessions")
        result = await backend.query(query.build())

        return result

    async def get_session_detail(self, session_id: str) -> Optional[Session]:
        """获取会话详情"""
        backend = self.get_backend("translation_sessions")
        session_data = await backend.read("translation_sessions", session_id)

        if not session_data:
            return None

        # 同时查询该会话的任务统计
        stats = await self._get_session_stats(session_id)

        return Session(**session_data, **stats)
```

### 3.3 Recovery Service（恢复服务）

**恢复流程**：
```
1. Backend V2 启动
   ↓
2. 调用 RecoveryService.get_incomplete_sessions()
   ↓
3. RecoveryService 查询数据库：
   SELECT * FROM translation_sessions
   WHERE status IN ('processing', 'pending')
   ↓
4. 对每个未完成会话：
   - 查询所有未完成任务
   - 构建恢复数据包
   - 返回给客户端
   ↓
5. Backend V2 重建内存状态：
   - 创建 TaskDataFrame
   - 加载任务数据
   - 注册到 SessionManager
   ↓
6. 继续执行翻译
```

**关键方法**：
```python
class RecoveryService:
    async def get_incomplete_sessions(self) -> List[SessionSummary]:
        """获取所有未完成的会话"""
        query = QueryBuilder()
        query.from_table("translation_sessions")
        query.where("status", "IN", ["processing", "pending"])
        query.order_by("created_at", "DESC")

        backend = self.get_backend("translation_sessions")
        result = await backend.query(query.build())

        return [SessionSummary(**item) for item in result.items]

    async def restore_session(self, session_id: str) -> RestoredSession:
        """恢复指定会话的完整数据"""
        # 1. 获取会话信息
        session = await self.query_service.get_session_detail(session_id)
        if not session:
            raise SessionNotFoundError(session_id)

        # 2. 获取所有未完成任务
        tasks_query = QueryBuilder()
        tasks_query.from_table("translation_tasks")
        tasks_query.where("session_id", "=", session_id)
        tasks_query.where("status", "IN", ["pending", "processing"])

        backend = self.get_backend("translation_tasks")
        tasks_result = await backend.query(tasks_query.build())

        # 3. 构建恢复数据包
        return RestoredSession(
            session=session,
            tasks=tasks_result.items,
            restored_at=datetime.now()
        )
```

### 3.4 Storage Backend Plugin System（存储后端插件系统）

**插件注册机制**：
```python
class StorageBackendRegistry:
    """存储后端注册表"""

    _backends: Dict[str, StorageBackend] = {}
    _routing_rules: Dict[str, str] = {}

    @classmethod
    def register(cls, name: str, backend: StorageBackend):
        """注册存储后端"""
        cls._backends[name] = backend
        logger.info(f"Registered storage backend: {name}")

    @classmethod
    def register_collection(cls, collection: str, backend_name: str):
        """注册数据集合到存储后端的路由规则"""
        cls._routing_rules[collection] = backend_name

    @classmethod
    def get_backend(cls, collection: str) -> StorageBackend:
        """根据数据集合获取存储后端"""
        backend_name = cls._routing_rules.get(collection)
        if not backend_name:
            raise UnknownCollectionError(collection)

        backend = cls._backends.get(backend_name)
        if not backend:
            raise BackendNotFoundError(backend_name)

        return backend

# 使用示例
# 初始化时注册后端
mysql_backend = MySQLPlugin(config)
StorageBackendRegistry.register("mysql", mysql_backend)

# 注册路由规则
StorageBackendRegistry.register_collection("translation_sessions", "mysql")
StorageBackendRegistry.register_collection("translation_tasks", "mysql")

# 使用时自动路由
backend = StorageBackendRegistry.get_backend("translation_sessions")
await backend.write("translation_sessions", data)
```

## 4. 存储插件详细设计

### 4.1 MySQL Plugin

**实现要点**：
```python
class MySQLPlugin(StorageBackend):
    """MySQL 存储后端插件"""

    async def write(self, collection: str, data: List[Dict]) -> WriteResult:
        """批量写入"""
        # 使用 INSERT ... ON DUPLICATE KEY UPDATE
        # 保证幂等性
        pass

    async def query(
        self,
        collection: str,
        filters: Dict,
        pagination: Pagination
    ) -> QueryResult:
        """查询数据"""
        # 构建 SQL SELECT 语句
        # 支持复杂过滤和分页
        pass

    async def health_check(self) -> HealthStatus:
        """健康检查"""
        try:
            async with self.pool.acquire() as conn:
                await conn.ping()
            return HealthStatus.healthy()
        except Exception as e:
            return HealthStatus.unhealthy(str(e))
```

**表映射**：
| Collection | MySQL Table |
|-----------|-------------|
| translation_sessions | translation_sessions |
| translation_tasks | translation_tasks |

### 4.2 OSS Plugin（Phase 2）

**实现要点**：
```python
class OSSPlugin(StorageBackend):
    """OSS 对象存储插件"""

    async def write(self, collection: str, data: List[Dict]) -> WriteResult:
        """上传文件到 OSS"""
        # collection = "files"
        # data = [{"file_id": "xxx", "content": bytes, "metadata": {...}}]
        for item in data:
            file_id = item['file_id']
            content = item['content']
            key = f"files/{file_id}"
            await self.client.put_object(key, content)
        pass

    async def read(self, collection: str, key: str) -> Optional[Dict]:
        """从 OSS 下载文件"""
        object_key = f"{collection}/{key}"
        content = await self.client.get_object(object_key)
        return {"content": content, "metadata": {...}}

    async def delete(self, collection: str, key: str) -> bool:
        """从 OSS 删除文件"""
        object_key = f"{collection}/{key}"
        await self.client.delete_object(object_key)
        return True
```

### 4.3 Redis Plugin（Phase 3）

**实现要点**：
```python
class RedisPlugin(StorageBackend):
    """Redis 缓存插件"""

    async def write(self, collection: str, data: List[Dict]) -> WriteResult:
        """批量写入 Redis"""
        # 使用 pipeline 批量写入
        async with self.client.pipeline() as pipe:
            for item in data:
                key = f"{collection}:{item['id']}"
                await pipe.setex(
                    key,
                    self.ttl,  # TTL
                    json.dumps(item)
                )
            await pipe.execute()

    async def read(self, collection: str, key: str) -> Optional[Dict]:
        """从 Redis 读取"""
        redis_key = f"{collection}:{key}"
        value = await self.client.get(redis_key)
        return json.loads(value) if value else None
```

## 5. 数据流详解

### 5.1 写入流程（批量）

```
时间线（详细）：

T0: 客户端累积 100 条任务数据
    └─> 本地缓冲区达到阈值

T1 (0ms): 发送 HTTP POST 请求
    └─> URL: /api/v1/translation/tasks/batch
    └─> Body: {"tasks": [...100 items...]}

T2 (2ms): API Layer 接收请求
    └─> Pydantic 验证数据格式
    └─> 验证通过

T3 (3ms): Service Layer 处理
    └─> BufferManager.add_tasks(tasks)
    └─> 添加到内存缓冲区
    └─> 当前缓冲区大小：900 → 1000

T4 (4ms): 立即返回响应
    └─> HTTP 202 Accepted
    └─> {"status": "accepted", "count": 100}

T5 (5ms): 检查刷新条件
    └─> 缓冲区大小 >= 1000 ✓
    └─> 触发刷新

T6 (6ms): 后台刷新开始
    └─> 复制缓冲区快照（1000 条）
    └─> 调用 storage.write_batch()

T7 (806ms): MySQL 批量写入完成
    └─> INSERT ... ON DUPLICATE KEY UPDATE
    └─> 1000 rows affected

T8 (807ms): 清空缓冲区
    └─> session_buffer.clear()
    └─> task_buffer.clear()

客户端视角响应时间：4ms
实际数据库写入延迟：807ms（异步，不阻塞客户端）
```

### 5.2 查询流程

```
时间线（查询会话列表）：

T0: 客户端请求
    └─> GET /api/v1/translation/sessions?status=processing&page=1

T1 (5ms): API Layer 接收请求
    └─> 解析查询参数
    └─> filters = {status: "processing"}
    └─> pagination = {page: 1, page_size: 20}

T2 (10ms): Service Layer 处理
    └─> QueryService.query_sessions(filters, pagination)
    └─> 构建查询条件

T3 (15ms): Storage Layer 执行查询
    └─> MySQLPlugin.query()
    └─> SQL: SELECT * FROM translation_sessions
             WHERE status = 'processing'
             LIMIT 20 OFFSET 0
             ORDER BY created_at DESC

T4 (45ms): MySQL 返回结果
    └─> 20 rows returned

T5 (46ms): 结果转换
    └─> 转换为 SessionSummary 对象列表

T6 (47ms): 返回响应
    └─> HTTP 200 OK
    └─> {
          "total": 150,
          "page": 1,
          "page_size": 20,
          "items": [...]
        }

总响应时间：47ms
```

### 5.3 恢复流程

```
场景：Backend V2 重启后恢复

T0: Backend V2 启动
    └─> 检测到需要恢复

T1 (100ms): 请求未完成会话列表
    └─> GET /api/v1/translation/recovery/incomplete-sessions

T2 (150ms): Persistence Service 查询数据库
    └─> SELECT * FROM translation_sessions
        WHERE status IN ('processing', 'pending')
    └─> 返回 3 个未完成会话

T3 (200ms): 对每个会话请求恢复
    └─> POST /api/v1/translation/recovery/restore/{session_id}

T4 (500ms): 查询会话详情 + 所有未完成任务
    └─> SELECT * FROM translation_sessions WHERE session_id = ?
    └─> SELECT * FROM translation_tasks
        WHERE session_id = ? AND status IN ('pending', 'processing')
    └─> 返回会话 + 640 个任务

T5 (600ms): Backend V2 重建内存状态
    └─> 创建 TaskDataFrameManager
    └─> 加载任务到 DataFrame
    └─> 注册到 SessionManager

T6: 恢复完成，继续翻译
    └─> WorkerPool 继续执行未完成任务

总恢复时间：600ms × 3 sessions = 1.8秒
```

## 6. 性能优化策略

### 6.1 批量处理优化

**批量大小动态调整**：
```python
class AdaptiveBufferManager(BufferManager):
    """自适应缓冲管理器"""

    def __init__(self):
        self.min_buffer_size = 500
        self.max_buffer_size = 5000
        self.current_buffer_size = 1000

    async def adjust_buffer_size(self):
        """根据负载动态调整缓冲区大小"""
        avg_flush_time = self._get_avg_flush_time()

        if avg_flush_time > 2000:  # 2秒
            # 刷新太慢，减小批次
            self.current_buffer_size = max(
                self.min_buffer_size,
                self.current_buffer_size - 100
            )
        elif avg_flush_time < 500:  # 0.5秒
            # 刷新很快，增大批次
            self.current_buffer_size = min(
                self.max_buffer_size,
                self.current_buffer_size + 100
            )
```

### 6.2 查询缓存策略

**多级缓存**：
```
Level 1: Application Cache (Dict)
  └─> TTL: 10秒
  └─> 用于：频繁查询的会话详情

Level 2: Redis Cache
  └─> TTL: 60秒
  └─> 用于：会话列表、统计数据

Level 3: MySQL Database
  └─> 持久化存储
  └─> 用于：所有数据
```

**缓存更新策略**：
- 写入时：失效相关缓存（Cache Aside）
- 查询时：查不到则加载并缓存
- 定期：清理过期缓存

### 6.3 数据库优化

**连接池调优**：
```python
pool_config = {
    'minsize': 10,              # 最小连接数
    'maxsize': 50,              # 最大连接数（支持更高并发）
    'pool_recycle': 3600,       # 1小时回收
    'max_overflow': 10,         # 超出最大值时可额外创建
    'timeout': 30               # 获取连接超时
}
```

**索引设计**：
```sql
-- 会话表索引
CREATE INDEX idx_status_created ON translation_sessions(status, created_at);
CREATE INDEX idx_updated_at ON translation_sessions(updated_at);

-- 任务表索引
CREATE INDEX idx_session_status ON translation_tasks(session_id, status);
CREATE INDEX idx_batch_id ON translation_tasks(batch_id);
CREATE INDEX idx_status_updated ON translation_tasks(status, updated_at);
```

**查询优化**：
- 使用 EXPLAIN 分析查询计划
- 避免 SELECT *，只查询需要的字段
- 使用覆盖索引减少回表

## 7. 可扩展性设计

### 7.1 水平扩展

**无状态架构**：
- 所有实例完全相同
- 不共享内存状态
- 缓冲区独立

**部署模式**：
```
Round-Robin Load Balancing:

Request 1 → Instance 1 (Buffer: 150 items)
Request 2 → Instance 2 (Buffer: 220 items)
Request 3 → Instance 3 (Buffer: 80 items)
Request 4 → Instance 1 (Buffer: 250 items)
...

每个实例独立刷新缓冲区，互不影响
```

### 7.2 存储后端扩展

**添加新的存储后端步骤**：
1. 实现 `StorageBackend` 接口
2. 注册到 `StorageBackendRegistry`
3. 配置路由规则
4. 无需修改业务逻辑代码

**示例：添加 PostgreSQL 支持**：
```python
# 1. 实现插件
class PostgreSQLPlugin(StorageBackend):
    async def write(self, collection, data):
        # PostgreSQL 实现
        pass

# 2. 注册
pg_backend = PostgreSQLPlugin(config)
StorageBackendRegistry.register("postgresql", pg_backend)

# 3. 配置路由
StorageBackendRegistry.register_collection("analytics_data", "postgresql")

# 完成！可以直接使用
```

### 7.3 API 版本管理

**版本控制策略**：
```
/api/v1/...  当前版本（稳定）
/api/v2/...  下一版本（开发中）
```

**向后兼容原则**：
- 只添加字段，不删除字段
- 标记过时字段为 deprecated
- 提供迁移指南

## 8. 监控和可观测性

### 8.1 监控指标

**关键指标（Prometheus 格式）**：
```python
# 请求指标
persistence_api_requests_total{endpoint="/api/v1/translation/sessions/batch", method="POST"}
persistence_api_duration_seconds{endpoint="/api/v1/translation/sessions/batch", method="POST"}

# 缓冲区指标
persistence_buffer_size{type="session"}
persistence_buffer_size{type="task"}
persistence_flush_total
persistence_flush_duration_seconds

# 存储后端指标
persistence_storage_operations_total{backend="mysql", operation="write"}
persistence_storage_duration_seconds{backend="mysql", operation="write"}
persistence_storage_errors_total{backend="mysql", operation="write"}

# 业务指标
persistence_sessions_total{status="completed"}
persistence_tasks_total{status="completed"}
persistence_data_loss_total
```

### 8.2 日志记录

**结构化日志**：
```json
{
  "timestamp": "2025-09-30T10:15:30.123Z",
  "level": "INFO",
  "service": "persistence-service",
  "instance": "instance-1",
  "endpoint": "/api/v1/translation/tasks/batch",
  "method": "POST",
  "request_id": "req-123",
  "user_id": "user-456",
  "session_id": "session-789",
  "message": "Batch write accepted",
  "meta": {
    "count": 100,
    "buffer_size": 1000
  }
}
```

### 8.3 分布式追踪

**OpenTelemetry 集成**：
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@router.post("/api/v1/translation/tasks/batch")
async def batch_persist_tasks(request: TaskBatchRequest):
    with tracer.start_as_current_span("batch_persist_tasks") as span:
        span.set_attribute("task_count", len(request.tasks))

        # 业务逻辑
        await buffer_manager.add_tasks(request.tasks)

        span.set_attribute("buffer_size", buffer_manager.get_size())
        return {"status": "accepted"}
```

## 9. 安全设计

### 9.1 认证和授权（Phase 2）

**API Key 认证**：
```http
POST /api/v1/translation/tasks/batch
Headers:
  X-API-Key: your-api-key-here
  Content-Type: application/json
```

**JWT 令牌认证**：
```http
POST /api/v1/translation/tasks/batch
Headers:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  Content-Type: application/json
```

### 9.2 限流策略

**基于 IP 的限流**：
- 单个 IP：100 请求/分钟
- 单个 API Key：1000 请求/分钟

**基于资源的限流**：
- 单个会话的查询：10 次/分钟
- 批量写入：不限制（已有缓冲区保护）

### 9.3 数据加密

**传输加密**：
- 生产环境强制 HTTPS/TLS 1.3

**存储加密（可选）**：
- 敏感字段加密（如用户密码）
- 数据库透明加密（TDE）

## 10. 部署和运维

### 10.1 部署策略

**滚动更新**：
```
1. 部署新版本实例（standby）
2. 健康检查通过
3. 将流量切换到新实例
4. 旧实例刷新缓冲区
5. 关闭旧实例
6. 重复直到所有实例更新
```

### 10.2 备份和恢复

**数据库备份**：
- 全量备份：每天凌晨 2:00
- 增量备份：每小时
- 保留期：30 天

**恢复演练**：
- 每月一次恢复演练
- 验证 RTO/RPO 指标

### 10.3 容量规划

**当前容量**：
- 单实例：5000 条/分钟
- 3 实例集群：15000 条/分钟
- 数据库：1000万 行无压力

**扩容触发条件**：
- CPU 使用率 > 70% 持续 10 分钟
- 内存使用率 > 80%
- API 响应时间 P95 > 100ms

---

## 附录

### A. 技术栈总结

| 层次 | 技术 | 版本 | 用途 |
|------|------|------|------|
| Web 框架 | FastAPI | 0.104+ | API 层 |
| ASGI Server | Uvicorn | 0.24+ | HTTP 服务器 |
| 数据验证 | Pydantic | 2.5+ | 数据模型 |
| MySQL 驱动 | aiomysql | 0.2.0 | MySQL 连接 |
| OSS SDK | oss2 | 2.18+ | 阿里云 OSS |
| Redis 客户端 | aioredis | 2.0+ | Redis 连接 |
| 监控 | Prometheus Client | 0.19+ | 指标暴露 |
| 追踪 | OpenTelemetry | 1.20+ | 分布式追踪 |

### B. 关键代码骨架

见代码实现文档

### C. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2025-09-30 | 初始架构（仅批量写入） | Architecture Team |
| v2.0 | 2025-09-30 | 完整架构（查询、恢复、多后端） | Architecture Team |