"""
Recovery Service - Task 5.3
Handles data recovery for incomplete sessions
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
from storage.registry import StorageBackendRegistry
from storage.mysql_plugin import MySQLPlugin

logger = logging.getLogger(__name__)


class RecoveryService:
    """
    Data recovery service
    Helps restore incomplete sessions after service restart
    """

    async def get_incomplete_sessions(self) -> List[Dict]:
        """
        Get all incomplete sessions (pending or processing)

        Returns:
            List of incomplete session dictionaries
        """
        try:
            # Get MySQL backend for special query
            backend = StorageBackendRegistry.get_backend_by_name("mysql")

            if isinstance(backend, MySQLPlugin):
                sessions = await backend.get_incomplete_sessions()
                logger.info(f"Found {len(sessions)} incomplete sessions")
                return sessions
            else:
                raise ValueError("MySQL backend not available for recovery")

        except Exception as e:
            logger.error(f"Failed to get incomplete sessions: {e}")
            raise

    async def restore_session(self, session_id: str) -> Dict:
        """
        Restore complete data for a session

        Args:
            session_id: Session ID to restore

        Returns:
            Dictionary with session and all incomplete tasks
        """
        try:
            # Get MySQL backend for special query
            backend = StorageBackendRegistry.get_backend_by_name("mysql")

            if not isinstance(backend, MySQLPlugin):
                raise ValueError("MySQL backend not available for recovery")

            # Get session with tasks
            result = await backend.get_session_with_tasks(session_id)

            session = result['session']
            tasks = result['tasks']

            logger.info(
                f"Restored session {session_id}: "
                f"{len(tasks)} incomplete tasks"
            )

            return {
                "session_id": session_id,
                "session": session,
                "tasks_count": len(tasks),
                "tasks": tasks,
                "restored_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to restore session {session_id}: {e}")
            raise


# Global singleton instance
recovery_service = RecoveryService()