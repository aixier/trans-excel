# Persistence Service

**通用的、可扩展的数据持久化微服务**

```
One Service, Multiple Backends, Unified API
(一个服务，多个后端，统一接口)
```

---

## 📚 项目文档

本项目采用**文档驱动开发（Documentation Driven Development）**，在编写代码前完成详细的需求和架构设计。

### 核心文档

| 文档 | 说明 | 状态 | 阅读对象 |
|------|------|------|----------|
| **[需求文档 V2.0](docs/REQUIREMENTS_V2.md)** | 完整的功能需求、非功能需求、用户场景 | ✅ 完成 | 产品经理、开发团队 |
| **[架构设计 V2.0](docs/ARCHITECTURE_V2.md)** | 完整的架构设计、技术选型、核心组件 | ✅ 完成 | 架构师、开发团队 |
| **[项目路线图](docs/ROADMAP.md)** | 演进路线、里程碑、资源规划 | ✅ 完成 | 项目经理、团队全员 |

### 参考文档（Phase 1 设计）

| 文档 | 说明 | 状态 |
|------|------|------|
| [需求文档 V1.0](docs/REQUIREMENTS.md) | Phase 1 基础需求（仅批量写入） | 🔄 参考 |
| [架构设计 V1.0](docs/ARCHITECTURE.md) | Phase 1 基础架构 | 🔄 参考 |

---

## 🎯 项目概述

### 问题背景

当前翻译系统存在的问题：
- 数据库压力大（每条任务都触发写入）
- 架构耦合严重（持久化逻辑与业务逻辑混合）
- 事务复杂度高（Session 和 Task 两阶段提交）
- 并发问题（DataFrame 和数据库状态不一致）

### 解决方案

通过 **Persistence Service** 实现：
1. **批量写入**：1000 条/批，降低数据库压力 95%+
2. **存储抽象**：插件式架构，支持 MySQL、OSS、Redis、Elasticsearch
3. **异步非阻塞**：Fire-and-Forget 模式，API 响应 < 10ms
4. **完整功能**：不仅写入，还支持查询、恢复、管理

### 核心特性

| 特性 | 说明 | Phase |
|------|------|-------|
| **批量写入** | 批量持久化会话和任务数据 | Phase 1 |
| **数据查询** | 查询历史数据、分页、过滤、排序 | Phase 1 |
| **数据恢复** | 服务重启后恢复未完成会话 | Phase 1 |
| **文件存储** | 上传/下载文件到 OSS | Phase 2 |
| **用户管理** | 用户信息和会话管理 | Phase 3 |
| **审计日志** | 操作日志记录和查询 | Phase 4 |

---

## 🏗️ 架构概览

### 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                   Client Applications                   │
│  Backend V2 | Frontend | Admin Dashboard               │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP + JSON
┌────────────────────────▼────────────────────────────────┐
│              Persistence Service                        │
│                                                          │
│  API Layer (FastAPI)                                    │
│    ↓                                                     │
│  Service Layer (BufferManager, QueryService, Recovery)  │
│    ↓                                                     │
│  Storage Abstraction Layer (Plugin System)              │
│    ↓                                                     │
│  Storage Plugins (MySQL, OSS, Redis, ES)                │
└──────────────────┬──────────────────────────────────────┘
                   │
     ┌─────────────┼─────────────┬──────────────┐
     ▼             ▼             ▼              ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────────┐
│  MySQL  │  │   OSS   │  │  Redis  │  │Elasticsearch│
└─────────┘  └─────────┘  └─────────┘  └────────────┘
```

### 核心组件

| 组件 | 职责 | 技术 |
|------|------|------|
| **API Layer** | HTTP 端点、数据验证 | FastAPI + Pydantic |
| **Buffer Manager** | 批量缓冲、刷新策略 | Python asyncio |
| **Query Service** | 查询构建、结果聚合 | QueryBuilder + ORM |
| **Recovery Service** | 数据恢复、会话重建 | Business Logic |
| **Storage Plugins** | 存储后端适配 | Plugin Architecture |

---

## 📊 演进路线

### Phase 1: 翻译数据持久化 MVP (Week 1-5)

**目标**：完成核心功能，服务于翻译系统

**功能**：
- ✅ 批量写入（sessions/tasks）
- ✅ 数据查询（列表、详情）
- ✅ 数据恢复（未完成会话）
- ✅ 系统管理（健康检查、统计）

**技术栈**：
- FastAPI + Uvicorn
- aiomysql + MySQL 8.0
- Pydantic 2.5

### Phase 2: 文件存储持久化 (Week 6-10)

**目标**：添加文件存储能力

**功能**：
- 文件上传/下载（OSS）
- 文件元数据管理
- 预签名 URL

### Phase 3: 用户数据持久化 (Week 11-15)

**目标**：支持用户系统

**功能**：
- 用户信息管理
- 用户会话管理（Redis）
- 缓存策略

### Phase 4: 审计日志持久化 (Week 16-20)

**目标**：完整的审计能力

**功能**：
- 审计日志记录（Elasticsearch）
- 日志查询和导出
- 全文搜索

---

## 📋 API 快速参考

### Phase 1 核心 API

#### 批量写入
```bash
POST /api/v1/translation/sessions/batch    # 批量写入会话
POST /api/v1/translation/tasks/batch       # 批量写入任务
POST /api/v1/translation/flush             # 强制刷新缓冲区
```

#### 数据查询
```bash
GET /api/v1/translation/sessions                    # 查询会话列表
GET /api/v1/translation/sessions/{id}               # 查询单个会话
GET /api/v1/translation/sessions/{id}/tasks         # 查询会话任务
GET /api/v1/translation/tasks                       # 查询任务列表
GET /api/v1/translation/tasks/{id}                  # 查询单个任务
```

#### 数据恢复
```bash
GET  /api/v1/translation/recovery/incomplete-sessions   # 未完成会话列表
POST /api/v1/translation/recovery/restore/{id}          # 恢复会话数据
```

#### 系统管理
```bash
GET /health                             # 健康检查
GET /api/v1/system/metrics              # 性能指标
GET /api/v1/system/config               # 配置信息
```

---

## 🚀 快速开始（未来实现后）

### 前置要求

- Python 3.10+
- MySQL 8.0+
- 2GB+ 内存

### 安装步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd persistence_service

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置数据库
cp config/config.yaml.example config/config.yaml
vim config/config.yaml  # 修改数据库连接信息

# 5. 初始化数据库
mysql -u root -p ai_terminal < database/schema.sql

# 6. 启动服务
python main.py
```

