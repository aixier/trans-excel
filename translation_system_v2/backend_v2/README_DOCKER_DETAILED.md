# 🐳 Backend V2 Docker 部署指南

**目标**: 独立 Docker 容器部署，简单启动，简单配置

---

## ⚡ 快速开始

### 1. 构建镜像（分层优化，利用缓存）

```bash
cd /mnt/d/work/trans_excel/translation_system_v2/backend_v2

# 构建镜像
docker build -t translation-backend:latest .
```

**构建优化说明**:
- ✅ **分层构建**: 依赖安装层会被缓存，代码修改不会重新安装依赖
- ✅ **slim 基础镜像**: 使用 python:3.10-slim 减小镜像大小
- ✅ **.dockerignore**: 排除不必要的文件，加快构建速度

---

### 2. 运行容器（最简单方式）

```bash
docker run -d \
  --name translation-backend \
  -p 8013:8013 \
  -v /mnt/d/work/trans_excel:/app/data \
  -e QWEN_API_KEY=sk-4c89a24b73d24731b86bf26337398cef \
  -e MYSQL_HOST=rm-bp13t8tx0697ewx4wpo.mysql.rds.aliyuncs.com \
  -e MYSQL_USER=chenyang \
  -e MYSQL_PASSWORD=mRA9ycdvj8NW71qG5Dnajq5 \
  -e MYSQL_DATABASE=ai_terminal \
  translation-backend:latest
```

**参数说明**:
- `-d`: 后台运行
- `--name`: 容器名称
- `-p 8013:8013`: 端口映射
- `-v`: 挂载数据目录（输入/输出文件）
- `-e`: 环境变量配置

---

### 3. 使用 .env 文件（推荐）

**创建 .env 文件**:

```bash
cat > .env <<EOF
QWEN_API_KEY=sk-4c89a24b73d24731b86bf26337398cef
MYSQL_HOST=rm-bp13t8tx0697ewx4wpo.mysql.rds.aliyuncs.com
MYSQL_PORT=3306
MYSQL_USER=chenyang
MYSQL_PASSWORD=mRA9ycdvj8NW71qG5Dnajq5
MYSQL_DATABASE=ai_terminal
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_CONCURRENT_WORKERS=10
EOF
```

**使用 .env 运行**:

```bash
docker run -d \
  --name translation-backend \
  -p 8013:8013 \
  -v /mnt/d/work/trans_excel:/app/data \
  --env-file .env \
  translation-backend:latest
```

---

## 🎯 Docker 分层架构

### Dockerfile 分层说明

```dockerfile
# Layer 1: 基础镜像 + 系统依赖（很少变化）
FROM python:3.10-slim as base
RUN apt-get install gcc g++ make ...

# Layer 2: Python 依赖（requirements.txt 不变就缓存）⭐
COPY requirements.txt .
RUN pip install -r requirements.txt

# Layer 3: 应用代码（经常变化）
COPY . .

# Layer 4: 运行时配置
CMD ["python3", "main.py"]
```

**缓存优化**:
- ✅ **Layer 2 缓存**: 如果 `requirements.txt` 不变，依赖安装层会被缓存
- ✅ **快速重建**: 代码修改后，重建只需 10-20 秒（跳过依赖安装）
- ✅ **避免重复安装**: 不会每次都重新安装 pandas、fastapi 等依赖

---

## 📊 环境变量配置

### 必需变量

| 变量 | 说明 | 示例 |
|-----|------|-----|
| `QWEN_API_KEY` | 通义千问 API 密钥 | `sk-xxx...` |
| `MYSQL_HOST` | MySQL 主机地址 | `rm-xxx.mysql.rds.aliyuncs.com` |
| `MYSQL_USER` | MySQL 用户名 | `chenyang` |
| `MYSQL_PASSWORD` | MySQL 密码 | `mRA9ycdvj8NW71qG5Dnajq5` |
| `MYSQL_DATABASE` | MySQL 数据库名 | `ai_terminal` |

### 可选变量

| 变量 | 默认值 | 说明 |
|-----|--------|-----|
| `MYSQL_PORT` | `3306` | MySQL 端口 |
| `ENVIRONMENT` | `production` | 运行环境 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `MAX_CONCURRENT_WORKERS` | `10` | 最大并发数 |
| `OPENAI_API_KEY` | - | OpenAI API 密钥（可选） |

---

## 🗂️ 数据卷挂载

### 推荐挂载方式

```bash
docker run -d \
  -v /mnt/d/work/trans_excel:/app/data \              # 数据目录
  -v /path/to/config:/app/config \                     # 配置文件（可选）
  -v /path/to/glossaries:/app/data/glossaries \        # 术语表（可选）
  translation-backend:latest
```

### 目录说明

| 容器内路径 | 用途 | 是否必需 |
|-----------|------|---------|
| `/app/data/input` | Excel 输入文件 | ✅ 必需 |
| `/app/data/output` | 翻译结果输出 | ✅ 必需 |
| `/app/data/glossaries` | 术语表文件 | 可选 |
| `/app/data/logs` | 日志文件 | 可选 |
| `/app/config` | 配置文件 | 可选 |

---

## 🔍 容器管理

### 查看日志

```bash
# 实时日志
docker logs -f translation-backend

# 最后 100 行
docker logs --tail 100 translation-backend
```

### 查看状态

```bash
# 容器状态
docker ps | grep translation-backend

# 健康检查
docker inspect --format='{{json .State.Health}}' translation-backend
```

