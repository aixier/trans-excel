"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.analyze_api import router as analyze_router
from api.task_api import router as task_router
from api.execute_api import router as execute_router
from api.monitor_api import router as monitor_router
from api.download_api import router as download_router
# 禁用持久化服务 - 改为纯内存运行
# from api.log_api import router as log_router
# from api.resume_api import router as resume_router
# from api.database_api import router as database_router
from api.websocket_api import router as websocket_router
from api.pool_monitor_api import router as pool_monitor_router
from utils.config_manager import config_manager
# 禁用持久化服务 - 改为纯内存运行
# from services.monitor.performance_monitor import performance_monitor
# from services.logging.log_persister import log_persister
# from database.mysql_connector import MySQLConnector
import asyncio
from fastapi import Request
import time

# Global instances
# 禁用持久化服务 - 改为纯内存运行
# mysql_connector = MySQLConnector()


# Configure logging
logging.basicConfig(
    level=getattr(logging, config_manager.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Translation System Backend V2",
    description="Excel-based translation task management system",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config_manager.get('api.cors_origins', ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analyze_router)
app.include_router(task_router)
app.include_router(execute_router)
app.include_router(monitor_router)
app.include_router(download_router)
# 禁用持久化服务 - 改为纯内存运行
# app.include_router(log_router)
# app.include_router(resume_router)
app.include_router(websocket_router)
app.include_router(pool_monitor_router)
# 禁用持久化服务 - 改为纯内存运行
# app.include_router(database_router)


# HTTP request logging middleware disabled for performance
# Logs are now only written to files, not database
# Uncomment if you need HTTP request logging to files

# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     """Log all HTTP requests (disabled for performance)."""
#     start_time = time.time()
#     response = await call_next(request)
#     duration = (time.time() - start_time) * 1000
#
#     # Only log slow requests or errors
#     if duration > 1000 or response.status_code >= 400:
#         logger.warning(f"{request.method} {request.url.path} - {response.status_code} ({duration:.2f}ms)")
#
#     return response


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Translation System Backend V2",
        "version": "2.0.0",
        "status": "running",
        "endpoints": [
            "/api/analyze/upload",
            "/api/tasks/split",
            "/api/tasks/export/{session_id}",
            "/api/execute/start",
            "/api/execute/stop/{session_id}",
            "/api/monitor/status/{session_id}",
            "/api/monitor/dataframe/{session_id}",
            "/api/download/{session_id}",
            "/api/download/{session_id}/info",
            "/api/download/{session_id}/summary",
            "/docs"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "config": {
            "max_chars_per_batch": config_manager.max_chars_per_batch,
            "max_concurrent_workers": config_manager.max_concurrent_workers
        }
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("Starting Translation System Backend V2 - Memory Only Mode")
    logger.info(f"Max chars per batch: {config_manager.max_chars_per_batch}")
    logger.info(f"Max concurrent workers: {config_manager.max_concurrent_workers}")
    logger.info("Persistence disabled - running in memory-only mode")

    # 禁用持久化服务 - 改为纯内存运行
    # Initialize database connection pool
    # try:
    #     await mysql_connector.initialize()
    #     logger.info("Database connection pool initialized")
    # except Exception as e:
    #     logger.warning(f"Failed to initialize database connection: {e}")
    #     logger.warning("System will run without persistence features")

    # 禁用持久化服务 - 改为纯内存运行
    # Start performance monitoring
    # try:
    #     await performance_monitor.start()
    #     logger.info("Performance monitoring started")
    # except Exception as e:
    #     logger.warning(f"Failed to start performance monitoring: {e}")
    #     logger.warning("System will run without performance monitoring")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down Translation System Backend V2 - Memory Only Mode")

    # 禁用持久化服务 - 改为纯内存运行
    # Stop performance monitoring
    # try:
    #     await performance_monitor.stop()
    #     logger.info("Performance monitoring stopped")
    # except Exception as e:
    #     logger.warning(f"Error stopping performance monitoring: {e}")

    # 禁用持久化服务 - 改为纯内存运行
    # Close database connection pool
    # try:
    #     await mysql_connector.close()
    #     logger.info("Database connection pool closed")
    # except Exception as e:
    #     logger.warning(f"Error closing database connection: {e}")


if __name__ == "__main__":
    import uvicorn

    host = config_manager.get('api.host', '0.0.0.0')
    port = config_manager.get('api.port', 8013)

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level=config_manager.log_level.lower()
    )