### 验证服务

```bash
# 健康检查
curl http://localhost:8001/health

# 预期输出
{
  "status": "healthy",
  "database": "healthy",
  "buffer": {...}
}
```

---

## 📈 性能指标

### Phase 1 目标

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| API 响应时间（写入） | < 10ms | P95 |
| API 响应时间（查询） | < 50ms | P95 |
| 吞吐量（写入） | > 5000 条/分钟 | 峰值 |
| 数据库压力降低 | 95%+ | 对比现有方案 |
| 服务可用性 | 99.9% | Uptime 监控 |

### Phase 2+ 目标

| 指标 | Phase 2 | Phase 3 | Phase 4 |
|------|---------|---------|---------|
| API 响应时间 | < 10ms | < 5ms | < 5ms |
| 吞吐量 | 10000 条/min | 20000 条/min | 50000 条/min |
| 可用性 | 99.95% | 99.99% | 99.99% |

---

## 🛡️ 设计权衡

### 优点

✅ **性能优异**：批量处理降低数据库压力 95%+
✅ **架构解耦**：业务系统不依赖持久化细节
✅ **易于扩展**：插件式架构，轻松添加新存储
✅ **简单可靠**：无消息队列，架构简单

### 代价

❌ **数据延迟**：数据最多延迟 30 秒写入
❌ **数据丢失**：服务崩溃最多丢失 1000 条或 30 秒数据
❌ **最终一致**：内存与数据库短暂不一致

### 适用场景

✅ **适合**：
- 可容忍短时间数据丢失（如进度跟踪）
- 高频写入场景（如任务状态更新）
- 需要降低数据库压力的场景

❌ **不适合**：
- 金融交易等零容忍数据丢失场景
- 需要实时数据一致性的场景

---

## 🗂️ 项目结构（未来实现）

```
persistence_service/
├── main.py                    # FastAPI 应用入口
├── api/                       # API 层
│   └── v1/
│       ├── translation_api.py
│       ├── storage_api.py
│       └── system_api.py
├── services/                  # 服务层
│   ├── buffer_manager.py
│   ├── query_service.py
│   └── recovery_service.py
├── storage/                   # 存储层
│   ├── backend.py            # 抽象接口
│   ├── mysql_plugin.py
│   ├── oss_plugin.py
│   └── redis_plugin.py
├── models/                    # 数据模型
│   └── api_models.py
├── config/                    # 配置
│   ├── settings.py
│   └── config.yaml
├── docs/                      # 文档
│   ├── REQUIREMENTS_V2.md
│   ├── ARCHITECTURE_V2.md
│   ├── ROADMAP.md
│   └── API.md
├── tests/                     # 测试
│   ├── unit/
│   ├── integration/
│   └── performance/
└── README.md                  # 本文档
```

---

## 📖 文档导航

### 产品文档
- [需求文档 V2.0](docs/REQUIREMENTS_V2.md) - 完整的功能需求和用户场景
- [项目路线图](docs/ROADMAP.md) - 演进路线和里程碑

### 技术文档
- [架构设计 V2.0](docs/ARCHITECTURE_V2.md) - 完整的架构设计和技术选型
- [API 接口文档](docs/API.md) - API 详细说明（Phase 1 完成后）
- [数据模型文档](docs/DATA_MODELS.md) - 数据模型设计（Phase 1 完成后）

### 运维文档
- [部署文档](docs/DEPLOYMENT.md) - 部署和配置说明（Phase 1 完成后）
- [监控告警](docs/MONITORING.md) - 监控指标和告警规则（Phase 2 完成后）

---

## 👥 团队

| 角色 | 人数 | 主要职责 |
|------|------|----------|
| 产品经理 | 1 | 需求管理、优先级决策 |
| 架构师 | 1 | 架构设计、技术选型 |
| 后端工程师 | 2 | 核心功能开发 |
| 测试工程师 | 1 | 测试用例、质量保证 |
| 运维工程师 | 1 | 部署、监控、运维 |

---

## 📅 当前状态

**Phase**: Phase 1 - 设计阶段

**完成情况**：
- [x] 需求文档 V2.0
- [x] 架构设计 V2.0
- [x] 项目路线图
- [ ] 核心代码实现（待开始）
- [ ] 单元测试（待开始）
- [ ] 集成测试（待开始）

**下一步**：
1. 产品经理和架构师评审需求和架构文档
2. 评审通过后，开始编写代码
3. 实现 Phase 1 核心功能

---

## 📞 联系方式

如有问题或建议，请联系：
- 项目经理：[待补充]
- 技术负责人：[待补充]
- Issue Tracker：[待补充]

---

## 📄 许可证

MIT License

---

**最后更新**: 2025-09-30
**文档状态**: ✅ 设计完成，待评审
**下次评审**: 待定