# 🐳 Docker 极简部署指南

## 🚀 一键启动

```bash
# 1. 构建镜像
./docker-start.sh --build

# 2. 运行容器 (完整版)
./docker-start.sh --run

# 3. 查看服务
open http://localhost:8000/docs
```

## 📋 快速命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `--build` | 构建镜像 | `./docker-start.sh --build` |
| `--run` | 运行容器 | `./docker-start.sh --run` |
| `--stop` | 停止容器 | `./docker-start.sh --stop` |
| `--logs` | 查看日志 | `./docker-start.sh --logs` |
| `--rebuild` | 重建并运行 | `./docker-start.sh --rebuild` |
| `--clean` | 清理所有资源 | `./docker-start.sh --clean` |

## 🔧 运行模式

### 完整模式 (默认)
```bash
./docker-start.sh --run --full
```
- 包含所有功能
- 支持数据库和翻译服务
- 完整的API接口

### 简化模式
```bash
./docker-start.sh --run --simple
```
- 基础翻译功能
- 轻量级启动
- 适合开发测试

### 最小模式
```bash
./docker-start.sh --run --minimal
```
- 只有基础API
- 最快启动速度
- 健康检查和系统信息

## ⚙️ 自定义配置

### 指定端口
```bash
./docker-start.sh --run --port 8080
```

### 指定容器名称
```bash
./docker-start.sh --run --name my-translator
```

### 环境变量配置
```bash
docker run -p 8000:8000 \
  -e DEBUG_MODE=true \
  -e LLM_API_KEY=your-api-key \
  -e OSS_ACCESS_KEY_ID=your-oss-key \
  -v $(pwd)/data:/app/data \
  translation-system
```

## 💾 数据持久化

容器会自动创建 `docker-data` 目录用于持久化存储：
```
docker-data/
├── translation.db    # SQLite数据库
├── logs/            # 日志文件
└── uploads/         # 上传文件
```

## 🔍 监控和调试

### 查看实时日志
```bash
./docker-start.sh --logs
```

### 进入容器
```bash
docker exec -it trans-system bash
```

### 健康检查
```bash
curl http://localhost:8000/health
```

## 🏗️ 构建优化

Dockerfile 采用多阶段构建，分层缓存依赖：

1. **基础层** - Python 3.10
2. **系统依赖层** - 构建工具
3. **Web框架层** - FastAPI, Uvicorn
4. **存储层** - 数据库和缓存
5. **数据处理层** - Pandas, NumPy
6. **AI服务层** - LLM和云服务
7. **应用层** - 业务代码

每层独立缓存，只有代码变更时才重建应用层。

## 🐛 故障排除

### 端口被占用
```bash
# 检查端口占用
lsof -i :8000

# 或更换端口
./docker-start.sh --run --port 8001
```

### 容器启动失败
```bash
# 查看详细日志
docker logs trans-system

# 重新构建
./docker-start.sh --rebuild
```

### 清理并重新开始
```bash
./docker-start.sh --clean
./docker-start.sh --build
./docker-start.sh --run
```

## 📊 资源使用

| 模式 | 内存使用 | 启动时间 | 功能完整度 |
|------|----------|----------|-----------|
| 最小模式 | ~50MB | 3s | 20% |
| 简化模式 | ~150MB | 8s | 60% |
| 完整模式 | ~300MB | 15s | 100% |

## 🌟 生产部署

### 后台运行
```bash
./docker-start.sh --run
# 容器已配置 --restart unless-stopped
```

### 负载均衡
```bash
# 运行多个实例
for i in {1..3}; do
  docker run -d --name trans-system-$i \
    -p $((8000+i)):8000 \
    translation-system
done
```

### 监控集成
```bash
# 配置监控
docker run -p 8000:8000 \
  -e ENABLE_METRICS=true \
  translation-system
```

## 💡 最佳实践

1. **开发环境** - 使用简化模式快速迭代
2. **测试环境** - 使用完整模式验证功能
3. **生产环境** - 配置外部数据库和监控
4. **数据备份** - 定期备份 docker-data 目录
5. **日志管理** - 配置日志轮转和收集

无需 docker-compose，一个命令搞定所有部署需求！🎉