# Persistence Service

独立的批量数据持久化服务，为翻译系统提供高效、解耦的数据存储能力。

## 📋 项目概述

Persistence Service 是一个独立运行的微服务，负责将翻译系统的运行数据批量写入 MySQL 数据库。通过批量处理和容忍短暂数据丢失的设计，实现了架构简单、性能优异的持久化方案。

### 核心特性

- **完全解耦**：与主业务系统通过 HTTP API 通信
- **批量高效**：批量写入数据库，减少 99%+ 数据库操作
- **简单可靠**：无消息队列、无复杂重试，接受最多 30 秒数据丢失
- **异步非阻塞**：Fire-and-Forget 调用，不阻塞业务逻辑

## 🚀 快速开始

### 前置要求

- Python 3.10+
- MySQL 8.0+
- 2GB+ 内存

### 安装步骤

```bash
# 1. 进入项目目录
cd persistence_service

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置数据库
vim config/config.yaml  # 修改数据库连接信息

# 5. 初始化数据库（创建表）
mysql -u root -p ai_terminal < docs/schema.sql

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

## 📚 文档

完整文档位于 `docs/` 目录：

| 文档 | 说明 |
|------|------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架构设计、核心组件、数据流 |
| [API.md](docs/API.md) | API 接口文档、调用示例 |
| [DATA_MODELS.md](docs/DATA_MODELS.md) | 数据模型、数据库表结构 |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | 部署指南、配置说明、运维 |

## 🔧 配置

主要配置文件：`config/config.yaml`

```yaml
# 缓冲区配置
buffer:
  max_buffer_size: 1000        # 缓冲区大小（条）
  flush_interval: 30           # 刷新间隔（秒）

# 数据库配置
database:
  host: "localhost"
  port: 3306
  user: "root"
  password: ""
  database: "ai_terminal"
  pool_size: 10

# 服务配置
service:
  host: "0.0.0.0"
  port: 8001
```

支持环境变量覆盖：
```bash
export DB_HOST=localhost
export DB_PASSWORD=your_password
export BUFFER_MAX_SIZE=2000
```

## 📡 API 端点

### 批量持久化

```bash
# 批量持久化会话
POST /api/v1/persistence/sessions/batch

# 批量持久化任务
POST /api/v1/persistence/tasks/batch

# 强制刷新缓冲区
POST /api/v1/persistence/flush

# 获取缓冲区统计
GET /api/v1/persistence/stats
```

### 健康检查

```bash
# 简单健康检查
GET /

# 详细健康检查
GET /health
```

详细 API 文档见 [docs/API.md](docs/API.md)

## 🔌 客户端集成

在 Backend V2 中使用：

```python
from services.persistence.persistence_client import persistence_client

# 持久化会话
await persistence_client.persist_session(session_data)

# 持久化任务
await persistence_client.persist_tasks(tasks_data)

# 强制刷新（停止/暂停时）
await persistence_client.flush_all()
```

## 📊 性能指标

| 指标 | 目标值 |
|------|--------|
| API 响应时间 | < 10ms |
| 批量写入时间 | < 1s (1000 条) |
| 数据库压力降低 | 95%+ |
| 最大数据丢失 | 30 秒 或 1000 条 |

## 🏗️ 项目结构

```
persistence_service/
├── main.py                    # FastAPI 应用入口
├── api/                       # API 路由层
│   └── batch_api.py
├── services/                  # 业务逻辑层
│   └── buffer_manager.py
├── database/                  # 数据访问层
│   └── mysql_connector.py
├── models/                    # 数据模型
│   └── api_models.py
├── config/                    # 配置管理
│   ├── settings.py
│   └── config.yaml
├── docs/                      # 文档
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DATA_MODELS.md
│   └── DEPLOYMENT.md
└── requirements.txt           # Python 依赖
```

## 🔍 监控和运维

### 查看服务状态

```bash
# 缓冲区统计
curl http://localhost:8001/api/v1/persistence/stats

# 健康检查
curl http://localhost:8001/health
```

### 日志查看

```bash
# 实时日志
tail -f logs/persistence_service.log

# 错误日志
grep ERROR logs/persistence_service.log
```

### 手动刷新

```bash
# 触发强制刷新（如停止前）
curl -X POST http://localhost:8001/api/v1/persistence/flush
```

## 🛡️ 容错设计

### 数据丢失场景

- **服务崩溃**：丢失内存缓冲区数据（最多 1000 条或 30 秒）
- **数据库故障**：丢弃当前批次，继续接收新数据
- **网络超时**：客户端记录警告，不重试

### 不会发生的问题

- ✅ 数据重复（幂等性保证）
- ✅ 数据不一致（批量原子操作）
- ✅ 数据损坏（Pydantic 验证）

## 🚦 生产部署

### 使用 systemd

```bash
# 创建服务文件
sudo vim /etc/systemd/system/persistence-service.service

# 启动服务
sudo systemctl start persistence-service
sudo systemctl enable persistence-service

# 查看状态
sudo systemctl status persistence-service
```

详细部署指南见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## ⚠️ 重要说明

### 适用场景

✅ **适合：**
- 可容忍短时间数据丢失的场景（如进度跟踪）
- 高频写入场景（如任务状态更新）
- 需要降低数据库压力的场景

❌ **不适合：**
- 金融交易等零容忍数据丢失场景
- 需要实时数据一致性的场景

### 设计权衡

- ✅ **获得**：架构简单、性能优异、完全解耦
- ❌ **代价**：最多丢失 30 秒或 1000 条数据

## 🤝 与主系统集成

```
Backend V2 (主业务)
      ↓
PersistenceClient
      ↓ HTTP POST (Fire-and-Forget)
Persistence Service
      ↓ 批量写入（1000 条/次）
MySQL Database
```

## 📝 开发计划

### Phase 1: 原型验证（当前）
- [x] 目录结构
- [x] 架构设计文档
- [x] API 接口文档
- [ ] 核心代码实现
- [ ] 单元测试

### Phase 2: 生产就绪
- [ ] 监控指标（Prometheus）
- [ ] 健康检查增强
- [ ] 优雅关闭
- [ ] 完善错误处理

### Phase 3: 高可用
- [ ] 多实例部署
- [ ] 负载均衡
- [ ] 连接池优化

## 🐛 故障排查

### 服务无法启动

```bash
# 检查端口占用
netstat -tlnp | grep 8001

# 检查配置文件
cat config/config.yaml

# 检查日志
tail -f logs/persistence_service.log
```

### 数据库连接失败

```bash
# 检查 MySQL 状态
systemctl status mysql

# 测试连接
mysql -h localhost -u root -p ai_terminal
```

更多故障排查见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#7-故障处理)

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题，请通过以下方式联系：
- Issue: [GitHub Issues](#)
- Email: [admin@example.com](#)

---

**注意**：这是一个为翻译系统特别设计的实用方案，通过接受短暂数据丢失换取架构简单性和高性能。请确保理解其设计权衡后再使用。