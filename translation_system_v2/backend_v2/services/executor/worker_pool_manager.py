"""Worker pool manager for multi-session concurrent execution."""

import asyncio
from typing import Dict, Optional
import logging
from datetime import datetime, timedelta

from services.executor.worker_pool import WorkerPool

logger = logging.getLogger(__name__)


class WorkerPoolManager:
    """Manage multiple worker pools for concurrent multi-user execution."""

    def __init__(self):
        """Initialize worker pool manager."""
        self._pools: Dict[str, WorkerPool] = {}
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def get_or_create_pool(self, session_id: str, max_workers: int = 10) -> WorkerPool:
        """
        Get existing pool for session or create a new one.

        Args:
            session_id: Session identifier
            max_workers: Maximum concurrent workers for this pool

        Returns:
            WorkerPool instance for the session
        """
        if session_id not in self._pools:
            self.logger.info(f"Creating new worker pool for session {session_id} with {max_workers} workers")
            self._pools[session_id] = WorkerPool(session_id=session_id, max_workers=max_workers)
        return self._pools[session_id]

    def get_pool(self, session_id: str) -> Optional[WorkerPool]:
        """
        Get existing pool for session.

        Args:
            session_id: Session identifier

        Returns:
            WorkerPool instance or None if not found
        """
        return self._pools.get(session_id)

    async def cleanup_pool(self, session_id: str) -> None:
        """
        Clean up worker pool for completed/stopped session.

        Args:
            session_id: Session identifier
        """
        async with self._lock:
            if session_id in self._pools:
                pool = self._pools[session_id]

                # Stop execution if still running
                if pool.status.value in ['running', 'paused']:
                    self.logger.warning(f"Stopping active pool for session {session_id} before cleanup")
                    await pool.stop_execution()

                # Remove from dictionary
                del self._pools[session_id]
                self.logger.info(f"Cleaned up worker pool for session {session_id}")

    async def cleanup_completed_pools(self, age_hours: int = 8) -> None:
        """
        Clean up worker pools for completed sessions older than specified age.

        Args:
            age_hours: Remove pools completed more than this many hours ago
        """
        async with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=age_hours)
            sessions_to_remove = []

            for session_id, pool in self._pools.items():
                # Check if pool is completed and old enough
                if pool.status.value in ['completed', 'stopped', 'failed']:
                    end_time = pool.statistics.get('end_time')
                    if end_time and end_time < cutoff_time:
                        sessions_to_remove.append(session_id)

            # Remove old completed pools
            for session_id in sessions_to_remove:
                del self._pools[session_id]
                self.logger.info(f"Auto-cleaned up worker pool for session {session_id} (older than {age_hours}h)")

    def get_active_sessions(self) -> list[str]:
        """
        Get list of session IDs with active worker pools.

        Returns:
            List of session IDs
        """
        return [
            session_id for session_id, pool in self._pools.items()
            if pool.status.value in ['running', 'paused']
        ]

    def get_all_sessions(self) -> list[str]:
        """
        Get list of all session IDs with worker pools.

        Returns:
            List of session IDs
        """
        return list(self._pools.keys())

    def get_pool_statistics(self) -> Dict:
        """
        Get statistics about all worker pools.

        Returns:
            Dictionary with pool statistics
        """
        stats = {
            'total_pools': len(self._pools),
            'active_pools': len(self.get_active_sessions()),
            'pools_by_status': {}
        }

        for pool in self._pools.values():
            status = pool.status.value
            if status not in stats['pools_by_status']:
                stats['pools_by_status'][status] = 0
            stats['pools_by_status'][status] += 1

        return stats


# Global worker pool manager instance
worker_pool_manager = WorkerPoolManager()
