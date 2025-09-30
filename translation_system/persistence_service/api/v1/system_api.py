"""
System API Endpoints - Task 6.5
System health check and metrics endpoints
"""
import logging
from fastapi import APIRouter

from models.api_models import HealthResponse
from services.buffer_manager import buffer_manager
from storage.registry import StorageBackendRegistry

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, status_code=200)
async def health_check():
    """
    Health check endpoint

    Check the health status of the service and its dependencies.

    - Returns: Health status including database and buffer stats
    """
    try:
        # Check all storage backends
        health_results = await StorageBackendRegistry.health_check_all()

        # Determine overall database health
        db_healthy = all(health_results.values())

        # Get buffer stats
        buffer_stats = buffer_manager.get_stats()

        # Overall status
        status = "healthy" if db_healthy else "unhealthy"

        return HealthResponse(
            status=status,
            version="1.0.0",
            database="healthy" if db_healthy else "unhealthy",
            buffer=buffer_stats
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            database="unhealthy",
            buffer={}
        )


@router.get("/api/v1/system/metrics", status_code=200)
async def get_metrics():
    """
    Get system metrics

    Returns system metrics in a format suitable for monitoring.
    (Prometheus format can be added in future)

    - Returns: System metrics
    """
    try:
        # Get buffer stats
        buffer_stats = buffer_manager.get_stats()

        # Get storage backend health
        backend_health = await StorageBackendRegistry.health_check_all()

        metrics = {
            "buffer": buffer_stats,
            "backends": backend_health,
            "version": "1.0.0"
        }

        return metrics

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return {
            "error": str(e),
            "version": "1.0.0"
        }


@router.get("/api/v1/system/config", status_code=200)
async def get_config():
    """
    Get system configuration

    Returns current system configuration (non-sensitive values only).

    - Returns: Configuration dictionary
    """
    from config.settings import settings

    config = {
        "service": {
            "host": settings.service.host,
            "port": settings.service.port,
            "debug": settings.service.debug
        },
        "buffer": {
            "max_buffer_size": settings.buffer.max_buffer_size,
            "flush_interval": settings.buffer.flush_interval
        },
        "database": {
            "host": settings.database.host,
            "port": settings.database.port,
            "database": settings.database.database,
            "pool_size": settings.database.pool_size
            # Omit sensitive fields like password
        }
    }

    return config