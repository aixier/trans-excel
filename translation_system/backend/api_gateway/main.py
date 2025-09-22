"""
FastAPI主应用程序
基于架构文档的API网关实现
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import uuid

from config.settings import settings
from database.connection import get_async_engine, AsyncSession
from .routers import translation, project, health, terminology, workspace
from .models.task import ErrorResponse, ValidationErrorResponse


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 Translation System API Gateway 启动")

    # 初始化数据库连接
    try:
        engine = get_async_engine()
        logger.info("✅ 数据库连接初始化成功")
    except Exception as e:
        logger.error(f"❌ 数据库连接初始化失败: {e}")
        raise

    yield

    logger.info("🛑 Translation System API Gateway 关闭")


# 创建FastAPI应用
app = FastAPI(
    title="Translation System API Gateway",
    description="游戏本地化翻译系统 API 网关",
    version="1.0.0",
    docs_url="/docs" if settings.debug_mode else None,
    redoc_url="/redoc" if settings.debug_mode else None,
    lifespan=lifespan
)


# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 安全中间件
if not settings.debug_mode:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.example.com"]
    )


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    logger.info(f"🔄 [{request_id}] {request.method} {request.url.path}")

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"✅ [{request_id}] {response.status_code} | "
        f"{process_time:.3f}s | {request.client.host if request.client else 'unknown'}"
    )

    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id

    return response


# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="http_error",
            message=exc.detail,
            details={"status_code": exc.status_code}
        ).dict()
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """值错误异常处理"""
    logger.error(f"ValueError: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="validation_error",
            message=str(exc)
        ).dict()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_server_error",
            message="Internal server error occurred"
        ).dict()
    )


# 注册路由
app.include_router(
    health.router,
    prefix="/api/health",
    tags=["健康检查"]
)

app.include_router(
    translation.router,
    prefix="/api/translation",
    tags=["翻译服务"]
)

app.include_router(
    project.router,
    prefix="/api/project",
    tags=["项目管理"]
)

app.include_router(
    terminology.router,
    prefix="/api/terminology",
    tags=["术语管理"]
)

app.include_router(
    workspace.router,
    prefix="/api/workspace",
    tags=["翻译工作台"]
)


# 根路径
@app.get("/")
async def root():
    """根路径信息"""
    return {
        "service": "Translation System API Gateway",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if settings.debug_mode else None
    }


# 系统信息端点
@app.get("/api/info")
async def system_info():
    """系统信息"""
    return {
        "service": "Translation System",
        "version": "1.0.0",
        "environment": "development" if settings.debug_mode else "production",
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug_mode,
        log_level="info"
    )