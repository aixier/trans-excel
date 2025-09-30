# Persistence Service - 完整需求文档 V2.0

**文档版本**: v2.0
**创建日期**: 2025-09-30
**更新日期**: 2025-09-30
**产品经理**: Product Team
**目标用户**: Translation System + 未来扩展系统

---

## 1. 项目定位

### 1.1 服务定位

**Persistence Service** 是一个**通用的数据持久化微服务**，不仅服务于翻译系统，还可以扩展到：

| 业务域 | 数据类型 | 存储后端 | 优先级 |
|--------|----------|----------|--------|
| **翻译系统** | 会话、任务、进度 | MySQL | P0（当前） |
| **文件存储** | 上传文件、翻译结果 | OSS/S3 | P1（未来） |
| **用户系统** | 用户信息、偏好设置 | MySQL/Redis | P2（未来） |
| **审计日志** | 操作日志、访问记录 | Elasticsearch | P3（未来） |
| **缓存层** | 热数据、会话状态 | Redis | P2（未来） |

### 1.2 核心价值

1. **统一持久化入口**：所有数据持久化操作通过统一服务
2. **存储抽象**：业务系统无需关心底层存储实现（MySQL/OSS/Redis）
3. **性能优化**：批量处理、缓存策略、连接池管理
4. **监控可观测**：统一的数据持久化监控和告警
5. **易于扩展**：插件式架构，轻松添加新的存储后端

## 2. 完整功能需求

### 2.1 Phase 1: 翻译数据持久化（当前）

#### F1.1: 批量写入（Write API）

**需求描述**：批量创建或更新翻译数据

**端点设计**：
```
POST /api/v1/translation/sessions/batch    # 批量写入会话
POST /api/v1/translation/tasks/batch       # 批量写入任务
POST /api/v1/translation/flush             # 强制刷新缓冲区
```

**特性**：
- ✅ 批量处理（1000 条/批）
- ✅ 异步非阻塞（Fire-and-Forget）
- ✅ 幂等性保证
- ✅ 自动缓冲管理

#### F1.2: 数据查询（Query API）

**需求描述**：查询历史数据，用于恢复、统计、展示

**端点设计**：
```
GET /api/v1/translation/sessions/{session_id}              # 查询单个会话
GET /api/v1/translation/sessions                           # 查询会话列表（分页）
GET /api/v1/translation/sessions/{session_id}/tasks       # 查询会话的所有任务
GET /api/v1/translation/tasks/{task_id}                    # 查询单个任务
GET /api/v1/translation/tasks                              # 查询任务列表（分页、过滤）
```

**查询参数示例**：
```
GET /api/v1/translation/sessions?status=completed&page=1&page_size=20
GET /api/v1/translation/tasks?session_id=xxx&status=failed&from_date=2025-09-01
```

**使用场景**：
1. **恢复场景**：服务重启后，从数据库恢复未完成的会话和任务
2. **进度查询**：前端实时查询翻译进度
3. **历史记录**：用户查看历史翻译记录
4. **数据分析**：统计翻译质量、成功率等

#### F1.3: 数据管理（Management API）

**需求描述**：管理持久化数据的生命周期

**端点设计**：
```
DELETE /api/v1/translation/sessions/{session_id}          # 删除会话（级联删除任务）
DELETE /api/v1/translation/sessions/cleanup               # 清理过期数据
PATCH  /api/v1/translation/sessions/{session_id}/status   # 更新会话状态
GET    /api/v1/translation/stats                          # 获取统计信息
```

**业务规则**：
- 已完成会话保留 90 天后自动清理
- 失败会话保留 30 天后自动清理
- 支持手动删除（用户主动清理）
- 删除操作可配置软删除（标记）或硬删除（物理删除）

#### F1.4: 数据恢复（Recovery API）

**需求描述**：系统崩溃或重启后，恢复未完成的翻译任务

**端点设计**：
```
GET  /api/v1/translation/recovery/incomplete-sessions     # 获取所有未完成的会话
POST /api/v1/translation/recovery/restore/{session_id}    # 恢复指定会话到内存
GET  /api/v1/translation/recovery/status                  # 获取恢复状态
```

**恢复流程**：
```
1. Backend V2 重启
   ↓
2. 调用 /recovery/incomplete-sessions 获取未完成会话列表
   ↓
3. 对每个会话调用 /recovery/restore 恢复到内存（DataFrame）
   ↓
4. 继续执行未完成的翻译任务
```

### 2.2 Phase 2: 文件存储持久化（未来）

#### F2.1: 文件上传（Upload API）

