"""Analytics API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from datetime import datetime, timedelta

from utils.pipeline_session_manager import pipeline_session_manager

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


@router.get("")
async def get_analytics(
    time_range: str = Query(default="month", description="Time range: day, week, month, year")
):
    """
    Get analytics data for sessions.

    Args:
        time_range: Time range for analytics (day/week/month/year)

    Returns:
        Analytics data with statistics
    """
    try:
        # Get all sessions
        all_sessions = pipeline_session_manager.list_sessions()

        # Filter by time range
        now = datetime.now()
        time_deltas = {
            'day': timedelta(days=1),
            'week': timedelta(weeks=1),
            'month': timedelta(days=30),
            'year': timedelta(days=365)
        }

        delta = time_deltas.get(time_range, timedelta(days=30))
        cutoff_time = now - delta

        # Filter sessions (for now, return all - would need created_at timestamp)
        filtered_sessions = all_sessions

        # Calculate statistics
        total_sessions = len(filtered_sessions)
        completed_sessions = [s for s in filtered_sessions if s.stage.value == 'EXECUTION_COMPLETED']

        # Extract session data
        sessions_data = []
        for session in filtered_sessions:
            session_info = {
                'id': session.session_id,
                'stage': session.stage.value,
                'input_source': session.input_source,
                'parent_session_id': session.parent_session_id,
                'createdAt': datetime.now().isoformat(),  # Mock - would need real timestamp
                'config': {
                    'rule_set': ','.join(session.rules) if session.rules else None,
                    'target_langs': [],  # Would need to extract from config
                    'llm_model': session.processor if session.processor else 'unknown'
                }
            }

            # Add execution results if available
            if session.tasks:
                total_tasks = len(session.tasks.df)
                completed_tasks = len(session.tasks.df[session.tasks.df['status'] == 'completed'])
                failed_tasks = len(session.tasks.df[session.tasks.df['status'] == 'failed'])

                session_info['executionResult'] = {
                    'totalTasks': total_tasks,
                    'completedTasks': completed_tasks,
                    'failedTasks': failed_tasks,
                    'cost': 0.0,  # Mock - would need real cost tracking
                    'duration': 0   # Mock - would need real duration tracking
                }

            sessions_data.append(session_info)

        return {
            'sessions': sessions_data,
            'time_range': time_range,
            'total': total_sessions,
            'completed': len(completed_sessions)
        }

    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")
