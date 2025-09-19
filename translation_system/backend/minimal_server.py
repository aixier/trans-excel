#!/usr/bin/env python3
"""
最小化API服务器 - 完全独立运行
不依赖任何项目配置和数据库
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import os

# 创建FastAPI应用
app = FastAPI(
    title="Translation System Minimal Server",
    description="游戏本地化翻译系统最小服务器",
    version="1.0.0-minimal",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 根路径
@app.get("/")
async def root():
    """根路径信息"""
    return {
        "service": "Translation System Minimal Server",
        "version": "1.0.0-minimal",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "🎮 游戏本地化翻译系统最小服务器",
        "docs": "/docs"
    }

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "translation-system-minimal",
        "version": "1.0.0-minimal"
    }

# 系统信息
@app.get("/api/info")
async def system_info():
    """系统信息"""
    return {
        "service": "Translation System Minimal",
        "version": "1.0.0-minimal",
        "config": {
            "app_name": "游戏本地化翻译系统",
            "debug_mode": True,
            "server_port": 8000,
            "environment": "minimal"
        },
        "supported_languages": ["pt", "th", "ind"],
        "supported_regions": ["na", "sa", "eu", "me", "as"],
        "features": [
            "基础API服务",
            "健康检查",
            "系统信息查询",
            "API文档"
        ]
    }

# 测试接口
@app.get("/api/test/ping")
async def test_ping():
    """测试连接"""
    return {
        "status": "success",
        "message": "pong",
        "timestamp": datetime.utcnow().isoformat()
    }

def main():
    """启动服务器"""
    port = int(os.getenv("SERVER_PORT", 8000))

    print("🎮 游戏本地化翻译系统 - 最小服务器")
    print("=" * 60)
    print(f"🌐 服务地址: http://localhost:{port}")
    print(f"📚 API文档: http://localhost:{port}/docs")
    print(f"🔍 健康检查: http://localhost:{port}/health")
    print(f"ℹ️ 系统信息: http://localhost:{port}/api/info")
    print("=" * 60)
    print("按 Ctrl+C 停止服务器")
    print()

    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n⏹️ 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

if __name__ == "__main__":
    main()