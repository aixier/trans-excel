"""Resume and recovery API endpoints."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
import logging

from services.persistence.resume_handler import resume_handler
from services.persistence.checkpoint_service import checkpoint_service
from utils.session_manager import session_manager
from database.mysql_connector import mysql_connector

router = APIRouter(prefix="/api/resume", tags=["resume"])
logger = logging.getLogger(__name__)


@router.get("/sessions")
async def get_resumable_sessions(
    status: Optional[str] = None,
    days: int = 7
):
    """
    Get list of resumable sessions.

    Args:
        status: Filter by session status
        days: Number of days to look back

    Returns:
        List of resumable sessions
    """
    try:
        sessions = await resume_handler.get_resumable_sessions(days)

        if status:
            sessions = [s for s in sessions if s.get('status') == status]

        return {
            'sessions': sessions,
            'count': len(sessions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resumable sessions: {str(e)}")


@router.post("/session/{session_id}")
async def resume_session(session_id: str):
    """
    Resume an interrupted session.

    Args:
        session_id: Session ID to resume

    Returns:
        Resume status and restored data
    """
    try:
        # Check if session exists
        session_data = await resume_handler.get_session_info(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check if session is already active
        if session_manager.get_task_manager(session_id):
            return {
                'status': 'already_active',
                'message': 'Session is already active',
                'session_id': session_id
            }

        # Resume the session
        result = await resume_handler.resume_session(session_id)

        if result['success']:
            return {
                'status': 'resumed',
                'session_id': session_id,
                'restored_tasks': result.get('restored_tasks', 0),
                'checkpoint_time': result.get('checkpoint_time'),
                'message': 'Session successfully resumed'
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Failed to resume session')
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Resume failed: {str(e)}")


@router.get("/checkpoints/{session_id}")
async def get_session_checkpoints(session_id: str):
    """
    Get all checkpoints for a session.

    Args:
        session_id: Session ID

    Returns:
        List of checkpoints
    """
    try:
        checkpoints = await checkpoint_service.list_checkpoints(session_id)

        return {
            'session_id': session_id,
            'checkpoints': checkpoints,
            'count': len(checkpoints)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get checkpoints: {str(e)}")


@router.post("/restore/{session_id}")
async def restore_from_checkpoint(
    session_id: str,
    checkpoint_id: Optional[int] = None
):
    """
    Restore session from a specific checkpoint.

    Args:
        session_id: Session ID
        checkpoint_id: Specific checkpoint ID (uses latest if not provided)

    Returns:
        Restore status
    """
    try:
        # Restore from checkpoint
        success = await checkpoint_service.restore_checkpoint(session_id, checkpoint_id)

        if success:
            # Get restored session info
            task_manager = session_manager.get_task_manager(session_id)
            stats = task_manager.get_statistics() if task_manager else {}

            return {
                'status': 'success',
                'session_id': session_id,
                'checkpoint_id': checkpoint_id,
                'restored_tasks': stats.get('total', 0),
                'message': 'Session restored from checkpoint'
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to restore checkpoint")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore checkpoint for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, keep_checkpoints: bool = False):
    """
    Delete a session and optionally its checkpoints.

    Args:
        session_id: Session ID to delete
        keep_checkpoints: Whether to keep checkpoints

    Returns:
        Deletion status
    """
    try:
        # Delete from database
        async with mysql_connector.get_connection() as cursor:
            if keep_checkpoints:
                # Only delete session, keep checkpoints
                await cursor.execute(
                    "UPDATE checkpoints SET is_latest = FALSE WHERE session_id = %s",
                    (session_id,)
                )

            # Delete session (cascades to tasks, logs, and checkpoints if not keeping)
            await cursor.execute(
                "DELETE FROM translation_sessions WHERE session_id = %s",
                (session_id,)
            )

            deleted = cursor.rowcount > 0

        # Remove from memory if active
        if session_manager.get_task_manager(session_id):
            session_manager.remove_session(session_id)

        return {
            'status': 'success' if deleted else 'not_found',
            'session_id': session_id,
            'deleted': deleted,
            'checkpoints_kept': keep_checkpoints
        }

    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/recovery-info/{session_id}")
async def get_recovery_info(session_id: str):
    """
    Get detailed recovery information for a session.

    Args:
        session_id: Session ID

    Returns:
        Detailed recovery information
    """
    try:
        # Get session info
        session_info = await resume_handler.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get checkpoint info
        checkpoints = await checkpoint_service.list_checkpoints(session_id)

        # Get task statistics
        async with mysql_connector.get_connection() as cursor:
            # Task status counts
            await cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM translation_tasks
                WHERE session_id = %s
                GROUP BY status
            """, (session_id,))

            task_stats = {}
            for row in await cursor.fetchall():
                task_stats[row[0]] = row[1]

            # Failed task details
            await cursor.execute("""
                SELECT task_id, error_message, retry_count
                FROM translation_tasks
                WHERE session_id = %s AND status = 'failed'
                LIMIT 10
            """, (session_id,))

            failed_tasks = []
            for row in await cursor.fetchall():
                failed_tasks.append({
                    'task_id': row[0],
                    'error': row[1],
                    'retries': row[2]
                })

        return {
            'session_info': session_info,
            'checkpoints': {
                'count': len(checkpoints),
                'latest': checkpoints[0] if checkpoints else None,
                'list': checkpoints
            },
            'task_statistics': task_stats,
            'failed_tasks': failed_tasks,
            'can_resume': session_info.get('status') not in ['completed', 'cancelled'],
            'recommended_action': _get_recommended_action(session_info, task_stats)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recovery info for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recovery info: {str(e)}")


def _get_recommended_action(session_info, task_stats):
    """Determine recommended recovery action based on session state."""
    status = session_info.get('status')
    failed_count = task_stats.get('failed', 0)
    pending_count = task_stats.get('pending', 0)

    if status == 'completed':
        return 'Session already completed'
    elif status == 'cancelled':
        return 'Session was cancelled, resume to continue'
    elif failed_count > 10:
        return 'High failure rate, review errors before resuming'
    elif pending_count > 0:
        return 'Resume to process remaining tasks'
    else:
        return 'Session appears complete, verify results'