# Persistence Service - 部署和配置说明

## 1. 目录结构

```
persistence_service/
├── main.py                    # FastAPI 应用入口
├── api/                       # API 路由
│   ├── __init__.py
│   └── batch_api.py          # 批量持久化 API
├── services/                  # 业务服务
│   ├── __init__.py
│   └── buffer_manager.py     # 缓冲区管理器
├── database/                  # 数据库层
│   ├── __init__.py
│   └── mysql_connector.py    # MySQL 连接器
├── models/                    # 数据模型
│   ├── __init__.py
│   └── api_models.py         # API 模型定义
├── config/                    # 配置管理
│   ├── __init__.py
│   ├── settings.py           # 配置类
│   └── config.yaml           # 配置文件
├── docs/                      # 文档
│   ├── ARCHITECTURE.md       # 架构设计
│   ├── API.md                # API 接口文档
│   ├── DATA_MODELS.md        # 数据模型
│   └── DEPLOYMENT.md         # 本文档
├── requirements.txt           # Python 依赖
└── README.md                  # 项目说明
```

## 2. 环境要求

### 2.1 系统要求

- **操作系统**: Linux / macOS / Windows
- **Python**: 3.10+
- **MySQL**: 8.0+
- **内存**: 建议 2GB+（缓冲区 + 数据库连接池）
- **磁盘**: 100MB+（应用代码 + 日志）

### 2.2 Python 依赖

```txt
# requirements.txt
fastapi==0.104.1              # Web 框架
uvicorn[standard]==0.24.0     # ASGI 服务器
pydantic==2.5.0               # 数据验证
pydantic-settings==2.1.0      # 配置管理
aiomysql==0.2.0               # 异步 MySQL 客户端
PyMySQL==1.1.0                # MySQL 驱动
PyYAML==6.0.1                 # YAML 配置解析
python-dateutil==2.8.2        # 日期处理
httpx==0.25.2                 # HTTP 客户端（测试用）
```

### 2.3 数据库要求

需要预先创建数据库和表：

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS ai_terminal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建表（见 DATA_MODELS.md 中的 SQL）
USE ai_terminal;
-- translation_sessions 表
-- translation_tasks 表
```

## 3. 配置管理

### 3.1 配置文件（config/config.yaml）

```yaml
# 服务配置
service:
  host: "0.0.0.0"
  port: 8001
  workers: 1
  reload: false
  log_level: "info"

# 缓冲区配置
buffer:
  max_buffer_size: 1000        # 最大缓冲条数
  flush_interval: 30           # 刷新间隔（秒）
  max_batch_size: 1000         # API 单次请求最大条数

# 数据库配置
database:
  host: "localhost"
  port: 3306
  user: "root"
  password: ""
  database: "ai_terminal"
  pool_size: 10                # 连接池大小
  pool_recycle: 3600           # 连接回收时间（秒）
  echo: false                  # 是否打印 SQL（调试用）

# 日志配置
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/persistence_service.log"
  max_bytes: 10485760          # 10MB
  backup_count: 5
```

### 3.2 环境变量（可选）

环境变量会覆盖配置文件：

```bash
# 数据库配置
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=your_password
export DB_DATABASE=ai_terminal

# 服务配置
export SERVICE_HOST=0.0.0.0
export SERVICE_PORT=8001

# 缓冲区配置
export BUFFER_MAX_SIZE=1000
export BUFFER_FLUSH_INTERVAL=30
```

### 3.3 配置加载优先级

```
环境变量 > config.yaml > 默认值
```

## 4. 部署方式

### 4.1 开发环境部署

#### 步骤 1: 安装依赖

```bash
cd persistence_service

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 步骤 2: 配置数据库

```bash
# 修改 config/config.yaml
vim config/config.yaml

# 或使用环境变量
export DB_HOST=localhost
export DB_PASSWORD=your_password
```

#### 步骤 3: 初始化数据库

```bash
# 连接到 MySQL
mysql -u root -p

# 执行建表语句（见 DATA_MODELS.md）
USE ai_terminal;
-- 复制粘贴建表 SQL
```

#### 步骤 4: 启动服务

```bash
# 开发模式（自动重载）
python main.py

# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

#### 步骤 5: 验证服务

```bash
# 检查健康状态
curl http://localhost:8001/health

# 预期输出
{
  "status": "healthy",
  "database": "healthy",
  "buffer": {...}
}
```

### 4.2 生产环境部署（手动）

#### 步骤 1: 准备服务器

```bash
# 安装 Python 3.10+
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# 安装 MySQL
sudo apt install mysql-server
```

#### 步骤 2: 部署代码

```bash
# 上传代码到服务器
scp -r persistence_service user@server:/opt/

