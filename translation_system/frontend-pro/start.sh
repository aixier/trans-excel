#!/bin/bash

echo "Starting Translation System Frontend..."

# 检查依赖是否安装
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    pnpm install --prefer-frozen-lockfile
fi

# 启动开发服务器
echo "Starting development server on http://localhost:5173"
pnpm dev --host 0.0.0.0 --port 5173