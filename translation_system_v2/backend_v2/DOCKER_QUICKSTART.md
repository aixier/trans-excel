# 🚀 Docker 快速启动卡片

## 最简单的方式（2 条命令）

```bash
cd /mnt/d/work/trans_excel/translation_system_v2/backend_v2

# 构建
docker build -t translation-backend .

# 启动
docker run -d --name backend -p 8013:8013 translation-backend
```

## 一行命令

```bash
docker build -t translation-backend . && docker run -d --name backend -p 8013:8013 translation-backend
```

## 验证

```bash
curl http://localhost:8013/health
```

## 常用命令

| 操作 | 命令 |
|-----|------|
| 查看日志 | `docker logs -f backend` |
| 重启 | `docker restart backend` |
| 停止 | `docker stop backend` |
| 删除 | `docker rm -f backend` |

## 分层缓存说明

- ✅ **首次构建**: ~3分钟
- ⚡ **代码修改后**: ~15秒（依赖层缓存）
- 📦 **镜像大小**: ~500MB

## 目录结构

```
backend_v2/
├── Dockerfile          ← 分层优化构建文件
├── .dockerignore       ← 排除不必要文件
├── .env                ← 配置（打包到镜像）
├── config/             ← 配置文件（打包到镜像）
└── requirements.txt    ← Python依赖（缓存层）
```

---

**详细文档**: `cat README_DOCKER.md`
