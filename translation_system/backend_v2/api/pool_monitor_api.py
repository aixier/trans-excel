"""Database connection pool monitoring API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from database.mysql_connector import mysql_connector

router = APIRouter(prefix="/api/pool", tags=["pool-monitor"])
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_pool_statistics() -> Dict[str, Any]:
    """
    Get current connection pool statistics.

    Returns:
        Pool statistics including usage, health, and recommendations
    """
    try:
        stats = mysql_connector.get_pool_stats()
        return {
            'status': 'success',
            'pool_stats': stats,
            'message': _get_status_message(stats)
        }
    except Exception as e:
        logger.error(f"Failed to get pool stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pool stats: {str(e)}")


@router.get("/health")
async def check_pool_health() -> Dict[str, Any]:
    """
    Perform health check on connection pool.

    Returns:
        Health check results including connectivity and latency
    """
    try:
        health = await mysql_connector.check_pool_health()
        return {
            'status': 'success',
            'health_check': health,
            'summary': _get_health_summary(health)
        }
    except Exception as e:
        logger.error(f"Pool health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/metrics")
async def get_connection_metrics() -> Dict[str, Any]:
    """
    Get detailed connection metrics and optimization recommendations.

    Returns:
        Comprehensive metrics and recommendations
    """
    try:
        metrics = await mysql_connector.get_connection_metrics()
        return {
            'status': 'success',
            'metrics': metrics,
            'action_required': _needs_action(metrics)
        }
    except Exception as e:
        logger.error(f"Failed to get connection metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.post("/optimize")
async def optimize_pool_settings() -> Dict[str, Any]:
    """
    Apply recommended optimizations to pool settings (if safe).

    Returns:
        Optimization results
    """
    try:
        # Get current metrics
        metrics = await mysql_connector.get_connection_metrics()
        pool_stats = metrics['pool_stats']

        recommendations = []

        # Check if we need to increase pool size
        if pool_stats['usage_percent'] > 80:
            new_max_size = min(pool_stats['max_size'] * 2, 50)  # Cap at 50
            recommendations.append({
                'action': 'increase_max_size',
                'current': pool_stats['max_size'],
                'recommended': new_max_size,
                'reason': 'High pool usage detected'
            })

        # Check if we need to increase min size
        if pool_stats['wait_queue'] > 0 and pool_stats['min_size'] < 5:
            recommendations.append({
                'action': 'increase_min_size',
                'current': pool_stats['min_size'],
                'recommended': 5,
                'reason': 'Connections waiting in queue'
            })

        return {
            'status': 'success',
            'current_settings': {
                'max_size': pool_stats['max_size'],
                'min_size': pool_stats['min_size'],
                'current_usage': pool_stats['usage_percent']
            },
            'recommendations': recommendations,
            'message': 'Manual configuration update required in config files'
        }

    except Exception as e:
        logger.error(f"Failed to optimize pool: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


def _get_status_message(stats: Dict[str, Any]) -> str:
    """Generate status message based on pool stats."""
    if stats['status'] == 'not_initialized':
        return 'Connection pool not initialized'

    health = stats.get('health', 'unknown')
    usage = stats.get('usage_percent', 0)

    if health == 'critical':
        return f'CRITICAL: Pool usage at {usage:.1f}%! Immediate action required.'
    elif health == 'warning':
        return f'WARNING: High pool usage ({usage:.1f}%). Monitor closely.'
    else:
        return f'Pool operating normally ({usage:.1f}% usage)'


def _get_health_summary(health: Dict[str, Any]) -> str:
    """Generate health summary message."""
    status = health.get('status', 'unknown')
    latency = health.get('latency_ms', 0)

    if status == 'unhealthy':
        return f"Pool unhealthy: {health.get('error', 'Unknown error')}"
    elif status == 'degraded':
        return f"Pool degraded: High latency ({latency:.1f}ms)"
    else:
        return f"Pool healthy: Latency {latency:.1f}ms"


def _needs_action(metrics: Dict[str, Any]) -> bool:
    """Check if any action is required based on metrics."""
    for rec in metrics.get('recommendations', []):
        if rec.get('level') in ['critical', 'warning']:
            return True
    return False