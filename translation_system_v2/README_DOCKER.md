# Excel翻译系统 V2 - Docker手动部署

## 🐳 手动构建和运行

### 1. 构建镜像

```bash
docker build -t excel-translation:v2 .
```

### 2. 运行容器

```bash
# 极简运行（推荐）
docker run -d --name excel-translation -p 8080:80 excel-translation:v2

# 或者指定端口
docker run -d --name excel-translation -p 3000:80 excel-translation:v2
```

### 3. 访问系统

打开浏览器访问: **http://localhost:8080**

## 📁 目录结构

```
translation_system/
├── Dockerfile           # Docker镜像定义
├── .dockerignore       # Docker构建忽略文件
├── backend_v2/         # 后端代码
├── frontend_v2/        # 前端代码
│   └── nginx.conf      # Nginx配置文件
└── data/               # 数据目录（运行时创建）
    ├── uploads/        # 上传文件
    ├── exports/        # 导出文件
    └── logs/           # 日志文件
```

## 🔧 配置说明

### 配置文件

所有配置都在 `backend_v2/config/config.yaml` 中管理：
- LLM提供商配置（OpenAI、Qwen等）
- API密钥和端点
- 系统参数（超时、并发数等）

### 端口映射

- **8080** → 80 (Web访问端口，可自定义)

## 📋 常用命令

```bash
# 查看容器状态
docker ps -a | grep excel-translation

# 查看实时日志
docker logs -f excel-translation

# 查看最近100行日志
docker logs --tail 100 excel-translation

# 进入容器
docker exec -it excel-translation bash

# 停止容器
docker stop excel-translation

# 启动容器
docker start excel-translation

# 重启容器
docker restart excel-translation

# 删除容器
docker rm -f excel-translation

# 删除镜像
docker rmi excel-translation:v2
```

## 🔍 健康检查

```bash
# 检查服务状态
curl http://localhost:8080

# 检查API状态
curl http://localhost:8080/api/health
```

## ⚙️ 性能优化

### 资源限制

```bash
# 限制CPU和内存
docker run -d --name excel-translation -p 8080:80 --cpus="2" --memory="2g" excel-translation:v2
```

### 日志管理

```bash
# 限制日志大小
docker run -d --name excel-translation -p 8080:80 --log-opt max-size=10m --log-opt max-file=3 excel-translation:v2
```

## 🐛 故障排除

### 1. 容器无法启动

```bash
# 查看错误日志
docker logs excel-translation

# 常见原因：
# - 端口被占用：更改 -p 8080:80 为其他端口
# - 权限问题：确保有docker权限
```

### 2. 无法访问Web界面

```bash
# 检查容器是否运行
docker ps | grep excel-translation

# 检查端口绑定
netstat -tlnp | grep 8080

# 检查防火墙
sudo ufw status
```

### 3. API调用失败

```bash
# 进入容器检查后端
docker exec -it excel-translation bash
cd /app/backend_v2
python -m uvicorn main:app --reload
```

### 4. 文件上传失败

```bash
# 检查权限
docker exec -it excel-translation ls -la /app/uploads

# 修复权限
docker exec -it excel-translation chmod 777 /app/uploads
```

## 🔄 更新部署

```bash
# 1. 停止并删除旧容器
docker stop excel-translation
docker rm excel-translation

# 2. 删除旧镜像
docker rmi excel-translation:v2

# 3. 重新构建
docker build -t excel-translation:v2 .

# 4. 运行新容器
docker run -d --name excel-translation -p 8080:80 excel-translation:v2
```

## 🌐 生产环境建议

1. **使用HTTPS**
   - 在Nginx前添加SSL证书
   - 或使用反向代理（如Traefik）

2. **数据备份**
   ```bash
   # 备份数据
   tar -czf backup_$(date +%Y%m%d).tar.gz data/
   ```

3. **监控**
   - 使用docker stats监控资源
   - 配置日志收集（如ELK）

4. **安全**
   - 不要在镜像中硬编码API密钥
   - 使用secrets管理敏感信息
   - 定期更新基础镜像

## 📊 镜像信息

```bash
# 查看镜像大小
docker images excel-translation:v2

# 预期大小：约 300-400MB
# 包含：Python 3.10 + Nginx + 依赖包
```

## 🎯 特点

- ✅ **手动构建** - 完全手动控制构建和运行过程
- ✅ **单一镜像** - 前后端集成在一个Docker镜像中
- ✅ **进程管理** - 使用Supervisor管理多进程
- ✅ **数据持久** - 支持数据卷挂载
- ✅ **健康检查** - 内置健康检查机制
- ✅ **易于维护** - 清晰的日志和命令

---

**版本**: 2.0.0
**更新日期**: 2025-01-20