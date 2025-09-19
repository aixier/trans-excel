# ================================
# 优化版本 - 使用预装科学计算包的镜像
# ================================

# 使用包含科学计算包的镜像 (预装numpy, pandas等)
FROM jupyter/scipy-notebook:python-3.10

# 切换到root用户安装系统依赖
USER root

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    JUPYTER_ENABLE_LAB=no \
    JUPYTER_TOKEN=disabled

# 数据库配置
ENV MYSQL_HOST=your-mysql-host \
    MYSQL_PORT=3306 \
    MYSQL_USER=your-mysql-user \
    MYSQL_PASSWORD=your-mysql-password \
    MYSQL_DATABASE=ai_terminal

# OSS配置
ENV OSS_ACCESS_KEY_ID=your-oss-access-key-id \
    OSS_ACCESS_KEY_SECRET=your-oss-access-key-secret \
    OSS_BUCKET_NAME=cms-mcp \
    OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com

# LLM配置
ENV LLM_PROVIDER=dashscope \
    LLM_API_KEY=your-llm-api-key \
    LLM_MODEL=qwen-plus \
    LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Redis缓存配置 (不使用Redis，设置为空值使用内存缓存)
ENV REDIS_HOST= \
    REDIS_PORT= \
    REDIS_PASSWORD= \
    REDIS_DB=

# 应用配置
ENV APP_NAME="游戏本地化智能翻译系统" \
    APP_VERSION=1.0.0 \
    DEBUG=true \
    DEBUG_MODE=true \
    SERVER_PORT=8000 \
    DEFAULT_BATCH_SIZE=3 \
    DEFAULT_MAX_CONCURRENT=10 \
    DEFAULT_MAX_ITERATIONS=5 \
    DEFAULT_REGION_CODE=na

# 只安装缺失的系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    default-mysql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY requirements.txt .

# 安装额外的Python依赖 (跳过已预装的)
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    sqlalchemy==2.0.23 \
    aiomysql==0.2.0 \
    openpyxl==3.1.2 \
    pydantic==2.5.0 \
    pydantic-settings==2.1.0 \
    redis==5.0.1 \
    aioredis==2.0.1 \
    oss2==2.18.4 \
    dashscope==1.14.1 \
    httpx==0.25.2 \
    openai==1.3.7 \
    python-dotenv==1.0.0 \
    python-multipart==0.0.6

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p logs temp uploads downloads data

# 使用现有的jovyan用户并设置权限
RUN chown -R jovyan:users /app

# 切换到jovyan用户 (jupyter镜像默认用户)
USER jovyan

# 只暴露翻译系统端口 (不暴露8888 Jupyter端口)
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/status || exit 1

# 覆盖Jupyter镜像的默认启动命令，只启动我们的翻译系统
ENTRYPOINT []
CMD ["python", "start.py"]