**需求描述**：上传文件到对象存储（OSS/S3/MinIO）

**端点设计**：
```
POST /api/v1/storage/files/upload              # 上传文件（multipart/form-data）
POST /api/v1/storage/files/upload-url          # 获取预签名上传 URL
GET  /api/v1/storage/files/{file_id}           # 获取文件元数据
GET  /api/v1/storage/files/{file_id}/download  # 下载文件或获取下载 URL
DELETE /api/v1/storage/files/{file_id}         # 删除文件
```

**功能特性**：
- 支持大文件上传（分片上传）
- 支持预签名 URL（客户端直传）
- 自动生成唯一文件 ID
- 记录文件元数据（名称、大小、类型、上传时间）

**存储后端**：
- 阿里云 OSS
- AWS S3
- MinIO（私有部署）

#### F2.2: 文件管理（File Management API）

```
GET  /api/v1/storage/files                     # 查询文件列表（分页）
POST /api/v1/storage/files/batch-delete        # 批量删除文件
GET  /api/v1/storage/files/stats               # 文件存储统计
POST /api/v1/storage/files/cleanup             # 清理过期文件
```

**清理策略**：
- 临时文件（uploaded）：7 天后自动删除
- 已使用文件（processed）：90 天后自动删除
- 归档文件（archived）：永久保留

### 2.3 Phase 3: 用户数据持久化（未来）

#### F3.1: 用户信息管理（User API）

**需求描述**：持久化用户信息、偏好设置

**端点设计**：
```
POST   /api/v1/users                           # 创建用户
GET    /api/v1/users/{user_id}                 # 获取用户信息
PATCH  /api/v1/users/{user_id}                 # 更新用户信息
DELETE /api/v1/users/{user_id}                 # 删除用户
```

**数据类型**：
- 用户基本信息（ID、用户名、邮箱）
- 用户偏好设置（语言、主题、通知设置）
- 用户配额（翻译次数、存储空间）

**存储策略**：
- 热数据（当前登录用户）：Redis 缓存
- 冷数据（历史数据）：MySQL 持久化

#### F3.2: 用户会话管理（Session API）

```
POST   /api/v1/users/sessions                  # 创建用户会话（登录）
GET    /api/v1/users/sessions/{session_token}  # 验证会话
DELETE /api/v1/users/sessions/{session_token}  # 删除会话（登出）
```

**存储后端**：Redis（TTL 自动过期）

### 2.4 Phase 4: 审计日志持久化（未来）

#### F4.1: 审计日志写入（Audit API）

**需求描述**：记录所有关键操作的审计日志

**端点设计**：
```
POST /api/v1/audit/logs/batch                  # 批量写入审计日志
GET  /api/v1/audit/logs                        # 查询审计日志（分页、过滤）
GET  /api/v1/audit/logs/export                 # 导出审计日志
```

**日志内容**：
- 操作时间、操作人、操作类型
- 操作对象（资源 ID、资源类型）
- 操作结果（成功/失败）
- IP 地址、User-Agent

**存储后端**：Elasticsearch（支持全文搜索）

## 3. 完整 API 体系设计

### 3.1 API 版本和命名空间

```
/api/v1/
├── translation/          # 翻译数据持久化（Phase 1）
│   ├── sessions/
│   ├── tasks/
│   ├── recovery/
│   └── stats/
├── storage/              # 文件存储持久化（Phase 2）
│   └── files/
├── users/                # 用户数据持久化（Phase 3）
│   ├── users/
│   └── sessions/
├── audit/                # 审计日志持久化（Phase 4）
│   └── logs/
└── system/               # 系统管理接口
    ├── health
    ├── metrics
    └── config
```

### 3.2 API 端点完整列表（Phase 1 核心功能）

