"""Translation System Backend V2 - 主应用入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from utils.logger import setup_logger
from utils.config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=" * 60)
    logger.info("Translation System Backend V2 启动中...")
    logger.info(f"环境: {config.env}")
    logger.info(f"API地址: http://{config.get('api.host')}:{config.get('api.port')}")
    logger.info(f"文档地址: http://{config.get('api.host')}:{config.get('api.port')}{config.get('api.docs_url')}")
    logger.info("=" * 60)
    
    yield
    
    # 关闭时执行
    logger.info("Translation System Backend V2 关闭中...")
    logger.info("清理资源...")
    logger.info("应用已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=config.get('api.title', 'Translation System Backend V2'),
    description=config.get('api.description', 'Excel批量翻译管理系统API'),
    version=config.get('api.version', '2.0.0'),
    docs_url=config.get('api.docs_url', '/docs'),
    redoc_url=config.get('api.redoc_url', '/redoc'),
    lifespan=lifespan
)

# 配置CORS
cors_origins = config.get('cors_origins', ["*"])
if config.is_development:
    cors_origins = config.get('development.cors_origins', ["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "Translation System Backend V2",
        "version": config.get('api.version'),
        "environment": config.env
    }


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Translation System Backend V2",
        "version": config.get('api.version'),
        "docs": config.get('api.docs_url'),
        "redoc": config.get('api.redoc_url')
    }


# API路由注册（后续添加）
# from api import analyze_api, task_api, execute_api, monitor_api, websocket_api
# app.include_router(analyze_api.router, prefix="/api/analyze", tags=["analyze"])
# app.include_router(task_api.router, prefix="/api/task", tags=["task"])
# app.include_router(execute_api.router, prefix="/api/execute", tags=["execute"])
# app.include_router(monitor_api.router, prefix="/api/monitor", tags=["monitor"])
# app.include_router(websocket_api.router, prefix="/ws", tags=["websocket"])


if __name__ == "__main__":
    import uvicorn
    
    # 从配置获取运行参数
    host = config.get('api.host', '0.0.0.0')
    port = config.get('api.port', 8013)
    reload = config.get('development.reload', True) if config.is_development else False
    
    # 运行应用
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload
    )
