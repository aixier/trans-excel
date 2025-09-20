#!/usr/bin/env python3
"""
最小化启动脚本 - 跳过Excel依赖，只启动API框架
用于验证完整系统架构
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_minimal_app():
    """创建最小化的FastAPI应用"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from datetime import datetime

    app = FastAPI(
        title="Translation System - Minimal Mode",
        description="游戏本地化翻译系统 - 最小化模式",
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
        return {
            "service": "Translation System - Minimal Mode",
            "version": "1.0.0-minimal",
            "status": "running",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "🎮 游戏本地化翻译系统 - 最小化模式",
            "docs": "/docs",
            "note": "Excel功能暂时禁用，仅测试API架构"
        }

    # 健康检查
    @app.get("/api/health/ping")
    async def health_ping():
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "translation-system-minimal"
        }

    # 系统信息
    @app.get("/api/info")
    async def system_info():
        return {
            "service": "Translation System - Minimal Mode",
            "version": "1.0.0-minimal",
            "config": {
                "app_name": settings.app_name,
                "debug_mode": settings.debug_mode,
                "server_port": settings.server_port,
                "llm_provider": settings.llm_provider,
                "llm_configured": bool(settings.llm_api_key and settings.llm_api_key != "sk-demo-api-key"),
                "oss_configured": bool(settings.oss_access_key_id and "XXXX" not in settings.oss_access_key_id)
            },
            "supported_languages": ["pt", "th", "ind"],
            "supported_regions": ["na", "sa", "eu", "me", "as"],
            "features": [
                "API网关架构",
                "配置管理系统",
                "健康检查服务",
                "系统信息查询"
            ],
            "disabled_features": [
                "Excel文件处理",
                "数据库连接",
                "实际翻译功能"
            ]
        }

    # 模拟翻译状态 (用于API架构测试)
    @app.get("/api/translation/demo/status")
    async def demo_translation_status():
        return {
            "task_id": "demo-task-12345",
            "status": "completed",
            "progress": {
                "total_rows": 100,
                "translated_rows": 100,
                "current_iteration": 3,
                "max_iterations": 5,
                "completion_percentage": 100.0
            },
            "statistics": {
                "total_api_calls": 35,
                "total_tokens_used": 12500,
                "total_cost": 0.85
            },
            "timestamp": datetime.utcnow().isoformat(),
            "note": "这是演示数据，用于API架构测试"
        }

    # 配置测试接口
    @app.get("/api/test/config")
    async def test_config():
        return {
            "status": "success",
            "config_loaded": True,
            "database": {
                "host": settings.mysql_host,
                "database": settings.mysql_database,
                "status": "configured"
            },
            "llm": {
                "provider": settings.llm_provider,
                "model": settings.llm_model,
                "api_key_configured": bool(settings.llm_api_key and settings.llm_api_key != "sk-demo-api-key"),
                "status": "configured" if settings.llm_api_key else "not_configured"
            },
            "oss": {
                "bucket": settings.oss_bucket_name,
                "endpoint": settings.oss_endpoint,
                "access_key_configured": bool(settings.oss_access_key_id and "XXXX" not in settings.oss_access_key_id),
                "status": "configured" if settings.oss_access_key_id else "not_configured"
            }
        }

    # 错误处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": str(exc),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    return app


async def main():
    """主函数"""
    try:
        # 创建必要目录
        directories = ["logs", "temp", "uploads", "downloads"]
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)

        logger.info("🚀 翻译系统启动 - 最小化模式")
        logger.info("⚙️ 验证配置...")

        # 验证配置
        logger.info(f"   App Name: {settings.app_name}")
        logger.info(f"   Server Port: {settings.server_port}")
        logger.info(f"   LLM Provider: {settings.llm_provider}")

        if settings.llm_api_key and settings.llm_api_key != "sk-demo-api-key":
            logger.info("✅ LLM API密钥已配置")
        else:
            logger.warning("⚠️ LLM API密钥未配置")

        if settings.oss_access_key_id and "XXXX" not in settings.oss_access_key_id:
            logger.info("✅ OSS存储配置已完整")
        else:
            logger.warning("⚠️ OSS存储配置未完整")

        # 创建应用
        app = create_minimal_app()

        # 显示系统信息
        logger.info("=" * 60)
        logger.info("🎮 游戏本地化翻译系统 - 最小化模式")
        logger.info(f"📡 服务地址: http://0.0.0.0:{settings.server_port}")
        logger.info(f"📚 API文档: http://0.0.0.0:{settings.server_port}/docs")
        logger.info(f"🔧 调试模式: {settings.debug_mode}")
        logger.info(f"🌍 支持语言: pt, th, ind")
        logger.info(f"🗺️ 支持地区: na, sa, eu, me, as")
        logger.info("⚠️ 注意: Excel和数据库功能已禁用，仅验证API架构")
        logger.info("=" * 60)

        # 启动服务器
        import uvicorn
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=settings.server_port,
            reload=settings.debug_mode,
            log_level="info",
            access_log=True
        )

        server = uvicorn.Server(config)
        await server.serve()

    except KeyboardInterrupt:
        logger.info("⏹️ 接收到停止信号，正在关闭系统...")
    except Exception as e:
        logger.error(f"❌ 系统运行错误: {e}")
        sys.exit(1)
    finally:
        logger.info("👋 系统已关闭")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ 程序被用户终止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)