| 分类 | 端点 | 方法 | 功能 | 优先级 |
|------|------|------|------|--------|
| **写入** | `/api/v1/translation/sessions/batch` | POST | 批量写入会话 | P0 |
| **写入** | `/api/v1/translation/tasks/batch` | POST | 批量写入任务 | P0 |
| **写入** | `/api/v1/translation/flush` | POST | 强制刷新缓冲区 | P0 |
| **查询** | `/api/v1/translation/sessions/{id}` | GET | 查询单个会话 | P0 |
| **查询** | `/api/v1/translation/sessions` | GET | 查询会话列表 | P1 |
| **查询** | `/api/v1/translation/sessions/{id}/tasks` | GET | 查询会话任务 | P0 |
| **查询** | `/api/v1/translation/tasks/{id}` | GET | 查询单个任务 | P1 |
| **查询** | `/api/v1/translation/tasks` | GET | 查询任务列表 | P1 |
| **管理** | `/api/v1/translation/sessions/{id}` | DELETE | 删除会话 | P1 |
| **管理** | `/api/v1/translation/sessions/cleanup` | POST | 清理过期数据 | P2 |
| **管理** | `/api/v1/translation/stats` | GET | 统计信息 | P2 |
| **恢复** | `/api/v1/translation/recovery/incomplete-sessions` | GET | 未完成会话列表 | P0 |
| **恢复** | `/api/v1/translation/recovery/restore/{id}` | POST | 恢复会话数据 | P0 |
| **系统** | `/health` | GET | 健康检查 | P0 |
| **系统** | `/api/v1/system/metrics` | GET | 性能指标 | P1 |
| **系统** | `/api/v1/system/config` | GET | 配置信息 | P2 |

### 3.3 查询接口详细设计

#### 查询会话列表

```http
GET /api/v1/translation/sessions?status=processing&page=1&page_size=20

Response:
{
  "total": 150,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "session_id": "xxx-xxx-xxx",
      "filename": "game.xlsx",
      "status": "processing",
      "total_tasks": 1000,
      "completed_tasks": 350,
      "progress": 35.0,
      "created_at": "2025-09-30T10:00:00Z",
      "updated_at": "2025-09-30T10:05:00Z"
    },
    ...
  ]
}
```

**查询参数**：
- `status`: 过滤状态（pending/processing/completed/failed）
- `from_date`: 起始日期
- `to_date`: 结束日期
- `page`: 页码（默认 1）
- `page_size`: 每页大小（默认 20，最大 100）
- `sort_by`: 排序字段（created_at/updated_at）
- `order`: 排序方向（asc/desc）

#### 查询会话详情

```http
GET /api/v1/translation/sessions/{session_id}

Response:
{
  "session_id": "xxx-xxx-xxx",
  "filename": "game.xlsx",
  "file_path": "/uploads/game.xlsx",
  "status": "processing",
  "game_info": {
    "game_name": "Fantasy RPG",
    "source_language": "en",
    "target_language": "zh"
  },
  "llm_provider": "openai",
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

#### 查询会话的所有任务

```http
GET /api/v1/translation/sessions/{session_id}/tasks?status=failed&page=1

Response:
{
  "session_id": "xxx-xxx-xxx",
  "total": 5,
  "page": 1,
  "page_size": 20,
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
      "created_at": "2025-09-30T10:01:00Z",
      "updated_at": "2025-09-30T10:03:00Z"
    },
    ...
  ]
}
```

### 3.4 恢复接口详细设计

#### 获取未完成会话

```http
GET /api/v1/translation/recovery/incomplete-sessions

Response:
{
  "count": 3,
  "sessions": [
    {
      "session_id": "xxx-xxx-xxx",
      "filename": "game.xlsx",
      "status": "processing",
      "total_tasks": 1000,
      "completed_tasks": 350,
      "pending_tasks": 640,
      "created_at": "2025-09-30T10:00:00Z"
    },
    ...
  ]
}
```

#### 恢复会话数据

```http
POST /api/v1/translation/recovery/restore/{session_id}

Response:
{
  "session_id": "xxx-xxx-xxx",
  "restored_session": {...},
  "restored_tasks_count": 640,
  "tasks": [
    {
      "task_id": "task_351",
      "status": "pending",
      "source_text": "...",
      ...
    },
    ...
  ]
}
```

**使用场景**：
```python
# Backend V2 启动时
async def restore_incomplete_sessions():
    # 1. 获取未完成会话列表
    response = await client.get("/api/v1/translation/recovery/incomplete-sessions")
    sessions = response.json()['sessions']

    # 2. 恢复每个会话
    for session in sessions:
        restore_response = await client.post(
            f"/api/v1/translation/recovery/restore/{session['session_id']}"
        )
        session_data = restore_response.json()

        # 3. 重建 TaskDataFrame
        task_manager = TaskDataFrameManager()
        task_manager.load_from_dict(session_data)

        # 4. 注册到 session_manager
        session_manager.register(session['session_id'], task_manager)

        logger.info(f"Restored session {session['session_id']} with {session_data['restored_tasks_count']} tasks")
```

## 4. 存储抽象层设计

### 4.1 存储后端插件架构

```
┌────────────────────────────────────────────────┐
│           Persistence Service API              │
└──────────────────┬─────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────┐
│          Storage Abstraction Layer             │
│  (统一的存储接口定义)                           │
└─────┬────────────┬────────────┬────────────────┘
      │            │            │
      ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│  MySQL   │ │   OSS    │ │  Redis   │ ...
