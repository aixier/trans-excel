"""
Persistence Service - Main Application Entry Point
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import configuration and logging
from config.settings import settings
from config.logging import setup_logging

# Import storage setup
from storage.registry import StorageBackendRegistry, setup_storage_backends

# Import services
from services.buffer_manager import buffer_manager

# Import API routers
from api.v1 import translation_api, system_api


# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    logger.info("=" * 60)
    logger.info("Starting Persistence Service...")
    logger.info(f"Service: {settings.service.host}:{settings.service.port}")
    logger.info(f"Database: {settings.database.host}:{settings.database.port}/{settings.database.database}")
    logger.info(f"Buffer: max_size={settings.buffer.max_buffer_size}, flush_interval={settings.buffer.flush_interval}s")
    logger.info("=" * 60)

    try:
        # Setup and initialize storage backends
        setup_storage_backends()
        await StorageBackendRegistry.initialize_all()

        # Start periodic buffer flush task
        asyncio.create_task(buffer_manager.start_periodic_flush())
        logger.info("Periodic buffer flush task started")

        logger.info("=" * 60)
        logger.info("Persistence Service started successfully!")
        logger.info("API Documentation: http://{}:{}/docs".format(settings.service.host, settings.service.port))
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise

    yield

    # Shutdown: cleanup resources
    logger.info("=" * 60)
    logger.info("Shutting down Persistence Service...")

    # Stop periodic flush
    await buffer_manager.stop_periodic_flush()

    # Flush remaining buffer data
    try:
        result = await buffer_manager.flush()
        logger.info(
            f"Final buffer flush: {result['sessions']} sessions, "
            f"{result['tasks']} tasks"
        )
    except Exception as e:
        logger.error(f"Failed to flush buffer during shutdown: {e}")

    # Close storage backends
    await StorageBackendRegistry.close_all()

    logger.info("Persistence Service stopped")
    logger.info("=" * 60)


# Create FastAPI application
app = FastAPI(
    title="Persistence Service API",
    description="通用的、可扩展的数据持久化微服务 - Phase 1: Translation Persistence",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Error Handling - Task 6.6
# ============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
    )


# ============================================================================
# Register API Routers
# ============================================================================

# Register translation API
app.include_router(translation_api.router)

# Register system API
app.include_router(system_api.router)


# Root endpoint
@app.get("/", tags=["system"])
async def root():
    """
    Root endpoint - service information
    """
    return {
        "service": "Persistence Service",
        "version": "1.0.0",
        "phase": "Phase 1 - Translation Persistence MVP",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting Uvicorn server on {settings.service.host}:{settings.service.port}")

    uvicorn.run(
        "main:app",
        host=settings.service.host,
        port=settings.service.port,
        reload=settings.service.debug,
        log_level=settings.logging.level.lower()
    )