# Excel翻译系统 V2 - 极简单一镜像
FROM python:3.10-slim

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y nginx supervisor curl && \
    rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制后端依赖并安装
COPY backend_v2/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# 复制应用代码（包含config/config.yaml配置文件）
COPY backend_v2/ ./backend_v2/
COPY frontend_v2/ /usr/share/nginx/html/

# 复制配置文件
COPY frontend_v2/nginx.conf /etc/nginx/sites-available/default

# 创建必要目录和权限
RUN mkdir -p /app/uploads /app/exports /app/logs && \
    chmod -R 777 /app/uploads /app/exports /app/logs && \
    rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/

# 创建Supervisor配置
RUN echo '[supervisord]\n\
nodaemon=true\n\
logfile=/app/logs/supervisord.log\n\
\n\
[program:nginx]\n\
command=nginx -g "daemon off;"\n\
autostart=true\n\
autorestart=true\n\
stdout_logfile=/app/logs/nginx_stdout.log\n\
stderr_logfile=/app/logs/nginx_stderr.log\n\
\n\
[program:backend]\n\
command=python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4\n\
directory=/app/backend_v2\n\
autostart=true\n\
autorestart=true\n\
environment=PYTHONPATH="/app"\n\
stdout_logfile=/app/logs/backend_stdout.log\n\
stderr_logfile=/app/logs/backend_stderr.log\n\
' > /etc/supervisor/conf.d/app.conf

# 设置环境变量
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# 启动命令
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]