│  Plugin  │ │  Plugin  │ │  Plugin  │
└──────────┘ └──────────┘ └──────────┘
```

### 4.2 存储接口定义

```python
class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    async def write(self, data: Dict[str, Any]) -> bool:
        """写入数据"""
        pass

    @abstractmethod
    async def read(self, key: str) -> Optional[Dict[str, Any]]:
        """读取数据"""
        pass

    @abstractmethod
    async def query(self, filters: Dict[str, Any], pagination: Pagination) -> QueryResult:
        """查询数据"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除数据"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
```

### 4.3 多后端配置

```yaml
storage:
  backends:
    # MySQL 后端（翻译数据）
    mysql:
      type: "mysql"
      enabled: true
      config:
        host: "localhost"
        port: 3306
        database: "ai_terminal"
      data_types:
        - translation_sessions
        - translation_tasks

    # OSS 后端（文件存储）
    oss:
      type: "oss"
      enabled: false        # Phase 2 启用
      config:
        endpoint: "oss-cn-hangzhou.aliyuncs.com"
        bucket: "translation-files"
      data_types:
        - uploaded_files
        - translated_files

    # Redis 后端（缓存和会话）
    redis:
      type: "redis"
      enabled: false        # Phase 3 启用
      config:
        host: "localhost"
        port: 6379
        db: 0
      data_types:
        - user_sessions
        - hot_data_cache
```

## 5. 数据类型扩展规划

### 5.1 当前支持（Phase 1）

| 数据类型 | 存储后端 | 表名/Key | 说明 |
|---------|---------|----------|------|
| TranslationSession | MySQL | translation_sessions | 翻译会话 |
| TranslationTask | MySQL | translation_tasks | 翻译任务 |

### 5.2 未来支持（Phase 2-4）

| 数据类型 | 存储后端 | 表名/Key | Phase |
|---------|---------|----------|-------|
| UploadedFile | OSS | files/{file_id} | Phase 2 |
| FileMetadata | MySQL | file_metadata | Phase 2 |
| UserInfo | MySQL | users | Phase 3 |
| UserPreferences | Redis | user:pref:{user_id} | Phase 3 |
| UserSession | Redis | session:{token} | Phase 3 |
| AuditLog | Elasticsearch | audit_logs-{date} | Phase 4 |

## 6. 非功能需求扩展

### 6.1 性能要求（更新）

| 指标 | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|
| API 响应时间（写入） | < 10ms | < 10ms | < 5ms |
| API 响应时间（查询） | < 50ms | < 50ms | < 20ms |
| 吞吐量（写入） | 5000 条/分钟 | 10000 条/分钟 | 20000 条/分钟 |
| 吞吐量（查询） | 1000 qps | 2000 qps | 5000 qps |
| 并发连接数 | 100 | 500 | 1000 |

### 6.2 可扩展性要求（更新）

- 支持水平扩展（无状态设计）
- 支持多存储后端（插件式架构）
- 支持动态添加新的数据类型
- 支持配置热更新（无需重启）

### 6.3 监控指标（扩展）

**基础指标**：
- 请求量（按端点、按数据类型）
- 响应时间（P50/P95/P99）
- 错误率（按错误类型）

**存储指标**：
- 每个后端的读写 QPS
- 连接池使用率
- 缓冲区使用率
- 数据丢失次数

**业务指标**：
- 数据写入量（按数据类型）
- 数据查询量（按查询类型）
- 存储空间使用量
- 数据恢复成功率

## 7. 部署架构（完整版）

### 7.1 Phase 1 部署

```
┌─────────────────────────────────────┐
│  Backend V2                         │
└────────────┬────────────────────────┘
             │ HTTP
             ▼
┌─────────────────────────────────────┐
│  Persistence Service (1-2 实例)     │
│  - Translation API                  │
│  - MySQL Connector                  │
└────────────┬────────────────────────┘
             │
             ▼
      ┌──────────────┐
      │    MySQL     │
      └──────────────┘
```

### 7.2 Phase 2 部署（添加 OSS）

```
┌─────────────────────────────────────┐
│  Backend V2 + Frontend              │
└────────────┬────────────────────────┘
             │ HTTP
             ▼
┌─────────────────────────────────────┐
│  Persistence Service (2-4 实例)     │
│  - Translation API                  │
│  - Storage API                      │
│  - MySQL Connector                  │
│  - OSS Connector                    │
└──────┬─────────────────┬────────────┘
       │                 │
       ▼                 ▼
┌──────────────┐   ┌──────────────┐
│    MySQL     │   │     OSS      │
└──────────────┘   └──────────────┘
```

### 7.3 Phase 3 完整部署

```
                      ┌─────────────────┐
                      │  Load Balancer  │
                      └────────┬────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│ Backend V2  │        │  Frontend   │        │   Admin     │
└──────┬──────┘        └──────┬──────┘        └──────┬──────┘
       │                      │                       │
       └──────────────────────┼───────────────────────┘
                              │ HTTP
                              ▼
                    ┌──────────────────┐
                    │    API Gateway   │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    ┌─────────┐        ┌─────────┐        ┌─────────┐
    │Instance1│        │Instance2│        │Instance3│
    └────┬────┘        └────┬────┘        └────┬────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
   ┌──────────┐       ┌──────────┐      ┌──────────┐
   │  MySQL   │       │   OSS    │      │  Redis   │
   └──────────┘       └──────────┘      └──────────┘
```

## 8. 演进路线图

### Phase 1: 翻译数据持久化（当前 - Week 1-5）

**目标**：完成核心的批量写入和查询功能

- [x] 需求文档、架构文档
- [ ] 批量写入 API（sessions/tasks）
- [ ] 查询 API（sessions/tasks）
- [ ] 恢复 API（recovery）
- [ ] 单元测试 + 集成测试
- [ ] 部署到生产环境

### Phase 2: 文件存储持久化（Week 6-10）

**目标**：添加文件存储能力

- [ ] OSS 存储后端插件
- [ ] 文件上传/下载 API
- [ ] 文件元数据管理
- [ ] 文件生命周期管理
- [ ] 存储空间监控

### Phase 3: 用户数据持久化（Week 11-15）

**目标**：支持用户系统

- [ ] Redis 存储后端插件
- [ ] 用户信息管理 API
- [ ] 用户会话管理 API
- [ ] 缓存策略实现
- [ ] 用户数据导出

### Phase 4: 审计日志持久化（Week 16-20）

**目标**：完整的审计能力

- [ ] Elasticsearch 存储后端插件
- [ ] 审计日志写入 API
- [ ] 审计日志查询 API
- [ ] 日志导出功能
- [ ] 日志分析仪表盘

### Phase 5: 高级功能（Week 21+）

- [ ] 数据备份和恢复
- [ ] 多区域部署
- [ ] 数据归档
- [ ] 全文搜索
- [ ] 实时数据同步

## 9. 成功标准（完整版）

### 9.1 Phase 1 验收标准

**功能验收**：
- [ ] 批量写入接口完成（sessions/tasks）
- [ ] 查询接口完成（sessions/tasks）
- [ ] 恢复接口完成（recovery）
- [ ] 所有 P0 接口测试通过

**性能验收**：
- [ ] 批量写入响应时间 < 10ms（P95）
- [ ] 查询响应时间 < 50ms（P95）
- [ ] 吞吐量 > 5000 条/分钟
- [ ] 数据库压力降低 95%+

**可靠性验收**：
- [ ] 服务可用性 > 99.9%
- [ ] 数据丢失率 < 0.1%
- [ ] 恢复成功率 > 99%

### 9.2 Phase 2-4 验收标准

（待后续补充）

---

## 附录

### A. API 快速参考

**写入操作**：
```bash
POST /api/v1/translation/sessions/batch    # 批量写入会话
POST /api/v1/translation/tasks/batch       # 批量写入任务
POST /api/v1/translation/flush             # 强制刷新
```

**查询操作**：
```bash
GET /api/v1/translation/sessions                    # 查询会话列表
GET /api/v1/translation/sessions/{id}               # 查询单个会话
GET /api/v1/translation/sessions/{id}/tasks         # 查询会话任务
GET /api/v1/translation/tasks                       # 查询任务列表
GET /api/v1/translation/tasks/{id}                  # 查询单个任务
```

**恢复操作**：
```bash
GET  /api/v1/translation/recovery/incomplete-sessions   # 未完成会话
POST /api/v1/translation/recovery/restore/{id}          # 恢复会话
```

**管理操作**：
```bash
DELETE /api/v1/translation/sessions/{id}            # 删除会话
POST   /api/v1/translation/sessions/cleanup         # 清理过期数据
GET    /api/v1/translation/stats                    # 统计信息
```

### B. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2025-09-30 | 初始版本（仅批量写入） | Product Team |
| v2.0 | 2025-09-30 | 扩展为完整微服务（查询、恢复、多后端） | Product Team |