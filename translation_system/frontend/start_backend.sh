#!/bin/bash

# 游戏本地化翻译系统 - 后端启动脚本

echo "🎮 启动游戏本地化翻译系统后端服务..."
echo "=" * 60

# 切换到后端目录
cd ../backend

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3未安装"
    exit 1
fi

# 启动最小化服务器
echo "📦 使用最小化服务器模式（无需数据库）"
echo "🌐 服务将运行在: http://localhost:8001"
echo ""

# 设置端口并启动
export SERVER_PORT=8001
python3 minimal_server.py

echo "👋 服务已停止"