"""
健康检查API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import asyncio

from database.connection import get_db, AsyncSession
from config.settings import settings


router = APIRouter()


@router.get("/ping")
async def ping():
    """基础健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Translation System API Gateway"
    }


@router.get("/status")
async def health_status(db: AsyncSession = Depends(get_db)):
    """详细健康状态检查"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Translation System",
        "version": "1.0.0",
        "checks": {}
    }

    # 数据库连接检查
    try:
        await db.execute("SELECT 1")
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }

    # LLM API连接检查（简化版本）
    try:
        # 这里可以添加实际的LLM API连接检查
        if settings.llm_api_key and settings.llm_base_url:
            health_status["checks"]["llm_api"] = {
                "status": "healthy",
                "message": "LLM API configuration available"
            }
        else:
            health_status["checks"]["llm_api"] = {
                "status": "warning",
                "message": "LLM API configuration incomplete"
            }
    except Exception as e:
        health_status["checks"]["llm_api"] = {
            "status": "unhealthy",
            "message": f"LLM API check failed: {str(e)}"
        }

    # OSS存储检查
    try:
        if all([settings.oss_access_key_id, settings.oss_access_key_secret,
                settings.oss_endpoint, settings.oss_bucket_name]):
            health_status["checks"]["oss_storage"] = {
                "status": "healthy",
                "message": "OSS configuration available"
            }
        else:
            health_status["checks"]["oss_storage"] = {
                "status": "warning",
                "message": "OSS configuration incomplete"
            }
    except Exception as e:
        health_status["checks"]["oss_storage"] = {
            "status": "unhealthy",
            "message": f"OSS check failed: {str(e)}"
        }

    return health_status


@router.get("/ready")
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """就绪探针 - 用于Kubernetes等容器编排"""
    try:
        # 检查数据库连接
        await db.execute("SELECT 1")

        # 检查关键配置
        if not settings.llm_api_key:
            raise HTTPException(status_code=503, detail="LLM API key not configured")

        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service not ready: {str(e)}"
        )


@router.get("/live")
async def liveness_probe():
    """存活探针 - 用于Kubernetes等容器编排"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": 0  # 可以添加实际的运行时间计算
    }