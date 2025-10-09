"""Session management API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
import logging
import os
from pathlib import Path
from datetime import datetime

from utils.session_manager import session_manager
from utils.session_cache import session_cache
from utils.json_converter import convert_numpy_types

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
logger = logging.getLogger(__name__)


@router.get("/list")
async def get_sessions_list(status: Optional[str] = None):
    """
    Get list of all sessions with their current status.

    Args:
        status: Filter by status (running/completed/stopped/all)

    Returns:
        List of sessions with detailed information
    """
    try:
        # Get all session IDs from cache (cross-worker)
        all_session_ids = session_cache.get_all_session_ids()

        sessions_list = []

        for session_id in all_session_ids:
            try:
                # Get session metadata from cache
                session_data = session_cache.get_session(session_id)
                if not session_data:
                    continue

                # Get task manager to check progress
                task_manager = session_manager.get_task_manager(session_id)

                # Build session info
                session_info = {
                    'session_id': session_id,
                    'filename': session_data.get('metadata', {}).get('filename', 'unknown'),
                    'created_at': session_data.get('created_at'),
                    'last_accessed': session_data.get('last_accessed'),
                    'stage': session_data.get('session_status', {}).get('stage', 'unknown'),
                    'has_tasks': False,
                    'progress': {
                        'total': 0,
                        'completed': 0,
                        'failed': 0,
                        'processing': 0,
                        'pending': 0,
                        'percentage': 0.0
                    },
                    'status': 'unknown',
                    'is_running': False,
                    'can_resume': False,
                    'can_download': False
                }

                # ✅ Determine status based on session stage (more reliable for cross-worker)
                current_stage = session_info['stage']

                # Check if tasks exist
                task_file_path = session_data.get('metadata', {}).get('task_file_path')
                if task_file_path and os.path.exists(task_file_path):
                    session_info['has_tasks'] = True

                    # ✅ Priority 1: Try to get real-time statistics from cache (cross-worker support)
                    # Use separate cache key to avoid conflict with session.to_dict()
                    realtime_stats = None
                    try:
                        realtime_key = f'realtime_progress:{session_id}'
                        realtime_stats = session_cache.cache.get(realtime_key)
                    except Exception as e:
                        logger.warning(f"Failed to get realtime_stats from cache: {e}")

                    if realtime_stats:
                        # Use real-time statistics from cache (synced by executing worker)
                        session_info['progress'] = {
                            'total': realtime_stats.get('total', 0),
                            'completed': realtime_stats.get('completed', 0),
                            'failed': realtime_stats.get('failed', 0),
                            'processing': realtime_stats.get('processing', 0),
                            'pending': realtime_stats.get('pending', 0),
                            'percentage': realtime_stats.get('completion_rate', 0.0)
                        }
                        logger.debug(f"Using real-time stats from cache for {session_id}")
                    elif task_manager and task_manager.df is not None:
                        # Fallback: Load from task_manager (works for all stages)
                        stats = task_manager.get_statistics()

                        session_info['progress'] = {
                            'total': stats.get('total', 0),
                            'completed': stats.get('by_status', {}).get('completed', 0),
                            'failed': stats.get('by_status', {}).get('failed', 0),
                            'processing': stats.get('by_status', {}).get('processing', 0),
                            'pending': stats.get('by_status', {}).get('pending', 0),
                            'percentage': (stats.get('by_status', {}).get('completed', 0) / stats.get('total', 1) * 100) if stats.get('total', 0) > 0 else 0.0
                        }
                        logger.debug(f"Using task_manager stats for {session_id} (stage: {current_stage})")
                    else:
                        # No stats available, keep default (all zeros)
                        logger.warning(f"No progress stats available for {session_id}")

                # ✅ Determine status based on session stage (primary indicator)
                if current_stage == 'executing':
                    session_info['status'] = 'running'
                    session_info['is_running'] = True
                    session_info['can_resume'] = False
                    session_info['can_download'] = False
                elif current_stage == 'completed':
                    session_info['status'] = 'completed'
                    session_info['is_running'] = False
                    session_info['can_resume'] = False
                    session_info['can_download'] = True
                elif current_stage == 'split_complete':
                    # Check if has partial progress (resumed case)
                    completed = session_info['progress']['completed']
                    if completed > 0:
                        session_info['status'] = 'stopped'
                        session_info['is_running'] = False
                        session_info['can_resume'] = True
                    else:
                        session_info['status'] = 'ready'
                        session_info['is_running'] = False
                        session_info['can_resume'] = True
                elif current_stage == 'analyzed':
                    session_info['status'] = 'analyzed'
                    session_info['is_running'] = False
                    session_info['can_resume'] = False
                else:
                    session_info['status'] = 'created'
                    session_info['is_running'] = False
                    session_info['can_resume'] = False

                # Apply filter
                if status:
                    if status == 'all' or session_info['status'] == status:
                        sessions_list.append(session_info)
                else:
                    # Default: return all
                    sessions_list.append(session_info)

            except Exception as e:
                logger.error(f"Error processing session {session_id}: {e}")
                continue

        # Sort by last_accessed (most recent first)
        sessions_list.sort(key=lambda x: x.get('last_accessed', ''), reverse=True)

        return convert_numpy_types({
            'sessions': sessions_list,
            'count': len(sessions_list),
            'filter': status or 'all'
        })

    except Exception as e:
        logger.error(f"Failed to get sessions list: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")


@router.get("/detail/{session_id}")
async def get_session_detail(session_id: str):
    """
    Get detailed information about a specific session.

    Args:
        session_id: Session ID

    Returns:
        Detailed session information
    """
    try:
        # Get session from cache
        session_data = session_cache.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get task manager
        task_manager = session_manager.get_task_manager(session_id)

        # Build detailed info
        detail = {
            'session_id': session_id,
            'filename': session_data.get('metadata', {}).get('filename'),
            'created_at': session_data.get('created_at'),
            'last_accessed': session_data.get('last_accessed'),
            'stage': session_data.get('session_status', {}).get('stage'),
            'metadata': session_data.get('metadata', {}),
            'has_tasks': task_manager is not None,
            'statistics': {},
            'files': {
                'excel_file': None,
                'task_file': None,
                'result_file': None
            }
        }

        # Add task statistics if available
        if task_manager and task_manager.df is not None:
            stats = task_manager.get_statistics()
            detail['statistics'] = stats

        # Check file existence
        metadata = session_data.get('metadata', {})
        excel_file_path = metadata.get('excel_file_path')
        task_file_path = metadata.get('task_file_path')

        if excel_file_path:
            detail['files']['excel_file'] = {
                'path': excel_file_path,
                'exists': os.path.exists(excel_file_path),
                'size': os.path.getsize(excel_file_path) if os.path.exists(excel_file_path) else 0
            }

        if task_file_path:
            detail['files']['task_file'] = {
                'path': task_file_path,
                'exists': os.path.exists(task_file_path),
                'size': os.path.getsize(task_file_path) if os.path.exists(task_file_path) else 0
            }

        return convert_numpy_types(detail)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session detail for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session detail: {str(e)}")


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and its data.

    Args:
        session_id: Session ID to delete

    Returns:
        Deletion status
    """
    try:
        # Delete from cache
        session_cache.delete_session(session_id)

        # Delete files
        deleted_files = []
        data_dir = Path(__file__).parent.parent / 'data' / 'sessions'

        for pattern in [f'{session_id}_*', f'{session_id}.*']:
            for file_path in data_dir.glob(pattern):
                try:
                    file_path.unlink()
                    deleted_files.append(str(file_path.name))
                except Exception as e:
                    logger.warning(f"Failed to delete file {file_path}: {e}")

        return {
            'status': 'success',
            'session_id': session_id,
            'deleted_files': deleted_files
        }

    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
