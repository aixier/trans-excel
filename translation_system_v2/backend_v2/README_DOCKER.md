# 🐳 Backend V2 Docker 简单部署

**最简单的方式 - 2 条命令启动**

---

## ⚡ 快速开始

### 前置准备

确保配置文件存在（配置会打包到镜像）：
```bash
cd /mnt/d/work/trans_excel/translation_system_v2/backend_v2

# 检查配置文件
ls -l .env config/config.yaml
```

---

### 1. 构建镜像

```bash
docker build -t translation-backend .
```

**说明**:
- 配置文件（.env 和 config/*.yaml）会直接打包到镜像
- 利用分层缓存，第二次构建很快（~15秒）

---

### 2. 启动容器

```bash
docker run -d --name backend -p 8013:8013 translation-backend
```

**就这么简单！**

---

## 📋 完整命令（一行）

```bash
# 构建并启动
docker build -t translation-backend . && docker run -d --name backend -p 8013:8013 translation-backend
```

---

## 🔍 验证运行

```bash
# 查看日志
docker logs -f backend

# 健康检查
curl http://localhost:8013/health

# API 文档
open http://localhost:8013/docs
```

---

## 🗂️ 可选：挂载数据目录

如果需要持久化数据（输入/输出文件）：

```bash
docker run -d \
  --name backend \
  -p 8013:8013 \
  -v /mnt/d/work/trans_excel:/app/data \
  translation-backend
```

---

## 🔧 常用操作

```bash
# 重启
docker restart backend

# 停止
docker stop backend

# 删除
docker rm -f backend

# 重建
docker build -t translation-backend . && docker restart backend
```

---

## 📦 Dockerfile 分层优化

```dockerfile
Layer 1: python:3.10-slim        (基础镜像，缓存)
Layer 2: pip install requirements (依赖安装，缓存) ⭐
Layer 3: COPY . .                 (代码复制，经常变)
Layer 4: CMD python3 main.py      (启动命令)
```

**效果**:
- ✅ 首次构建: ~3分钟
- ✅ 代码修改后: ~15秒（跳过依赖安装）
- ✅ 配置内置: 无需传递环境变量

---

## 🎯 设计理念

### ✅ 简单至上
- 2条命令启动
- 配置打包到镜像
- 无需复杂参数

### ✅ 分层缓存
- requirements.txt 不变 = 依赖层缓存
- 重建速度快 10 倍

### ✅ 开箱即用
- `python3 main.py` 自动启动
- 健康检查内置

---

## 📝 注意事项

**配置修改后需要重建镜像**:
```bash
# 修改 .env 或 config.yaml 后
docker build -t translation-backend .
docker restart backend
```

**如果不想重建，可以挂载配置**:
```bash
docker run -d \
  --name backend \
  -p 8013:8013 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/.env:/app/.env \
  translation-backend
```

---

**开始使用**:
```bash
docker build -t translation-backend . && docker run -d --name backend -p 8013:8013 translation-backend
```

🚀
