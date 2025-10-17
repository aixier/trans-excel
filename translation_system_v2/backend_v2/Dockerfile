# ============================================
# Stage 1: 基础环境 + 系统依赖
# ============================================
FROM python:3.10-slim as base

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（编译 Python 包需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /app


# ============================================
# Stage 2: Python 依赖安装（缓存层）
# ============================================
FROM base as dependencies

# 先复制 requirements.txt（单独一层，便于缓存）
COPY requirements.txt .

# 安装 Python 依赖（这层会被缓存，除非 requirements.txt 改变）
RUN pip install --no-cache-dir -r requirements.txt


# ============================================
# Stage 3: 应用代码
# ============================================
FROM dependencies as application

# 复制应用代码
COPY . .

# 创建必要的数据目录
RUN mkdir -p /app/data/input \
    /app/data/output \
    /app/data/glossaries \
    /app/data/logs \
    /app/data/cache

# 设置文件权限
RUN chmod -R 755 /app

# 设置默认环境变量（可通过 docker run -e 覆盖）
ENV PYTHONPATH=/app \
    DATA_PATH=/app/data


# ============================================
# Stage 4: 运行时配置
# ============================================
FROM application as runtime

# 暴露端口
EXPOSE 8013

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import httpx; httpx.get('http://localhost:8013/health', timeout=5.0)" || exit 1

# 启动命令
CMD ["python3", "main.py"]
