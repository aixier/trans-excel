"""Real-time progress tracker for translation execution."""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Set, Callable
from datetime import datetime
from collections import defaultdict

from models.task_dataframe import TaskDataFrameManager, TaskStatus
from utils.session_manager import session_manager

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Track and report translation progress in real-time."""

    def __init__(self):
        """Initialize progress tracker."""
        self.progress_cache = {}
        self.update_callbacks = []
        self.last_update_time = {}
        self.update_interval = 0.5  # Update at most every 500ms
        self.logger = logging.getLogger(self.__class__.__name__)

    def register_callback(self, callback: Callable):
        """
        Register a callback for progress updates.

        Args:
            callback: Function to call on progress update
        """
        self.update_callbacks.append(callback)

    async def update_task_progress(
        self,
        session_id: str,
        task_id: str,
        status: str,
        **kwargs
    ):
        """
        Update progress for a single task immediately.

        Args:
            session_id: Session ID
            task_id: Task ID
            status: New task status
            **kwargs: Additional task updates
        """
        # Update task in DataFrame immediately
        task_manager = session_manager.get_task_manager(session_id)
        if task_manager:
            # Update task
            update_data = {'status': status}
            update_data.update(kwargs)
            task_manager.update_task(task_id, update_data)

            # Update progress cache
            await self._update_progress_cache(session_id)

            # Trigger callbacks if enough time has passed
            current_time = time.time()
            last_update = self.last_update_time.get(session_id, 0)

            if current_time - last_update >= self.update_interval:
                self.last_update_time[session_id] = current_time
                await self._trigger_callbacks(session_id)

    async def _update_progress_cache(self, session_id: str):
        """Update cached progress statistics."""
        task_manager = session_manager.get_task_manager(session_id)
        if not task_manager or task_manager.df is None:
            return

        df = task_manager.df

        # Calculate real-time statistics
        total = len(df)
        completed = len(df[df['status'] == TaskStatus.COMPLETED])
        processing = len(df[df['status'] == TaskStatus.PROCESSING])
        pending = len(df[df['status'] == TaskStatus.PENDING])
        failed = len(df[df['status'] == TaskStatus.FAILED])

        # Calculate completion rate
        completion_rate = (completed / total * 100) if total > 0 else 0

        # Estimate remaining time
        if completed > 0 and processing > 0:
            # Calculate average task time
            completed_df = df[df['status'] == TaskStatus.COMPLETED]
            if 'duration_ms' in completed_df.columns:
                avg_duration = completed_df['duration_ms'].mean()
                remaining_tasks = pending + processing
                estimated_remaining = (avg_duration * remaining_tasks) / 1000  # Convert to seconds
            else:
                estimated_remaining = None
        else:
            estimated_remaining = None

        # Update cache
        self.progress_cache[session_id] = {
            'total': total,
            'completed': completed,
            'processing': processing,
            'pending': pending,
            'failed': failed,
            'completion_rate': completion_rate,
            'estimated_remaining_seconds': estimated_remaining,
            'last_updated': datetime.now().isoformat()
        }

    async def _trigger_callbacks(self, session_id: str):
        """Trigger all registered callbacks with progress update."""
        progress = self.progress_cache.get(session_id)
        if progress:
            for callback in self.update_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(session_id, progress)
                    else:
                        callback(session_id, progress)
                except Exception as e:
                    self.logger.error(f"Callback failed: {e}")

    def get_progress(self, session_id: str) -> Dict[str, Any]:
        """
        Get current progress for a session.

        Args:
            session_id: Session ID

        Returns:
            Progress statistics
        """
        if session_id in self.progress_cache:
            return self.progress_cache[session_id]

        # If not in cache, calculate now
        task_manager = session_manager.get_task_manager(session_id)
        if not task_manager or task_manager.df is None:
            return {
                'total': 0,
                'completed': 0,
                'processing': 0,
                'pending': 0,
                'failed': 0,
                'completion_rate': 0,
                'estimated_remaining_seconds': None
            }

        df = task_manager.df
        total = len(df)
        completed = len(df[df['status'] == TaskStatus.COMPLETED])
        processing = len(df[df['status'] == TaskStatus.PROCESSING])
        pending = len(df[df['status'] == TaskStatus.PENDING])
        failed = len(df[df['status'] == TaskStatus.FAILED])

        return {
            'total': total,
            'completed': completed,
            'processing': processing,
            'pending': pending,
            'failed': failed,
            'completion_rate': (completed / total * 100) if total > 0 else 0,
            'estimated_remaining_seconds': None
        }

    async def start_progress_monitoring(self, session_id: str):
        """
        Start monitoring progress for a session.

        Args:
            session_id: Session ID
        """
        self.logger.info(f"Starting progress monitoring for session {session_id}")

        # Initial cache update
        await self._update_progress_cache(session_id)

        # Start periodic updates
        asyncio.create_task(self._periodic_update(session_id))

    async def _periodic_update(self, session_id: str):
        """Periodically update progress cache."""
        while True:
            try:
                await asyncio.sleep(2)  # Update every 2 seconds

                # Check if execution is still active
                task_manager = session_manager.get_task_manager(session_id)
                if not task_manager or task_manager.df is None:
                    break

                # Check if all tasks are completed
                df = task_manager.df
                pending = len(df[df['status'] == TaskStatus.PENDING])
                processing = len(df[df['status'] == TaskStatus.PROCESSING])

                if pending == 0 and processing == 0:
                    # All tasks completed
                    await self._update_progress_cache(session_id)
                    await self._trigger_callbacks(session_id)
                    break

                # Regular update
                await self._update_progress_cache(session_id)

            except Exception as e:
                self.logger.error(f"Periodic update failed: {e}")
                break

    def clear_cache(self, session_id: str):
        """
        Clear cached progress for a session.

        Args:
            session_id: Session ID
        """
        if session_id in self.progress_cache:
            del self.progress_cache[session_id]
        if session_id in self.last_update_time:
            del self.last_update_time[session_id]


# Global progress tracker instance
progress_tracker = ProgressTracker()