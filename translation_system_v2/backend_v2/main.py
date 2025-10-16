"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.task_api import router as task_router
from api.execute_api import router as execute_router
from api.monitor_api import router as monitor_router
from api.download_api import router as download_router
from api.websocket_api import router as websocket_router
from api.pool_monitor_api import router as pool_monitor_router
from api.auth_api import router as auth_router
from api.session_api import router as session_router
from api.glossary_api import router as glossary_router
from api.debug_api import router as debug_router
# Removed: analyze_api (merged into task_api split endpoint)
# Removed: pipeline_api (直接修改existing APIs instead)
from utils.config_manager import config_manager
import asyncio
from fastapi import Request
import time


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
app.include_router(auth_router)
app.include_router(session_router)
app.include_router(glossary_router)
app.include_router(task_router)  # Includes split (with merged analyze logic)
app.include_router(execute_router)
app.include_router(monitor_router)
app.include_router(download_router)
app.include_router(websocket_router)
app.include_router(pool_monitor_router)
app.include_router(debug_router)  # Debug and data inspection




@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Translation System Backend V2",
        "version": "2.0.0",
        "status": "running",
        "architecture": "session-per-transformation (2024-10-16)",
        "endpoints": {
            "core": [
                "/api/tasks/split - Split tasks (supports file upload OR parent_session_id)",
                "/api/tasks/split/status/{session_id} - Check split progress",
                "/api/tasks/export/{session_id} - Export tasks",
                "/api/execute/start - Execute tasks (supports processor parameter)",
                "/api/execute/stop/{session_id} - Stop execution",
                "/api/monitor/status/{session_id} - Check execution status",
                "/api/download/{session_id} - Download result Excel"
            ],
            "documentation": "/docs"
        },
        "features": {
            "session_per_transformation": True,
            "parent_child_chaining": True,
            "configuration_driven": True,
            "analyze_merged_into_split": True,
            "caps_in_separate_session": True,
            "three_data_formats": ["Excel (.xlsx)", "ExcelDataFrame", "TaskDataFrame"]
        }
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


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down Translation System Backend V2 - Memory Only Mode")


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