# 安装依赖
cd /opt/persistence_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 步骤 3: 配置服务

```bash
# 修改配置文件
vim config/config.yaml

# 设置生产配置
service:
  reload: false
  workers: 2
  log_level: "warning"
```

#### 步骤 4: 使用 systemd 管理服务

创建服务文件 `/etc/systemd/system/persistence-service.service`:

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

启动服务：

```bash
# 重载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start persistence-service

# 开机自启
sudo systemctl enable persistence-service

# 查看状态
sudo systemctl status persistence-service

# 查看日志
sudo journalctl -u persistence-service -f
```

### 4.3 使用 Docker 部署（未来）

#### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8001

# 启动服务
CMD ["python", "main.py"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  persistence:
    build: .
    ports:
      - "8001:8001"
    environment:
      - DB_HOST=mysql
      - DB_USER=root
      - DB_PASSWORD=password
      - DB_DATABASE=ai_terminal
    depends_on:
      - mysql
    restart: always

  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=ai_terminal
    volumes:
      - mysql_data:/var/lib/mysql
    restart: always

volumes:
  mysql_data:
```

启动：

```bash
docker-compose up -d
```

### 4.4 使用 Nginx 反向代理（可选）

Nginx 配置 `/etc/nginx/sites-available/persistence`:

```nginx
upstream persistence_backend {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name persistence.example.com;

    location / {
        proxy_pass http://persistence_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 2s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }

    # 健康检查
    location /health {
        proxy_pass http://persistence_backend/health;
        access_log off;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/persistence /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 5. 客户端集成

### 5.1 在 Backend V2 中集成

#### 步骤 1: 创建客户端

在 `backend_v2/services/persistence/` 中创建 `persistence_client.py`:

```python
# backend_v2/services/persistence/persistence_client.py
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
        if not self.session_buffer:
            return

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(
                    f"{self.base_url}/api/v1/persistence/sessions/batch",
                    json={"sessions": self.session_buffer}
                )
            self.session_buffer = []
        except Exception as e:
            logger.warning(f"Failed to persist sessions: {e}")
            self.session_buffer = []

    async def _flush_tasks(self):
        if not self.task_buffer:
            return

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(
                    f"{self.base_url}/api/v1/persistence/tasks/batch",
                    json={"tasks": self.task_buffer}
                )
            self.task_buffer = []
        except Exception as e:
            logger.warning(f"Failed to persist tasks: {e}")
            self.task_buffer = []

    async def flush_all(self):
        """强制刷新所有缓冲区"""
        await self._flush_sessions()
        await self._flush_tasks()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(f"{self.base_url}/api/v1/persistence/flush")
        except Exception as e:
            logger.error(f"Failed to flush on server: {e}")

# 全局实例
persistence_client = PersistenceClient()
```

#### 步骤 2: 修改 TaskPersister

```python
# backend_v2/services/persistence/task_persister.py

from services.persistence.persistence_client import persistence_client

class TaskPersister:
    async def persist_tasks(self, session_id: str, force: bool = False):
        """持久化任务（使用持久化服务）"""
        task_manager = session_manager.get_task_manager(session_id)
        if not task_manager:
            return

        # 准备会话数据
        session_data = self._prepare_session_data(session_id, task_manager)
        await persistence_client.persist_session(session_data)

        # 准备任务数据
        tasks_data = self._prepare_tasks_data(task_manager)
        await persistence_client.persist_tasks(tasks_data)

        if force:
            await persistence_client.flush_all()
```

#### 步骤 3: 配置服务地址

在 `backend_v2/config/config.yaml` 中添加：

```yaml
persistence_service:
  url: "http://localhost:8001"
  batch_size: 100
  timeout: 2.0
```

## 6. 监控和日志

### 6.1 日志管理

日志文件位置：
```
logs/
├── persistence_service.log      # 主日志
├── persistence_service.log.1    # 轮转日志
└── ...
```

查看日志：
```bash
# 实时查看
tail -f logs/persistence_service.log

# 查看错误
grep ERROR logs/persistence_service.log

# 查看最近的刷新操作
grep "flush" logs/persistence_service.log
```

### 6.2 性能监控

健康检查端点：
```bash
# 获取缓冲区状态
curl http://localhost:8001/api/v1/persistence/stats

# 输出示例
{
  "buffer": {
    "sessions_count": 150,
    "tasks_count": 850,
    "usage_percent": 100.0
  },
  "flush_info": {
    "last_flush_time": "2025-09-30T16:30:00",
    "flush_count_today": 45
  },
  "performance": {
    "total_tasks_written": 38250,
    "average_batch_size": 1000
  }
}
```

### 6.3 告警规则（建议）

```bash
# 示例：使用 cron 检查服务健康
*/5 * * * * curl -f http://localhost:8001/health || echo "Persistence service down!" | mail -s "Alert" admin@example.com
```

## 7. 故障处理

### 7.1 常见问题

#### 问题 1: 服务无法启动

```bash
# 检查端口占用
sudo netstat -tlnp | grep 8001

# 检查配置文件
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# 检查数据库连接
mysql -h localhost -u root -p ai_terminal
```

#### 问题 2: 数据库连接失败

```bash
# 检查 MySQL 是否运行
sudo systemctl status mysql

# 测试连接
mysql -h localhost -u root -p

# 检查配置
grep database config/config.yaml
```

#### 问题 3: 缓冲区满但未刷新

```bash
# 手动触发刷新
curl -X POST http://localhost:8001/api/v1/persistence/flush

# 检查刷新日志
grep "flush" logs/persistence_service.log
```

### 7.2 数据恢复

如果服务崩溃导致数据丢失：

1. **接受数据丢失**（设计选择）
2. **从主业务系统重新同步**（如果需要）
3. **检查数据库中的最新记录**

```sql
-- 查看最新的会话
SELECT * FROM translation_sessions ORDER BY updated_at DESC LIMIT 10;

-- 查看最新的任务
SELECT * FROM translation_tasks ORDER BY updated_at DESC LIMIT 10;
```

## 8. 性能调优

### 8.1 缓冲区调优

```yaml
# 高频写入场景（降低延迟）
buffer:
  max_buffer_size: 500          # 更小的缓冲区
  flush_interval: 10            # 更频繁刷新

# 低频写入场景（降低数据库压力）
buffer:
  max_buffer_size: 2000         # 更大的缓冲区
  flush_interval: 60            # 更长的间隔
```

### 8.2 数据库连接池调优

```yaml
database:
  pool_size: 20                 # 增加连接数（多并发）
  pool_recycle: 1800            # 更短的回收时间（避免超时）
```

### 8.3 API 超时调优

客户端：
```python
# 根据网络情况调整
async with httpx.AsyncClient(timeout=5.0) as client:  # 增加超时
    await client.post(...)
```

## 9. 安全建议

### 9.1 网络隔离

- 仅允许 Backend V2 访问（防火墙规则）
- 不暴露到公网

```bash
# iptables 示例
sudo iptables -A INPUT -p tcp --dport 8001 -s 192.168.1.100 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8001 -j DROP
```

### 9.2 数据库安全

- 使用专用数据库用户（最小权限）
- 启用 SSL 连接（生产环境）

```sql
-- 创建专用用户
CREATE USER 'persistence'@'localhost' IDENTIFIED BY 'strong_password';
GRANT INSERT, UPDATE, SELECT ON ai_terminal.* TO 'persistence'@'localhost';
FLUSH PRIVILEGES;
```

### 9.3 日志脱敏

避免记录敏感信息：
```python
# 不要记录完整的源文本
logger.info(f"Processing task {task_id[:8]}...")  # 只记录 ID 前缀
```

## 10. 升级和维护

### 10.1 滚动升级

```bash
# 1. 触发强制刷新
curl -X POST http://localhost:8001/api/v1/persistence/flush

# 2. 停止服务
sudo systemctl stop persistence-service

# 3. 更新代码
git pull

# 4. 安装新依赖
pip install -r requirements.txt

# 5. 启动服务
sudo systemctl start persistence-service

# 6. 验证
curl http://localhost:8001/health
```

### 10.2 数据库迁移

使用 Alembic 或手动执行：

```bash
# 备份数据库
mysqldump -u root -p ai_terminal > backup_$(date +%Y%m%d).sql

# 执行迁移 SQL
mysql -u root -p ai_terminal < migration_v2.sql

# 验证
mysql -u root -p ai_terminal -e "SHOW TABLES"
```

## 11. 总结

### 快速启动检查清单

- [ ] Python 3.10+ 已安装
- [ ] MySQL 8.0+ 已安装并运行
- [ ] 数据库表已创建
- [ ] 依赖已安装 (`pip install -r requirements.txt`)
- [ ] 配置文件已修改 (`config/config.yaml`)
- [ ] 服务可启动 (`python main.py`)
- [ ] 健康检查通过 (`curl http://localhost:8001/health`)
- [ ] 客户端集成完成（Backend V2）

### 运维命令速查

```bash
# 启动服务
python main.py

# 查看状态
curl http://localhost:8001/health

# 查看统计
curl http://localhost:8001/api/v1/persistence/stats

# 强制刷新
curl -X POST http://localhost:8001/api/v1/persistence/flush

# 查看日志
tail -f logs/persistence_service.log

# 重启服务（systemd）
sudo systemctl restart persistence-service
```