### 进入容器

```bash
docker exec -it translation-backend bash

# 在容器内
python3 -c "from utils.config_manager import config_manager; print(config_manager.qwen_api_key)"
```

### 停止/重启

```bash
# 停止
docker stop translation-backend

# 重启
docker restart translation-backend

# 删除
docker rm -f translation-backend
```

---

## 🚀 常用命令

### 一键启动脚本

创建 `docker-run.sh`:

```bash
#!/bin/bash

docker run -d \
  --name translation-backend \
  --restart unless-stopped \
  -p 8013:8013 \
  -v /mnt/d/work/trans_excel:/app/data \
  --env-file .env \
  translation-backend:latest

echo "✅ 后端已启动"
echo "🌐 API地址: http://localhost:8013"
echo "📖 文档地址: http://localhost:8013/docs"
echo "📊 健康检查: http://localhost:8013/health"
```

使用:

```bash
chmod +x docker-run.sh
./docker-run.sh
```

---

## 🔧 开发模式

### 挂载代码（热重载）

```bash
docker run -d \
  --name translation-backend-dev \
  -p 8013:8013 \
  -v $(pwd):/app \                    # 挂载代码目录
  -v /mnt/d/work/trans_excel:/app/data \
  --env-file .env \
  translation-backend:latest
```

**说明**: 挂载代码目录后，修改代码会自动重载（uvicorn reload=True）

---

## 📈 性能优化

### 1. 限制资源

```bash
docker run -d \
  --cpus="2.0" \              # 限制 2 个 CPU
  --memory="2g" \             # 限制 2GB 内存
  translation-backend:latest
```

### 2. 多容器部署（负载均衡）

```bash
# 启动 3 个实例
for i in {1..3}; do
  docker run -d \
    --name translation-backend-$i \
    -p $((8012+i)):8013 \
    --env-file .env \
    translation-backend:latest
done

# 使用 Nginx 做负载均衡
```

---

## 🩺 健康检查

### 内置健康检查

Dockerfile 中已配置健康检查:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import httpx; httpx.get('http://localhost:8013/health', timeout=5.0)" || exit 1
```

### 手动检查

```bash
# 检查健康状态
curl http://localhost:8013/health

# 预期输出
{
  "status": "healthy",
  "config": {
    "max_chars_per_batch": 3000,
    "max_concurrent_workers": 10
  }
}
```

---

## 🐛 故障排除

### 问题1: 容器启动失败

```bash
# 查看详细日志
docker logs translation-backend

# 检查配置
docker exec translation-backend env | grep -E "QWEN|MYSQL"
```

### 问题2: 依赖安装失败

**原因**: requirements.txt 中的包需要编译，但缺少系统依赖

**解决**: Dockerfile 中已包含编译依赖（gcc、g++、make）

### 问题3: 数据文件找不到

**原因**: 数据卷未正确挂载

**解决**:
```bash
# 检查挂载
docker inspect translation-backend | grep -A 10 Mounts

# 确保挂载正确
-v /mnt/d/work/trans_excel:/app/data
```

### 问题4: 重建镜像慢

**原因**: 缓存未生效

**解决**:
```bash
# 检查构建日志
docker build -t translation-backend:latest . --progress=plain

# 确保 requirements.txt 未修改（会使用缓存 Layer 2）
# 如果修改了依赖，重建是正常的
```

---

## 📦 镜像管理

### 查看镜像

```bash
docker images | grep translation-backend
```

### 清理旧镜像

```bash
# 删除未使用的镜像
docker image prune -f

# 删除特定版本
docker rmi translation-backend:old-version
```

### 导出/导入镜像

```bash
# 导出
docker save translation-backend:latest | gzip > translation-backend.tar.gz

# 导入
docker load < translation-backend.tar.gz
```

---

## 🎉 最佳实践

### ✅ 推荐做法

1. **使用 .env 文件管理配置**
   - 不要在命令行暴露敏感信息
   - 便于版本控制（.env 加入 .gitignore）

2. **挂载数据目录**
   - 不要将数据打包到镜像
   - 容器重建不丢失数据

3. **设置重启策略**
   ```bash
   --restart unless-stopped
   ```

4. **使用健康检查**
   - 自动检测服务状态
   - 配合容器编排工具（k8s）

5. **分层构建**
   - 依赖层缓存，加快重建速度

### ❌ 避免做法

1. ❌ 不要在 Dockerfile 中硬编码敏感信息
2. ❌ 不要把大文件（Excel）打包到镜像
3. ❌ 不要每次都 `--no-cache` 构建
4. ❌ 不要忽略 .dockerignore（会导致镜像臃肿）

---

## 📚 相关文档

- [FastAPI 文档](http://localhost:8013/docs)
- [后端 API 参考](./API_REFERENCE.md)
- [配置说明](./docs/configuration_structure.md)

---

## 🆘 获取帮助

### 查看容器信息

```bash
# 完整信息
docker inspect translation-backend

# 环境变量
docker exec translation-backend env

# 进程列表
docker top translation-backend
```

### 测试 API

```bash
# 健康检查
curl http://localhost:8013/health

# 根路径
curl http://localhost:8013/

# API 文档
open http://localhost:8013/docs
```

---

**开始使用**: `docker build -t translation-backend . && docker run -d --name translation-backend -p 8013:8013 --env-file .env translation-backend` 🚀
