# Docker 简单构建和运行指南

## 构建Docker镜像
```bash
docker build -t trans_excel:latest .
```
**注意**: .env文件会被直接打包到镜像中，无需运行时指定

## 运行容器（极简版）
```bash
docker run -d --name trans_excel -p 8000:8000 trans_excel:latest
```

## 运行容器（带数据持久化）
```bash
docker run -d \
  --name trans_excel \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/temp:/app/temp \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/downloads:/app/downloads \
  trans_excel:latest
```

## Windows环境运行
```cmd
docker run -d ^
  --name trans_excel ^
  -p 8000:8000 ^
  -v %cd%/logs:/app/logs ^
  -v %cd%/temp:/app/temp ^
  -v %cd%/uploads:/app/uploads ^
  -v %cd%/downloads:/app/downloads ^
  trans_excel:latest
```

## 查看日志
```bash
docker logs trans_excel
docker logs -f trans_excel  # 实时查看
```

## 停止和删除容器
```bash
docker stop trans_excel
docker rm trans_excel
```

## 重新构建（不使用缓存）
```bash
docker build --no-cache -t trans_excel:latest .
```

## 一键重启（停止、删除、构建、运行）
```bash
# Linux/Mac
docker stop trans_excel && docker rm trans_excel && docker build -t trans_excel:latest . && docker run -d --name trans_excel -p 8000:8000 trans_excel:latest

# Windows
docker stop trans_excel & docker rm trans_excel & docker build -t trans_excel:latest . & docker run -d --name trans_excel -p 8000:8000 trans_excel:latest
```

## 健康检查
```bash
curl http://localhost:8000/api/health/status
```

## 注意事项
1. 确保 `.env` 文件存在且包含所有必要的配置
2. 确保端口 8000 未被占用
3. 日志和临时文件会保存在宿主机的对应目录中