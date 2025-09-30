"""
Cleanup Service - Task 5.5
Handles cleanup of old/expired data
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from storage.registry import StorageBackendRegistry
from storage.mysql_plugin import MySQLPlugin

logger = logging.getLogger(__name__)


class CleanupService:
    """
    Data cleanup service
    Removes old completed/failed sessions and their tasks
    """

    async def cleanup(
        self,
        completed_days: int = 90,
        failed_days: int = 30,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Cleanup old data

        Args:
            completed_days: Remove completed sessions older than N days
            failed_days: Remove failed sessions older than N days
            dry_run: If True, only count without deleting

        Returns:
            Dictionary with cleanup results
        """
        try:
            # Get MySQL backend
            backend = StorageBackendRegistry.get_backend_by_name("mysql")

            if not isinstance(backend, MySQLPlugin):
                raise ValueError("MySQL backend not available for cleanup")

            connector = backend.connector

            # Calculate cutoff dates
            completed_cutoff = (datetime.now() - timedelta(days=completed_days)).strftime('%Y-%m-%d')
            failed_cutoff = (datetime.now() - timedelta(days=failed_days)).strftime('%Y-%m-%d')

            logger.info(
                f"Cleanup started: completed_cutoff={completed_cutoff}, "
                f"failed_cutoff={failed_cutoff}, dry_run={dry_run}"
            )

            # Query sessions to delete
            filters_completed = {
                'status': 'completed',
                'to_date': completed_cutoff
            }
            filters_failed = {
                'status': 'failed',
                'to_date': failed_cutoff
            }

            # Get completed sessions
            result_completed = await connector.query_sessions(
                filters=filters_completed,
                page=1,
                page_size=1000,
                sort_by='created_at',
                order='asc'
            )

            # Get failed sessions
            result_failed = await connector.query_sessions(
                filters=filters_failed,
                page=1,
                page_size=1000,
                sort_by='created_at',
                order='asc'
            )

            sessions_to_delete = result_completed['items'] + result_failed['items']

            logger.info(f"Found {len(sessions_to_delete)} sessions to cleanup")

            if dry_run:
                # Count tasks that would be deleted
                tasks_count = 0
                for session in sessions_to_delete:
                    result = await connector.query_tasks(
                        filters={'session_id': session['session_id']},
                        page=1,
                        page_size=1
                    )
                    tasks_count += result['total']

                logger.info(
                    f"Dry run: would delete {len(sessions_to_delete)} sessions "
                    f"and {tasks_count} tasks"
                )

                return {
                    "deleted_sessions": len(sessions_to_delete),
                    "deleted_tasks": tasks_count,
                    "dry_run": True,
                    "timestamp": datetime.now().isoformat()
                }

            # Actually delete sessions (cascade deletes tasks)
            deleted_sessions = 0
            deleted_tasks = 0

            for session in sessions_to_delete:
                session_id = session['session_id']

                # Count tasks before deletion
                result = await connector.query_tasks(
                    filters={'session_id': session_id},
                    page=1,
                    page_size=1
                )
                task_count = result['total']

                # Delete session (cascade deletes tasks)
                success = await connector.delete_session(session_id)

                if success:
                    deleted_sessions += 1
                    deleted_tasks += task_count
                    logger.debug(f"Deleted session {session_id} with {task_count} tasks")

            logger.info(
                f"Cleanup completed: deleted {deleted_sessions} sessions "
                f"and {deleted_tasks} tasks"
            )

            return {
                "deleted_sessions": deleted_sessions,
                "deleted_tasks": deleted_tasks,
                "dry_run": False,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise


# Global singleton instance
cleanup_service = CleanupService()