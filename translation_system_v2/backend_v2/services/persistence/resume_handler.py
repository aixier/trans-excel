"""Resume handler for recovering interrupted sessions."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from database.mysql_connector import mysql_connector
from services.persistence.checkpoint_service import checkpoint_service
from utils.pipeline_session_manager import pipeline_session_manager
from models.task_dataframe import TaskDataFrameManager

logger = logging.getLogger(__name__)


class ResumeHandler:
    """Handle session recovery and resumption."""

    def __init__(self):
        """Initialize resume handler."""
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_resumable_sessions(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get list of sessions that can be resumed.

        Args:
            days: Number of days to look back

        Returns:
            List of resumable sessions
        """
        try:
            # Query sessions from the last N days that are not completed
            query = """
                SELECT
                    session_id, filename, created_at, updated_at,
                    status, total_tasks, completed_tasks, failed_tasks,
                    processing_tasks, llm_provider, metadata
                FROM translation_sessions
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                AND status IN ('created', 'analyzing', 'splitting', 'executing', 'failed', 'cancelled')
                ORDER BY updated_at DESC
            """

            async with mysql_connector.get_connection() as cursor:
                await cursor.execute(query, (days,))
                rows = await cursor.fetchall()

                sessions = []
                for row in rows:
                    sessions.append({
                        'session_id': row[0],
                        'filename': row[1],
                        'created_at': row[2].isoformat() if row[2] else None,
                        'updated_at': row[3].isoformat() if row[3] else None,
                        'status': row[4],
                        'total_tasks': row[5],
                        'completed_tasks': row[6],
                        'failed_tasks': row[7],
                        'processing_tasks': row[8],
                        'llm_provider': row[9],
                        'metadata': row[10]
                    })

                return sessions

        except Exception as e:
            self.logger.error(f"Failed to get resumable sessions: {e}")
            return []

    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a session.

        Args:
            session_id: Session ID

        Returns:
            Session information or None if not found
        """
        try:
            query = """
                SELECT
                    session_id, filename, created_at, updated_at,
                    status, total_tasks, completed_tasks, failed_tasks,
                    processing_tasks, llm_provider, metadata, file_path
                FROM translation_sessions
                WHERE session_id = %s
            """

            async with mysql_connector.get_connection() as cursor:
                await cursor.execute(query, (session_id,))
                row = await cursor.fetchone()

                if row:
                    return {
                        'session_id': row[0],
                        'filename': row[1],
                        'created_at': row[2].isoformat() if row[2] else None,
                        'updated_at': row[3].isoformat() if row[3] else None,
                        'status': row[4],
                        'total_tasks': row[5],
                        'completed_tasks': row[6],
                        'failed_tasks': row[7],
                        'processing_tasks': row[8],
                        'llm_provider': row[9],
                        'metadata': row[10],
                        'file_path': row[11]
                    }

                return None

        except Exception as e:
            self.logger.error(f"Failed to get session info: {e}")
            return None

    async def resume_session(self, session_id: str) -> Dict[str, Any]:
        """
        Resume an interrupted session.

        Args:
            session_id: Session ID to resume

        Returns:
            Resume result with status
        """
        try:
            # Check if session exists
            session_info = await self.get_session_info(session_id)
            if not session_info:
                return {
                    'success': False,
                    'error': 'Session not found'
                }

            # Try to restore from checkpoint
            restored = await checkpoint_service.restore_checkpoint(session_id)

            if restored:
                # Update session status
                await self._update_session_status(session_id, 'executing')

                # Get restored task manager
                task_manager = pipeline_session_manager.get_tasks(session_id)

                return {
                    'success': True,
                    'session_id': session_id,
                    'restored_tasks': len(task_manager.df) if task_manager and task_manager.df is not None else 0,
                    'checkpoint_time': datetime.now().isoformat(),
                    'message': 'Session restored from checkpoint'
                }
            else:
                # Try to restore from database
                tasks = await self._restore_tasks_from_db(session_id)

                if tasks:
                    return {
                        'success': True,
                        'session_id': session_id,
                        'restored_tasks': len(tasks),
                        'message': 'Session restored from database'
                    }

                return {
                    'success': False,
                    'error': 'Failed to restore session'
                }

        except Exception as e:
            self.logger.error(f"Failed to resume session {session_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _update_session_status(self, session_id: str, status: str):
        """Update session status in database."""
        try:
            query = """
                UPDATE translation_sessions
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = %s
            """
            await mysql_connector.execute(query, (status, session_id))
        except Exception as e:
            self.logger.error(f"Failed to update session status: {e}")

    async def _restore_tasks_from_db(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Restore tasks from database."""
        try:
            return await mysql_connector.get_tasks_by_session(session_id)
        except Exception as e:
            self.logger.error(f"Failed to restore tasks from database: {e}")
            return None


# Global instance
resume_handler = ResumeHandler()