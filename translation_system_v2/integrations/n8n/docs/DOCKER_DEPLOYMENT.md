# Docker 部署方案

本文档说明如何使用Docker部署n8n工作流自动化环境，包括开发环境和生产环境的配置。

---

## 📋 目录

1. [架构设计](#架构设计)
2. [开发环境部署](#开发环境部署)
3. [生产环境部署](#生产环境部署)
4. [环境变量配置](#环境变量配置)
5. [数据持久化](#数据持久化)
6. [网络配置](#网络配置)
7. [备份和恢复](#备份和恢复)
8. [监控和日志](#监控和日志)

---

## 🏗️ 架构设计

### 容器架构

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                       │
│                  (translation_network)                  │
│                                                         │
│  ┌────────────────┐         ┌────────────────┐        │
│  │   n8n          │         │   Backend      │        │
│  │   Container    │ ←──────→│   Container    │        │
│  │   :5678        │         │   :8013        │        │
│  └────────────────┘         └────────────────┘        │
│         │                            │                 │
│         │                            │                 │
│  ┌─────────────┐            ┌────────────────┐       │
│  │  n8n_data   │            │  backend_data  │       │
│  │   Volume    │            │     Volume     │       │
│  └─────────────┘            └────────────────┘       │
└─────────────────────────────────────────────────────────┘
         │                            │
         ↓                            ↓
   Host: 5678                   Host: 8013
```

---

## 🛠️ 开发环境部署

### 快速启动

#### 步骤1: 创建docker-compose.yml

```yaml
version: '3.8'

services:
  # n8n工作流引擎
  n8n:
    image: n8nio/n8n:latest
    container_name: translation_n8n_dev
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - GENERIC_TIMEZONE=Asia/Shanghai
      - N8N_LOG_LEVEL=info
      - N8N_DIAGNOSTICS_ENABLED=false
    volumes:
      # n8n数据持久化
      - n8n_data:/home/node/.n8n
      # 工作流文件（只读）
      - ../workflows:/workflows:ro
      # 数据文件
      - /mnt/d/work/trans_excel:/data
    networks:
      - translation_network
    depends_on:
      - backend

  # 翻译后端API
  backend:
    build:
      context: ../../../backend_v2
      dockerfile: Dockerfile
    container_name: translation_backend_dev
    restart: unless-stopped
    ports:
      - "8013:8013"
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
    volumes:
      # 后端数据
      - ../../../backend_v2/data:/app/data
      - ../../../backend_v2/logs:/app/logs
      # 配置文件
      - ../../../backend_v2/config:/app/config
    networks:
      - translation_network

networks:
  translation_network:
    driver: bridge

volumes:
  n8n_data:
    driver: local
```

---

#### 步骤2: 启动服务

```bash
# 进入docker目录
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/docker

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

---

#### 步骤3: 验证部署

```bash
# 检查n8n
curl http://localhost:5678

# 检查后端
curl http://localhost:8013/api/database/health

# 检查容器内部连接
docker exec translation_n8n_dev curl http://backend:8013/api/database/health
```

---

#### 步骤4: 访问n8n

打开浏览器: **http://localhost:5678**

创建账户后即可开始使用。

---

## 🏢 生产环境部署

### 完整配置

#### docker-compose.prod.yml

```yaml
version: '3.8'

services:
  # n8n工作流引擎
  n8n:
    image: n8nio/n8n:latest
    container_name: translation_n8n_prod
    restart: always
    ports:
      - "5678:5678"
    environment:
      # 基础配置
      - N8N_HOST=${N8N_HOST}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - GENERIC_TIMEZONE=Asia/Shanghai

      # 认证配置
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}

      # 用户管理
      - N8N_USER_MANAGEMENT_DISABLED=false

      # 加密密钥
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}

      # 日志配置
      - N8N_LOG_LEVEL=warn
      - N8N_LOG_OUTPUT=console,file
      - N8N_LOG_FILE_LOCATION=/home/node/.n8n/logs/

      # 性能配置
      - EXECUTIONS_PROCESS=main
      - EXECUTIONS_DATA_SAVE_ON_ERROR=all
      - EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
      - EXECUTIONS_DATA_MAX_AGE=336  # 14天

      # Webhook配置
      - WEBHOOK_URL=https://${N8N_HOST}/

    volumes:
      # 数据持久化
      - n8n_data:/home/node/.n8n
      # 工作流文件（只读）
      - ../workflows:/workflows:ro
      # 数据文件
      - ${DATA_PATH}:/data
      # SSL证书
      - ./certs:/certs:ro

    networks:
      - translation_network

    depends_on:
      - backend

    # 健康检查
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:5678/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    # 资源限制
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  # 翻译后端API
  backend:
    build:
      context: ../../../backend_v2
      dockerfile: Dockerfile
    container_name: translation_backend_prod
    restart: always
    ports:
      - "8013:8013"
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=WARNING
      - QWEN_API_KEY=${QWEN_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}

    volumes:
      - backend_data:/app/data
      - backend_logs:/app/logs
      - ../../../backend_v2/config:/app/config:ro

    networks:
      - translation_network

    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8013/api/database/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    # 资源限制
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
        reservations:
          cpus: '2.0'
          memory: 2G

  # Nginx反向代理（生产环境）
  nginx:
    image: nginx:alpine
    container_name: translation_nginx_prod
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./certs:/etc/nginx/certs:ro
    networks:
      - translation_network
    depends_on:
      - n8n
      - backend

networks:
  translation_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16

volumes:
  n8n_data:
    driver: local
  backend_data:
    driver: local
  backend_logs:
    driver: local
```

---

### Nginx配置

#### nginx/conf.d/n8n.conf

```nginx
# n8n upstream
upstream n8n_backend {
    server n8n:5678;
}

# API backend upstream
upstream api_backend {
    server backend:8013;
}

# n8n HTTPS server
server {
    listen 443 ssl http2;
    server_name n8n.example.com;

    # SSL证书
    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;

    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 日志
    access_log /var/log/nginx/n8n_access.log;
    error_log /var/log/nginx/n8n_error.log;

    # 最大上传大小
    client_max_body_size 100M;

    # n8n location
    location / {
        proxy_pass http://n8n_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时配置
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}

# API HTTPS server
server {
    listen 443 ssl http2;
    server_name api.example.com;

    # SSL证书
    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;

    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 日志
    access_log /var/log/nginx/api_access.log;
    error_log /var/log/nginx/api_error.log;

    # 最大上传大小
    client_max_body_size 100M;

    # API location
    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时配置
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}

# HTTP到HTTPS重定向
server {
    listen 80;
    server_name n8n.example.com api.example.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 🔐 环境变量配置

### .env文件

```bash
# n8n配置
N8N_HOST=n8n.example.com
N8N_USER=admin
N8N_PASSWORD=<strong-password-here>
N8N_ENCRYPTION_KEY=<random-32-character-string>

# 后端配置
QWEN_API_KEY=<your-qwen-api-key>
OPENAI_API_KEY=<your-openai-api-key>

# 路径配置
DATA_PATH=/mnt/d/work/trans_excel
```

---

### 生成加密密钥

```bash
# 生成32字符随机密钥
openssl rand -hex 16

# 或使用Python
python3 -c "import secrets; print(secrets.token_hex(16))"
```

---

## 💾 数据持久化

### 卷挂载说明

| 容器 | 卷 | 用途 |
|-----|---|------|
| n8n | `n8n_data:/home/node/.n8n` | n8n配置、工作流、执行历史 |
| n8n | `../workflows:/workflows:ro` | 工作流模板（只读） |
| n8n | `/data` | 输入输出文件 |
| backend | `backend_data:/app/data` | 会话数据、任务缓存 |
| backend | `backend_logs:/app/logs` | 日志文件 |
| backend | `../config:/app/config:ro` | 配置文件（只读） |

---

### 数据目录结构

```
/mnt/d/work/trans_excel/
├── input/              # 输入文件
│   └── *.xlsx
├── output/             # 输出文件
│   └── *_translated.xlsx
├── glossaries/         # 术语表
│   └── *.json
└── logs/              # 日志文件
    ├── n8n.log
    └── backend.log
```

---

## 🌐 网络配置

### 容器间通信

```yaml
networks:
  translation_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

**容器内部访问**:
- n8n访问后端: `http://backend:8013`
- 后端访问n8n: `http://n8n:5678`

**宿主机访问**:
- n8n: `http://localhost:5678`
- 后端: `http://localhost:8013`

---

### 端口映射

| 服务 | 容器端口 | 主机端口 | 协议 |
|-----|---------|---------|------|
| n8n | 5678 | 5678 | HTTP |
| backend | 8013 | 8013 | HTTP |
| nginx | 80 | 80 | HTTP |
| nginx | 443 | 443 | HTTPS |

---

## 💽 备份和恢复

### 备份脚本

创建 `scripts/backup.sh`:

```bash
#!/bin/bash

# 备份目录
BACKUP_DIR="/backup/translation_system"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR/$TIMESTAMP"

# 备份n8n数据
echo "Backing up n8n data..."
docker run --rm \
  -v translation_n8n_data:/data \
  -v "$BACKUP_DIR/$TIMESTAMP":/backup \
  alpine \
  tar czf /backup/n8n_data.tar.gz /data

# 备份后端数据
echo "Backing up backend data..."
docker run --rm \
  -v translation_backend_data:/data \
  -v "$BACKUP_DIR/$TIMESTAMP":/backup \
  alpine \
  tar czf /backup/backend_data.tar.gz /data

# 备份工作流文件
echo "Backing up workflows..."
cp -r ../workflows "$BACKUP_DIR/$TIMESTAMP/"

# 备份配置文件
echo "Backing up config..."
cp .env "$BACKUP_DIR/$TIMESTAMP/"
cp docker-compose.yml "$BACKUP_DIR/$TIMESTAMP/"

# 清理旧备份（保留30天）
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR/$TIMESTAMP"
```

---

### 恢复脚本

创建 `scripts/restore.sh`:

```bash
#!/bin/bash

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
  echo "Usage: ./restore.sh <backup_directory>"
  exit 1
fi

# 停止服务
docker-compose down

# 恢复n8n数据
echo "Restoring n8n data..."
docker run --rm \
  -v translation_n8n_data:/data \
  -v "$BACKUP_DIR":/backup \
  alpine \
  sh -c "rm -rf /data/* && tar xzf /backup/n8n_data.tar.gz -C /"

# 恢复后端数据
echo "Restoring backend data..."
docker run --rm \
  -v translation_backend_data:/data \
  -v "$BACKUP_DIR":/backup \
  alpine \
  sh -c "rm -rf /data/* && tar xzf /backup/backend_data.tar.gz -C /"

# 恢复工作流
echo "Restoring workflows..."
cp -r "$BACKUP_DIR/workflows" ../

# 恢复配置
echo "Restoring config..."
cp "$BACKUP_DIR/.env" .
cp "$BACKUP_DIR/docker-compose.yml" .

# 重启服务
docker-compose up -d

echo "Restore completed"
```

---

### 定时备份

添加到crontab:

```bash
# 每天凌晨3点备份
0 3 * * * /path/to/scripts/backup.sh >> /var/log/translation_backup.log 2>&1
```

---

## 📊 监控和日志

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f n8n
docker-compose logs -f backend

# 查看最近100行
docker-compose logs --tail=100 n8n

# 查看特定时间段日志
docker-compose logs --since="2025-10-17T00:00:00" n8n
```

---

### 日志配置

#### n8n日志

```yaml
environment:
  - N8N_LOG_LEVEL=info  # debug | info | warn | error
  - N8N_LOG_OUTPUT=console,file
  - N8N_LOG_FILE_LOCATION=/home/node/.n8n/logs/
```

日志文件位置:
```
docker volume inspect translation_n8n_data
# 找到Mountpoint路径
/var/lib/docker/volumes/translation_n8n_data/_data/logs/
```

---

#### 后端日志

日志输出到:
```
/mnt/d/work/trans_excel/translation_system_v2/backend_v2/logs/
├── app.log
├── error.log
└── access.log
```

---

### 资源监控

```bash
# 查看容器资源使用
docker stats translation_n8n_prod translation_backend_prod

# 查看容器详情
docker inspect translation_n8n_prod

# 查看卷使用情况
docker system df -v
```

---

### 健康检查

```bash
# 检查容器健康状态
docker ps --filter "name=translation" --format "table {{.Names}}\t{{.Status}}"

# 手动健康检查
docker exec translation_n8n_prod wget --spider http://localhost:5678/healthz
docker exec translation_backend_prod curl -f http://localhost:8013/api/database/health
```

---

## 🔧 维护操作

### 更新服务

```bash
# 拉取最新镜像
docker-compose pull

# 重建并重启
docker-compose up -d --build

# 清理旧镜像
docker image prune -f
```

---

### 清理数据

```bash
# 清理执行历史（保留14天）
docker exec translation_n8n_prod n8n execute --prune

# 清理Docker缓存
docker system prune -a --volumes

# 清理特定卷
docker volume rm translation_n8n_data
```

---

### 扩容配置

**增加n8n并发**:

```yaml
environment:
  - EXECUTIONS_PROCESS=own  # 独立进程执行
  - N8N_CONCURRENCY_PRODUCTION_LIMIT=10  # 并发数
```

**增加资源限制**:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 4G
```

---

## 🚀 部署检查清单

### 开发环境

- [ ] Docker和Docker Compose已安装
- [ ] 后端代码已构建
- [ ] docker-compose.yml配置正确
- [ ] 启动服务: `docker-compose up -d`
- [ ] 访问n8n: http://localhost:5678
- [ ] 访问后端: http://localhost:8013
- [ ] 导入测试工作流
- [ ] 执行测试翻译

---

### 生产环境

- [ ] 服务器资源充足（CPU≥2核, 内存≥4GB）
- [ ] 域名已配置（n8n.example.com, api.example.com）
- [ ] SSL证书已准备
- [ ] .env文件已配置（强密码）
- [ ] Nginx配置正确
- [ ] 防火墙规则已设置
- [ ] 启动服务: `docker-compose -f docker-compose.prod.yml up -d`
- [ ] 验证HTTPS访问
- [ ] 配置备份任务
- [ ] 设置监控告警
- [ ] 执行负载测试

---

## 📖 相关文档

- [快速开始](../README.md) - 5分钟上手
- [实现方案](./IMPLEMENTATION_PLAN.md) - 详细实施步骤
- [工作流目录](./WORKFLOW_CATALOG.md) - 所有工作流说明
- [故障排除](./TROUBLESHOOTING.md) - 常见问题

---

**Docker部署完成后，你就可以开始使用n8n自动化翻译工作流了！** 🎉
