# ================================
# 简单版本 - 直接Docker构建和运行
# ================================

# 使用Python官方镜像
FROM python:3.10-slim

# 设置Python环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 安装系统依赖 (一次性安装所有)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    default-mysql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制所有requirements文件
COPY requirements*.txt ./

# 安装所有Python依赖
RUN pip install --no-cache-dir -r requirements-core.txt && \
    pip install --no-cache-dir -r requirements-services.txt && \
    pip install --no-cache-dir -r requirements-business.txt

# 设置默认端口
ENV SERVER_PORT=8000

# 复制应用代码（包括.env文件如果存在）
COPY . .

# 创建必要目录
RUN mkdir -p logs temp uploads downloads data

# 设置权限
RUN chown -R 1000:1000 /app

# 切换到非root用户
USER 1000

# 只暴露翻译系统端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/status || exit 1

# 启动命令
ENTRYPOINT []
CMD ["python", "start.py"]