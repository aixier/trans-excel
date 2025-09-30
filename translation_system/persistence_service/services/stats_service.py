"""
Statistics Service - Task 5.4
Provides system and storage statistics
"""
import logging
from typing import Dict, Any
from storage.registry import StorageBackendRegistry
from storage.mysql_plugin import MySQLPlugin

logger = logging.getLogger(__name__)


class StatsService:
    """
    Statistics service
    Provides various statistics about sessions, tasks, and storage
    """

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics

        Returns:
            Dictionary with all statistics
        """
        try:
            # Get MySQL backend
            backend = StorageBackendRegistry.get_backend_by_name("mysql")

            if isinstance(backend, MySQLPlugin):
                stats = await backend.get_stats()
                logger.debug(f"Retrieved statistics: {stats}")
                return stats
            else:
                raise ValueError("MySQL backend not available for stats")

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise

    async def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session-only statistics

        Returns:
            Dictionary with session statistics
        """
        try:
            backend = StorageBackendRegistry.get_backend_by_name("mysql")

            if isinstance(backend, MySQLPlugin):
                stats = await backend.connector.get_sessions_stats()
                return stats
            else:
                raise ValueError("MySQL backend not available")

        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            raise

    async def get_task_stats(self) -> Dict[str, Any]:
        """
        Get task-only statistics

        Returns:
            Dictionary with task statistics
        """
        try:
            backend = StorageBackendRegistry.get_backend_by_name("mysql")

            if isinstance(backend, MySQLPlugin):
                stats = await backend.connector.get_tasks_stats()
                return stats
            else:
                raise ValueError("MySQL backend not available")

        except Exception as e:
            logger.error(f"Failed to get task stats: {e}")
            raise

    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage-only statistics

        Returns:
            Dictionary with storage statistics
        """
        try:
            backend = StorageBackendRegistry.get_backend_by_name("mysql")

            if isinstance(backend, MySQLPlugin):
                stats = await backend.connector.get_database_stats()
                return stats
            else:
                raise ValueError("MySQL backend not available")

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            raise


# Global singleton instance
stats_service = StatsService()