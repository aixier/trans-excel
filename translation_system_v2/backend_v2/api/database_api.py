"""Database monitoring and health check API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from datetime import datetime
import asyncio

from database.mysql_connector import mysql_connector

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/database",
    tags=["database"]
)


@router.get("/health")
async def check_database_health() -> Dict[str, Any]:
    """
    Comprehensive database health check endpoint.

    Returns:
        Dict containing health status, connection pool stats, and test results
    """
    try:
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "status": "checking",
            "pool_stats": {},
            "connection_test": {},
            "query_test": {},
            "recommendations": []
        }

        # 1. Get pool statistics
        pool_stats = mysql_connector.get_pool_stats()
        health_report["pool_stats"] = pool_stats

        # 2. Test connection health
        connection_test = {
            "status": "pending",
            "latency_ms": 0,
            "error": None
        }

        start_time = datetime.now()
        try:
            async with mysql_connector.get_healthy_connection(retry_count=1) as cursor:
                await cursor.execute("SELECT 1")
                result = await cursor.fetchone()
                connection_test["status"] = "success" if result else "failed"
                connection_test["latency_ms"] = (datetime.now() - start_time).total_seconds() * 1000
        except Exception as e:
            connection_test["status"] = "failed"
            connection_test["error"] = str(e)
            connection_test["latency_ms"] = (datetime.now() - start_time).total_seconds() * 1000

        health_report["connection_test"] = connection_test

        # 3. Test actual query performance
        query_test = {
            "sessions_count": 0,
            "tasks_count": 0,
            "query_latency_ms": 0,
            "status": "pending"
        }

        try:
            start_time = datetime.now()
            async with mysql_connector.get_connection() as cursor:
                # Count sessions
                await cursor.execute("SELECT COUNT(*) FROM translation_sessions")
                sessions_result = await cursor.fetchone()
                query_test["sessions_count"] = sessions_result[0] if sessions_result else 0

                # Count tasks
                await cursor.execute("SELECT COUNT(*) FROM translation_tasks")
                tasks_result = await cursor.fetchone()
                query_test["tasks_count"] = tasks_result[0] if tasks_result else 0

                query_test["query_latency_ms"] = (datetime.now() - start_time).total_seconds() * 1000
                query_test["status"] = "success"
        except Exception as e:
            query_test["status"] = "failed"
            query_test["error"] = str(e)

        health_report["query_test"] = query_test

        # 4. Generate recommendations
        recommendations = []

        # Check pool usage
        if pool_stats.get("usage_percent", 0) > 80:
            recommendations.append({
                "level": "warning",
                "message": f"High pool usage: {pool_stats['usage_percent']:.1f}%. Consider increasing pool size."
            })

        if pool_stats.get("wait_queue", 0) > 0:
            recommendations.append({
                "level": "warning",
                "message": f"{pool_stats['wait_queue']} connections waiting in queue."
            })

        # Check connection health
        if connection_test["status"] == "failed":
            recommendations.append({
                "level": "critical",
                "message": f"Connection test failed: {connection_test.get('error', 'Unknown error')}"
            })
        elif connection_test["latency_ms"] > 1000:
            recommendations.append({
                "level": "warning",
                "message": f"High connection latency: {connection_test['latency_ms']:.0f}ms"
            })

        # Check query performance
        if query_test["status"] == "failed":
            recommendations.append({
                "level": "critical",
                "message": f"Query test failed: {query_test.get('error', 'Unknown error')}"
            })
        elif query_test["query_latency_ms"] > 500:
            recommendations.append({
                "level": "warning",
                "message": f"High query latency: {query_test['query_latency_ms']:.0f}ms"
            })

        if not recommendations:
            recommendations.append({
                "level": "info",
                "message": "Database is healthy and operating normally."
            })

        health_report["recommendations"] = recommendations

        # Determine overall status
        critical_issues = any(r["level"] == "critical" for r in recommendations)
        warning_issues = any(r["level"] == "warning" for r in recommendations)

        if critical_issues:
            health_report["status"] = "critical"
        elif warning_issues:
            health_report["status"] = "warning"
        else:
            health_report["status"] = "healthy"

        return health_report

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": str(e),
            "message": "Failed to perform health check"
        }


@router.get("/pool/stats")
async def get_pool_statistics() -> Dict[str, Any]:
    """
    Get connection pool statistics.

    Returns:
        Dict containing pool statistics
    """
    try:
        stats = mysql_connector.get_pool_stats()
        metrics = mysql_connector.get_pool_metrics()

        return {
            "timestamp": datetime.now().isoformat(),
            "pool": stats,
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Failed to get pool statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pool/reinitialize")
async def reinitialize_pool() -> Dict[str, Any]:
    """
    Reinitialize the database connection pool.
    Use this when connections are stale or the pool is corrupted.

    Returns:
        Dict containing reinitialization status
    """
    try:
        start_time = datetime.now()

        # Reinitialize the pool
        await mysql_connector.reinitialize_pool()

        # Test the new pool
        test_success = False
        try:
            async with mysql_connector.get_connection() as cursor:
                await cursor.execute("SELECT 1")
                result = await cursor.fetchone()
                test_success = result is not None
        except Exception as e:
            logger.error(f"Pool test after reinitialize failed: {e}")

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "timestamp": datetime.now().isoformat(),
            "status": "success" if test_success else "partial",
            "message": "Pool reinitialized successfully" if test_success else "Pool reinitialized but test failed",
            "duration_ms": duration_ms,
            "pool_stats": mysql_connector.get_pool_stats()
        }

    except Exception as e:
        logger.error(f"Failed to reinitialize pool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/connection")
async def test_connection(retry_count: int = 3) -> Dict[str, Any]:
    """
    Test database connection with retry mechanism.

    Args:
        retry_count: Number of retry attempts

    Returns:
        Dict containing connection test results
    """
    try:
        results = []

        for attempt in range(retry_count):
            test_result = {
                "attempt": attempt + 1,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "latency_ms": 0,
                "error": None
            }

            start_time = datetime.now()
            try:
                async with mysql_connector.get_healthy_connection(retry_count=1) as cursor:
                    await cursor.execute("SELECT VERSION() as version, DATABASE() as db, USER() as user")
                    result = await cursor.fetchone()

                    test_result["success"] = True
                    test_result["latency_ms"] = (datetime.now() - start_time).total_seconds() * 1000
                    test_result["info"] = {
                        "version": result[0] if result else None,
                        "database": result[1] if result else None,
                        "user": result[2] if result else None
                    }

            except Exception as e:
                test_result["success"] = False
                test_result["error"] = str(e)
                test_result["latency_ms"] = (datetime.now() - start_time).total_seconds() * 1000

            results.append(test_result)

            # If successful, no need for more attempts
            if test_result["success"]:
                break

            # Wait before next attempt
            if attempt < retry_count - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # Summary
        successful = any(r["success"] for r in results)
        avg_latency = sum(r["latency_ms"] for r in results) / len(results)

        return {
            "timestamp": datetime.now().isoformat(),
            "status": "success" if successful else "failed",
            "retry_count": retry_count,
            "attempts": results,
            "summary": {
                "successful": successful,
                "attempts_made": len(results),
                "avg_latency_ms": avg_latency
            }
        }

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/query")
async def test_query(query: str = "SELECT 1") -> Dict[str, Any]:
    """
    Execute a test query against the database.

    Args:
        query: SQL query to execute (default: SELECT 1)

    Returns:
        Dict containing query execution results
    """
    # Only allow SELECT queries for safety
    if not query.strip().upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")

    try:
        start_time = datetime.now()

        async with mysql_connector.get_connection() as cursor:
            await cursor.execute(query)
            results = await cursor.fetchall()

            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Format results
            formatted_results = []
            for row in results[:10]:  # Limit to 10 rows for safety
                formatted_results.append(dict(zip(columns, row)))

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return {
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "query": query,
                "execution_time_ms": execution_time,
                "row_count": len(results),
                "columns": columns,
                "results": formatted_results,
                "truncated": len(results) > 10
            }

    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))