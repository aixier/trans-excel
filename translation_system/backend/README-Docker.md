# Docker 部署指南

## 🚀 快速开始

```bash
# 构建镜像 (使用预装科学计算包的优化镜像)
cd /mnt/d/work/trans_excel/translation_system/backend
docker build -t translation-system .

# 运行容器
docker run -p 8000:8000 translation-system
```

## 🌐 访问服务

- **服务地址**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 💾 数据持久化

```bash
# 挂载数据目录
docker run -p 8000:8000 -v $(pwd)/data:/app/data translation-system
```

## ⚙️ 环境变量配置

### 基础运行 (使用默认演示配置)
```bash
docker run -p 8000:8000 translation-system
```

### 完整配置 (生产环境)
```bash
docker run -p 8000:8000 \
  -e MYSQL_HOST=your-db-host \
  -e MYSQL_PASSWORD=your-db-password \
  -e OSS_ACCESS_KEY_ID=your-oss-key \
  -e OSS_ACCESS_KEY_SECRET=your-oss-secret \
  -e OSS_BUCKET_NAME=your-bucket \
  -e OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com \
  -e LLM_API_KEY=your-llm-api-key \
  translation-system
```

### 内置配置说明

容器已预配置生产环境参数，可直接运行：

| 配置项 | 默认值 |
|--------|--------|
| **数据库** | 阿里云RDS MySQL |
| **OSS存储** | 阿里云OSS (cms-mcp bucket) |
| **AI模型** | 通义千问Plus |
| **缓存** | 内存缓存 (无Redis) |
| **调试模式** | 开启 |

## 🔄 后台运行

```bash
docker run -d --name translation-system -p 8000:8000 translation-system
```

## ✨ 优化特性

- **预装科学计算包**: 基于 `jupyter/scipy-notebook`，预装pandas/numpy
- **避免编译问题**: 无需构建C扩展，大幅减少构建时间
- **网络友好**: 减少下载量，适合网络受限环境
- **完整功能**: 保留所有翻译系统功能
- **单端口服务**: 只启动翻译系统(8000端口)，禁用Jupyter服务(8888端口)

## 🔍 端口说明

- **8000端口**: 翻译系统API服务 (我们使用的)
- **8888端口**: Jupyter服务已禁用 (基础镜像自带，已关闭)