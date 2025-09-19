#!/bin/bash
# 本地运行脚本 - 游戏本地化翻译系统

echo "🎮 游戏本地化翻译系统 - 本地环境启动"
echo "=================================================="

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行："
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install fastapi uvicorn pydantic-settings python-dotenv"
    exit 1
fi

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "❌ 配置文件 .env 不存在，请先复制："
    echo "   cp .env.example .env"
    echo "   然后编辑 .env 文件配置数据库和API密钥"
    exit 1
fi

echo "✅ 环境检查通过"
echo

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 显示启动选项
echo "请选择启动模式："
echo "1) 基础测试服务器 (不需要数据库)"
echo "2) 完整系统服务器 (需要数据库和API配置)"
echo "3) 运行基础功能测试"
echo

read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo "🚀 启动基础测试服务器..."
        echo "服务地址: http://localhost:8000"
        echo "API文档: http://localhost:8000/docs"
        echo "按 Ctrl+C 停止服务器"
        echo
        uvicorn simple_server:app --host 0.0.0.0 --port 8000 --reload
        ;;
    2)
        echo "🚀 启动完整系统服务器..."
        echo "注意: 需要确保数据库连接和API配置正确"
        echo "服务地址: http://localhost:8000"
        echo "API文档: http://localhost:8000/docs"
        echo "按 Ctrl+C 停止服务器"
        echo
        python start.py
        ;;
    3)
        echo "🧪 运行基础功能测试..."
        python test_basic.py
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac