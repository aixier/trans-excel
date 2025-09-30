"""Log management API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta

from services.logging.log_persister import log_persister
from database.mysql_connector import mysql_connector

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/query")
async def query_logs(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    component: Optional[str] = Query(None, description="Filter by component"),
    hours: int = Query(1, description="Hours of logs to retrieve"),
    limit: int = Query(100, description="Maximum number of logs")
):
    """
    Query logs from database.

    Args:
        session_id: Optional session ID filter
        level: Optional level filter (INFO, WARNING, ERROR)
        component: Optional component filter
        hours: Number of hours to look back
        limit: Maximum number of logs to return

    Returns:
        List of log entries
    """
    try:
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        # Build query
        query = """
            SELECT log_id, session_id, timestamp, level, message, component, details
            FROM execution_logs
            WHERE timestamp >= %s AND timestamp <= %s
        """
        params = [start_time, end_time]

        if session_id:
            query += " AND session_id = %s"
            params.append(session_id)

        if level:
            query += " AND level = %s"
            params.append(level)

        if component:
            query += " AND component = %s"
            params.append(component)

        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)

        # Execute query
        async with mysql_connector.get_connection() as cursor:
            await cursor.execute(query, params)
            rows = await cursor.fetchall()

            logs = []
            for row in rows:
                logs.append({
                    'log_id': row[0],
                    'session_id': row[1],
                    'timestamp': row[2].isoformat() if row[2] else None,
                    'level': row[3],
                    'message': row[4],
                    'component': row[5],
                    'details': row[6]
                })

            return {
                'logs': logs,
                'count': len(logs),
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query logs: {str(e)}")


@router.get("/stats")
async def get_log_stats(session_id: Optional[str] = None):
    """
    Get log statistics.

    Args:
        session_id: Optional session ID filter

    Returns:
        Log statistics
    """
    try:
        base_query = "FROM execution_logs"
        params = []

        if session_id:
            base_query += " WHERE session_id = %s"
            params.append(session_id)

        async with mysql_connector.get_connection() as cursor:
            # Total count
            await cursor.execute(f"SELECT COUNT(*) {base_query}", params)
            total = (await cursor.fetchone())[0]

            # Count by level
            level_query = f"""
                SELECT level, COUNT(*) as count
                {base_query}
                {' AND ' if session_id else ' WHERE '} level IS NOT NULL
                GROUP BY level
            """
            await cursor.execute(level_query, params)
            level_counts = {}
            for row in await cursor.fetchall():
                level_counts[row[0]] = row[1]

            # Count by component
            component_query = f"""
                SELECT component, COUNT(*) as count
                {base_query}
                {' AND ' if session_id else ' WHERE '} component IS NOT NULL
                GROUP BY component
                ORDER BY count DESC
                LIMIT 10
            """
            await cursor.execute(component_query, params)
            component_counts = {}
            for row in await cursor.fetchall():
                component_counts[row[0]] = row[1]

            # Recent activity (last hour)
            recent_query = f"""
                SELECT COUNT(*)
                {base_query}
                {' AND ' if session_id else ' WHERE '} timestamp >= %s
            """
            recent_params = params + [datetime.now() - timedelta(hours=1)]
            await cursor.execute(recent_query, recent_params)
            recent_count = (await cursor.fetchone())[0]

            return {
                'total_logs': total,
                'by_level': level_counts,
                'by_component': component_counts,
                'recent_activity': recent_count,
                'session_id': session_id
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get log stats: {str(e)}")


@router.post("/flush")
async def flush_logs():
    """
    Force flush pending logs to database.

    Returns:
        Flush status
    """
    try:
        result = await log_persister.flush()
        return {
            'status': 'success',
            'flushed_count': result.get('flushed', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to flush logs: {str(e)}")


@router.delete("/cleanup")
async def cleanup_old_logs(days: int = 7):
    """
    Clean up old logs.

    Args:
        days: Delete logs older than this many days

    Returns:
        Cleanup result
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)

        async with mysql_connector.get_connection() as cursor:
            await cursor.execute(
                "DELETE FROM execution_logs WHERE timestamp < %s",
                (cutoff_date,)
            )
            deleted_count = cursor.rowcount

        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup logs: {str(e)}")