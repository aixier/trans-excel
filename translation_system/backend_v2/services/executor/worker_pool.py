"""Worker pool for concurrent batch execution."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from enum import Enum

from services.executor.batch_executor import RetryableBatchExecutor
from services.llm.base_provider import BaseLLMProvider
from models.task_dataframe import TaskDataFrameManager, TaskStatus
from utils.session_manager import session_manager

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Execution status enum."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkerPool:
    """Manage concurrent workers for batch execution."""

    def __init__(self, max_workers: int = 10):
        """
        Initialize worker pool.

        Args:
            max_workers: Maximum concurrent workers
        """
        self.max_workers = max_workers
        self.active_workers = []
        self.queue = asyncio.Queue()
        self.status = ExecutionStatus.IDLE
        self.current_session_id = None
        self.llm_provider = None
        self.statistics = {
            'total_batches': 0,
            'completed_batches': 0,
            'failed_batches': 0,
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'start_time': None,
            'end_time': None
        }
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def start_execution(
        self,
        session_id: str,
        llm_provider: BaseLLMProvider
    ) -> Dict[str, Any]:
        """
        Start translation execution.

        Args:
            session_id: Session ID
            llm_provider: LLM provider instance

        Returns:
            Execution status
        """
        if self.status == ExecutionStatus.RUNNING:
            return {
                'status': 'error',
                'message': 'Execution already in progress'
            }

        self.current_session_id = session_id
        self.llm_provider = llm_provider
        self.status = ExecutionStatus.RUNNING

        # Get task manager from session
        task_manager = session_manager.get_task_manager(session_id)
        if not task_manager or task_manager.df is None:
            self.status = ExecutionStatus.FAILED
            return {
                'status': 'error',
                'message': 'No tasks found in session'
            }

        # Get game info from session
        game_info_obj = session_manager.get_game_info(session_id)
        game_info = game_info_obj.to_dict() if game_info_obj else {}

        # Group tasks by batch_id
        batches = self._group_tasks_by_batch(task_manager)

        if not batches:
            self.status = ExecutionStatus.COMPLETED
            return {
                'status': 'completed',
                'message': 'No pending tasks to execute'
            }

        # Initialize statistics
        self.statistics = {
            'total_batches': len(batches),
            'completed_batches': 0,
            'failed_batches': 0,
            'total_tasks': sum(len(tasks) for tasks in batches.values()),
            'completed_tasks': 0,
            'failed_tasks': 0,
            'start_time': datetime.now(),
            'end_time': None
        }

        self.logger.info(
            f"Starting execution for session {session_id}: "
            f"{self.statistics['total_batches']} batches, "
            f"{self.statistics['total_tasks']} tasks"
        )

        # Add batches to queue
        for batch_id, tasks in batches.items():
            await self.queue.put((batch_id, tasks))

        # Start worker tasks
        self.active_workers = []
        for i in range(min(self.max_workers, len(batches))):
            worker = asyncio.create_task(
                self._worker(f"worker_{i}", task_manager, game_info)
            )
            self.active_workers.append(worker)

        # Start monitoring task
        asyncio.create_task(self._monitor_execution())

        return {
            'status': 'started',
            'total_batches': self.statistics['total_batches'],
            'total_tasks': self.statistics['total_tasks'],
            'workers': len(self.active_workers)
        }

    async def stop_execution(self) -> Dict[str, Any]:
        """Stop execution gracefully."""
        if self.status != ExecutionStatus.RUNNING:
            return {
                'status': 'error',
                'message': 'No execution in progress'
            }

        self.logger.info("Stopping execution...")
        self.status = ExecutionStatus.STOPPED

        # Cancel all workers
        for worker in self.active_workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.active_workers, return_exceptions=True)

        # Clear queue
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        self.statistics['end_time'] = datetime.now()

        return {
            'status': 'stopped',
            'completed_batches': self.statistics['completed_batches'],
            'completed_tasks': self.statistics['completed_tasks']
        }

    async def pause_execution(self) -> Dict[str, Any]:
        """Pause execution (can be resumed)."""
        if self.status != ExecutionStatus.RUNNING:
            return {
                'status': 'error',
                'message': 'No execution in progress'
            }

        self.status = ExecutionStatus.PAUSED
        self.logger.info("Execution paused")

        return {'status': 'paused'}

    async def resume_execution(self) -> Dict[str, Any]:
        """Resume paused execution."""
        if self.status != ExecutionStatus.PAUSED:
            return {
                'status': 'error',
                'message': 'Execution is not paused'
            }

        self.status = ExecutionStatus.RUNNING
        self.logger.info("Execution resumed")

        return {'status': 'resumed'}

    def get_status(self) -> Dict[str, Any]:
        """Get current execution status."""
        if not self.current_session_id:
            return {
                'status': self.status.value,
                'message': 'No active execution'
            }

        # Calculate progress
        progress = 0.0
        if self.statistics['total_tasks'] > 0:
            progress = (
                self.statistics['completed_tasks'] / self.statistics['total_tasks']
            ) * 100

        # Calculate estimated time
        estimated_remaining = None
        if self.statistics['completed_tasks'] > 0 and self.statistics['start_time']:
            elapsed = (datetime.now() - self.statistics['start_time']).total_seconds()
            avg_time_per_task = elapsed / self.statistics['completed_tasks']
            remaining_tasks = (
                self.statistics['total_tasks'] - self.statistics['completed_tasks']
            )
            estimated_remaining = int(avg_time_per_task * remaining_tasks)

        return {
            'status': self.status.value,
            'session_id': self.current_session_id,
            'progress': {
                'total': self.statistics['total_tasks'],
                'completed': self.statistics['completed_tasks'],
                'failed': self.statistics['failed_tasks'],
                'pending': (
                    self.statistics['total_tasks'] -
                    self.statistics['completed_tasks'] -
                    self.statistics['failed_tasks']
                )
            },
            'batches': {
                'total': self.statistics['total_batches'],
                'completed': self.statistics['completed_batches'],
                'failed': self.statistics['failed_batches']
            },
            'completion_rate': progress,
            'estimated_remaining_seconds': estimated_remaining,
            'active_workers': len([w for w in self.active_workers if not w.done()]),
            'start_time': (
                self.statistics['start_time'].isoformat()
                if self.statistics['start_time'] else None
            ),
            'end_time': (
                self.statistics['end_time'].isoformat()
                if self.statistics['end_time'] else None
            )
        }

    async def _worker(
        self,
        worker_name: str,
        task_manager: TaskDataFrameManager,
        game_info: Dict[str, Any]
    ) -> None:
        """Worker coroutine for processing batches."""
        self.logger.info(f"{worker_name} started")
        executor = RetryableBatchExecutor(self.llm_provider)

        try:
            while self.status in [ExecutionStatus.RUNNING, ExecutionStatus.PAUSED]:
                # Check if paused
                if self.status == ExecutionStatus.PAUSED:
                    await asyncio.sleep(1)
                    continue

                try:
                    # Get batch from queue with timeout
                    batch_id, tasks = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=1.0
                    )

                    self.logger.info(f"{worker_name} processing batch {batch_id}")

                    # Execute batch with session_id for WebSocket progress updates
                    result = await executor.execute_batch(
                        batch_id, tasks, task_manager, self.current_session_id, game_info
                    )

                    # Update statistics
                    self.statistics['completed_batches'] += 1
                    self.statistics['completed_tasks'] += result['successful']
                    self.statistics['failed_tasks'] += result['failed']

                    if result['failed'] > 0:
                        self.statistics['failed_batches'] += 1

                except asyncio.TimeoutError:
                    # No more batches in queue
                    if self.queue.empty():
                        break
                    continue

                except Exception as e:
                    self.logger.error(f"{worker_name} error: {str(e)}")
                    self.statistics['failed_batches'] += 1

        except asyncio.CancelledError:
            self.logger.info(f"{worker_name} cancelled")

        self.logger.info(f"{worker_name} finished")

    async def _monitor_execution(self) -> None:
        """Monitor execution progress."""
        while self.status == ExecutionStatus.RUNNING:
            # Check if all workers are done
            if all(worker.done() for worker in self.active_workers):
                self.status = ExecutionStatus.COMPLETED
                self.statistics['end_time'] = datetime.now()

                # ✅ FIX: Save final task_manager and update session state
                if self.current_session_id:
                    try:
                        task_manager = session_manager.get_task_manager(self.current_session_id)
                        task_file_path = session_manager.get_metadata(self.current_session_id, 'task_file_path')

                        if task_manager and task_manager.df is not None and task_file_path:
                            # Save to file
                            task_manager.df.to_parquet(task_file_path, index=False)
                            self.logger.info(f"✅ Saved final task_manager to {task_file_path} ({len(task_manager.df)} tasks)")

                            # ✅ Update session.stage to COMPLETED
                            from models.session_state import SessionStage
                            session = session_manager.get_session(self.current_session_id)
                            if session:
                                session.session_status.update_stage(SessionStage.COMPLETED)

                                # ✅ Sync final realtime_statistics to cache (use separate key)
                                from utils.session_cache import session_cache
                                df = task_manager.df
                                total = len(df)
                                completed = (df['status'] == 'completed').sum()
                                processing = (df['status'] == 'processing').sum()
                                pending = (df['status'] == 'pending').sum()
                                failed = (df['status'] == 'failed').sum()

                                # Use separate cache key to avoid being overwritten by session.to_dict()
                                realtime_key = f'realtime_progress:{self.current_session_id}'
                                realtime_data = {
                                    'total': int(total),
                                    'completed': int(completed),
                                    'processing': int(processing),
                                    'pending': int(pending),
                                    'failed': int(failed),
                                    'completion_rate': 100.0,
                                    'updated_at': datetime.now().isoformat()
                                }
                                session_cache.cache[realtime_key] = realtime_data

                                # Sync session to cache (this won't overwrite realtime_progress)
                                session_manager._sync_to_cache(session)
                                self.logger.info(f"✅ Updated session stage to COMPLETED and synced final stats to cache")

                    except Exception as e:
                        self.logger.error(f"Failed to save final state: {e}")

                # Log final progress (100%)
                final_status = self.get_status()
                self.logger.info(
                    f"Progress: {final_status['completion_rate']:.1f}% "
                    f"({final_status['progress']['completed']}/{final_status['progress']['total']})"
                )
                self.logger.info("Execution completed")
                break

            # Log progress every 10 seconds
            await asyncio.sleep(10)
            status = self.get_status()
            self.logger.info(
                f"Progress: {status['completion_rate']:.1f}% "
                f"({status['progress']['completed']}/{status['progress']['total']})"
            )

    def _group_tasks_by_batch(
        self,
        task_manager: TaskDataFrameManager
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group pending tasks by batch_id."""
        batches = {}

        # Get pending tasks
        pending_df = task_manager.get_pending_tasks()

        if pending_df is not None and not pending_df.empty:
            # Group by batch_id
            for batch_id, group in pending_df.groupby('batch_id'):
                batches[batch_id] = group.to_dict('records')

        return batches


# Global worker pool instance
worker_pool = WorkerPool()