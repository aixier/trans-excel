"""
Buffer Manager - Task 5.1
Manages in-memory buffers for batch writes with automatic flushing
"""
import asyncio
import time
import logging
from typing import List, Dict, Any
from datetime import datetime
from config.settings import settings
from storage.registry import StorageBackendRegistry

logger = logging.getLogger(__name__)


class BufferManager:
    """
    Buffer Manager for batch operations
    Accumulates data in memory and flushes to storage based on:
    - Buffer size threshold
    - Time interval threshold
    """

    def __init__(
        self,
        max_buffer_size: int = None,
        flush_interval: int = None
    ):
        """
        Initialize buffer manager

        Args:
            max_buffer_size: Maximum buffer size before auto-flush
            flush_interval: Flush interval in seconds
        """
        self.max_buffer_size = max_buffer_size or settings.buffer.max_buffer_size
        self.flush_interval = flush_interval or settings.buffer.flush_interval

        # Buffers
        self.session_buffer: List[Dict] = []
        self.task_buffer: List[Dict] = []

        # Timing
        self.last_flush_time = time.time()

        # Statistics
        self.total_sessions_written = 0
        self.total_tasks_written = 0
        self.total_flush_count = 0
        self.last_flush_duration_ms = 0

        # Locks for thread safety
        self._session_lock = asyncio.Lock()
        self._task_lock = asyncio.Lock()
        self._flush_lock = asyncio.Lock()

        # Flush task
        self._flush_task = None
        self._running = False

        logger.info(
            f"BufferManager initialized: "
            f"max_size={self.max_buffer_size}, "
            f"flush_interval={self.flush_interval}s"
        )

    async def add_sessions(self, sessions: List[Dict]):
        """
        Add sessions to buffer

        Args:
            sessions: List of session dictionaries
        """
        if not sessions:
            return

        async with self._session_lock:
            self.session_buffer.extend(sessions)
            logger.debug(f"Added {len(sessions)} sessions to buffer (total: {len(self.session_buffer)})")

        # Check if flush needed
        await self._check_and_flush()

    async def add_tasks(self, tasks: List[Dict]):
        """
        Add tasks to buffer

        Args:
            tasks: List of task dictionaries
        """
        if not tasks:
            return

        async with self._task_lock:
            self.task_buffer.extend(tasks)
            logger.debug(f"Added {len(tasks)} tasks to buffer (total: {len(self.task_buffer)})")

        # Check if flush needed
        await self._check_and_flush()

    async def _check_and_flush(self):
        """
        Check if flush is needed and trigger if necessary
        """
        if self._should_flush():
            await self.flush()

    def _should_flush(self) -> bool:
        """
        Determine if buffer should be flushed

        Returns:
            True if flush needed, False otherwise
        """
        # Check buffer size
        buffer_full = (
            len(self.session_buffer) >= self.max_buffer_size or
            len(self.task_buffer) >= self.max_buffer_size
        )

        # Check time elapsed
        time_expired = (time.time() - self.last_flush_time) >= self.flush_interval

        return buffer_full or time_expired

    async def flush(self) -> Dict[str, Any]:
        """
        Flush buffers to storage

        Returns:
            Dictionary with flush results
        """
        async with self._flush_lock:
            # Check if buffers are empty
            if not self.session_buffer and not self.task_buffer:
                return {
                    "sessions": 0,
                    "tasks": 0,
                    "duration_ms": 0
                }

            start_time = time.time()

            # Get snapshots and clear buffers
            async with self._session_lock:
                sessions_to_write = self.session_buffer.copy()
                self.session_buffer.clear()

            async with self._task_lock:
                tasks_to_write = self.task_buffer.copy()
                self.task_buffer.clear()

            logger.info(
                f"Flushing buffers: {len(sessions_to_write)} sessions, "
                f"{len(tasks_to_write)} tasks"
            )

            sessions_written = 0
            tasks_written = 0

            try:
                # Get storage backend
                session_backend = StorageBackendRegistry.get_backend("translation_sessions")
                task_backend = StorageBackendRegistry.get_backend("translation_tasks")

                # Flush sessions
                if sessions_to_write:
                    sessions_written = await session_backend.write(
                        "translation_sessions",
                        sessions_to_write
                    )
                    logger.info(f"Wrote {sessions_written} sessions to database")

                # Flush tasks
                if tasks_to_write:
                    tasks_written = await task_backend.write(
                        "translation_tasks",
                        tasks_to_write
                    )
                    logger.info(f"Wrote {tasks_written} tasks to database")

                # Update statistics
                self.total_sessions_written += sessions_written
                self.total_tasks_written += tasks_written
                self.total_flush_count += 1
                self.last_flush_time = time.time()

                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)
                self.last_flush_duration_ms = duration_ms

                logger.info(
                    f"Flush completed: {sessions_written} sessions, "
                    f"{tasks_written} tasks in {duration_ms}ms"
                )

                return {
                    "sessions": sessions_written,
                    "tasks": tasks_written,
                    "duration_ms": duration_ms
                }

            except Exception as e:
                logger.error(f"Flush failed: {e}")

                # IMPORTANT: Accept data loss on failure
                # Clear buffers even on error (design trade-off)
                logger.warning(
                    f"Data loss: {len(sessions_to_write)} sessions, "
                    f"{len(tasks_to_write)} tasks"
                )

                raise

    async def start_periodic_flush(self):
        """
        Start periodic flush task
        Runs in background and flushes buffers every flush_interval seconds
        """
        self._running = True
        logger.info(f"Starting periodic flush task (interval: {self.flush_interval}s)")

        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)

                # Flush if there's data
                if self.session_buffer or self.task_buffer:
                    await self.flush()

            except asyncio.CancelledError:
                logger.info("Periodic flush task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic flush task: {e}")
                # Continue running despite errors

    async def stop_periodic_flush(self):
        """
        Stop periodic flush task
        """
        self._running = False
        logger.info("Stopping periodic flush task")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get buffer statistics

        Returns:
            Dictionary with buffer statistics
        """
        total_buffered = len(self.session_buffer) + len(self.task_buffer)
        usage_percent = (total_buffered / (self.max_buffer_size * 2)) * 100

        return {
            "sessions_count": len(self.session_buffer),
            "tasks_count": len(self.task_buffer),
            "total_buffered": total_buffered,
            "capacity": self.max_buffer_size,
            "usage_percent": round(usage_percent, 2),
            "last_flush_time": datetime.fromtimestamp(self.last_flush_time).isoformat(),
            "last_flush_duration_ms": self.last_flush_duration_ms,
            "total_sessions_written": self.total_sessions_written,
            "total_tasks_written": self.total_tasks_written,
            "total_flush_count": self.total_flush_count
        }


# Global singleton instance
buffer_manager = BufferManager()