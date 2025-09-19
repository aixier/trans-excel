#!/usr/bin/env python3
"""
简化的API服务器 - 用于测试基础功能
不依赖数据库和外部服务
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
from config.settings import settings

# 创建FastAPI应用
app = FastAPI(
    title="Translation System Test Server",
    description="游戏本地化翻译系统测试服务器",
    version="1.0.0-test",
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
        "service": "Translation System Test Server",
        "version": "1.0.0-test",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "🎮 游戏本地化翻译系统测试服务器",
        "docs": "/docs"
    }

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "translation-system-test",
        "version": "1.0.0-test"
    }

# 系统信息
@app.get("/api/info")
async def system_info():
    """系统信息"""
    return {
        "service": "Translation System Test",
        "version": "1.0.0-test",
        "config": {
            "app_name": settings.app_name,
            "debug_mode": settings.debug_mode,
            "server_port": settings.server_port,
            "default_batch_size": settings.default_batch_size,
            "default_max_concurrent": settings.default_max_concurrent
        },
        "supported_languages": ["pt", "th", "ind"],
        "supported_regions": ["na", "sa", "eu", "me", "as"],
        "features": [
            "Excel文件翻译",
            "项目版本管理",
            "批量并发处理",
            "迭代翻译优化",
            "术语管理",
            "区域化本地化",
            "占位符保护"
        ]
    }

# 测试配置接口
@app.get("/api/test/config")
async def test_config():
    """测试配置信息"""
    try:
        return {
            "status": "success",
            "config_loaded": True,
            "app_name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug_mode,
            "database_host": settings.mysql_host,
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置加载失败: {str(e)}")

# 模拟翻译状态接口
@app.get("/api/test/translation/status")
async def mock_translation_status():
    """模拟翻译状态"""
    return {
        "task_id": "test-task-123",
        "status": "translating",
        "progress": {
            "total_rows": 100,
            "translated_rows": 65,
            "current_iteration": 2,
            "max_iterations": 5,
            "completion_percentage": 65.0
        },
        "statistics": {
            "total_api_calls": 22,
            "total_tokens_used": 8500,
            "total_cost": 0.45
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# 错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

def main():
    """启动服务器"""
    print("🎮 游戏本地化翻译系统 - 测试服务器")
    print("=" * 60)
    print(f"🌐 服务地址: http://localhost:{settings.server_port}")
    print(f"📚 API文档: http://localhost:{settings.server_port}/docs")
    print(f"🔍 健康检查: http://localhost:{settings.server_port}/health")
    print(f"ℹ️ 系统信息: http://localhost:{settings.server_port}/api/info")
    print("=" * 60)
    print("按 Ctrl+C 停止服务器")
    print()

    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=settings.server_port,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n⏹️ 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()