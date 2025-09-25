# ================================
# 生产版本 - 使用Jupyter科学计算栈镜像
# ================================

# 使用Jupyter科学计算镜像（预装pandas、numpy、scipy、matplotlib等所有数据科学包）
# 2024年最新版本，从quay.io拉取
FROM quay.io/jupyter/scipy-notebook:python-3.11

# 切换到root用户进行系统设置
USER root

# 设置Python环境变量和UTF-8编码
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1 \
    # UTF-8 locale settings
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    # 禁用Jupyter相关功能，只作为Python运行环境
    JUPYTER_ENABLE_LAB=no \
    JUPYTER_TOKEN=disabled \
    DEBIAN_FRONTEND=noninteractive

# 只需要安装curl用于健康检查（其他都已预装）
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY requirements*.txt ./

# 安装额外的Python依赖（跳过已预装的pandas、numpy、scipy等）
# 使用mamba（Jupyter镜像中的快速包管理器）安装conda包
RUN mamba install -y -c conda-forge \
    openpyxl \
    && mamba clean -afy

# 安装其余Python Web框架和服务依赖
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    sqlalchemy==2.0.23 \
    aiomysql==0.2.0 \
    pydantic==2.5.0 \
    pydantic-settings==2.1.0 \
    redis==5.0.1 \
    aioredis==2.0.1 \
    oss2==2.18.4 \
    dashscope==1.14.1 \
    httpx==0.25.2 \
    openai==1.35.0 \
    python-dotenv==1.0.0 \
    python-multipart==0.0.6

# 设置默认端口
ENV SERVER_PORT=8000

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p logs temp uploads downloads data

# 设置权限（Jupyter镜像已有jovyan用户，uid=1000）
RUN chown -R 1000:1000 /app

# 切换到Jupyter镜像的默认用户
USER 1000

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/status || exit 1

# 覆盖Jupyter的默认启动命令，只启动我们的FastAPI应用
ENTRYPOINT []
CMD ["python", "start.py"]