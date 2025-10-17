"""Worker pool for concurrent batch execution."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from enum import Enum

from services.executor.batch_executor import RetryableBatchExecutor
from services.llm.base_provider import BaseLLMProvider
from models.task_dataframe import TaskDataFrameManager, TaskStatus
from utils.pipeline_session_manager import pipeline_session_manager

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
    """Manage concurrent workers for batch execution (per-session instance)."""

    def __init__(self, session_id: str, max_workers: int = 10):
        """
        Initialize worker pool for a specific session.

        Args:
            session_id: Session identifier this pool manages
            max_workers: Maximum concurrent workers
        """
        self.session_id = session_id
        self.max_workers = max_workers
        self.active_workers = []
        self.queue = asyncio.Queue()
        self.caps_queue = asyncio.Queue()  # Separate queue for caps tasks
        self.status = ExecutionStatus.IDLE
        self.current_session_id = session_id  # Keep for backward compatibility
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
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}[{session_id[:8]}]")

    async def start_execution(
        self,
        llm_provider: BaseLLMProvider,
        glossary_config: Dict[str, Any] = None  # ✨ Glossary configuration
    ) -> Dict[str, Any]:
        """
        Start translation execution for this pool's session.

        Args:
            llm_provider: LLM provider instance
            glossary_config: Glossary configuration

        Returns:
            Execution status
        """
        # Check if THIS pool is already running (not global check)
        if self.status == ExecutionStatus.RUNNING:
            return {
                'status': 'error',
                'message': f'Execution already in progress for session {self.session_id}'
            }

        # session_id is already set in __init__, no need to pass it
        self.llm_provider = llm_provider
        self.glossary_config = glossary_config  # ✨ Store glossary config
        self.status = ExecutionStatus.RUNNING

        # Get task manager from session (use self.session_id)
        task_manager = pipeline_session_manager.get_tasks(self.session_id)
        if not task_manager or task_manager.df is None:
            self.status = ExecutionStatus.FAILED
            return {
                'status': 'error',
                'message': 'No tasks found in session'
            }

        # Get game info from session (if available)
        session = pipeline_session_manager.get_session(self.session_id)
        game_info = session.metadata.get('game_info', {}) if session else {}

        # Group tasks by batch_id and separate caps tasks
        batches, caps_batches = self._group_tasks_by_batch_with_deps(task_manager)

        total_batches = len(batches) + len(caps_batches)
        if total_batches == 0:
            self.status = ExecutionStatus.COMPLETED
            return {
                'status': 'completed',
                'message': 'No pending tasks to execute'
            }

        # Initialize statistics
        self.statistics = {
            'total_batches': total_batches,
            'completed_batches': 0,
            'failed_batches': 0,
            'total_tasks': sum(len(tasks) for tasks in batches.values()) +
                          sum(len(tasks) for tasks in caps_batches.values()),
            'completed_tasks': 0,
            'failed_tasks': 0,
            'start_time': datetime.now(),
            'end_time': None
        }

        self.logger.info(
            f"Starting execution for session {self.session_id}: "
            f"{len(batches)} normal batches, {len(caps_batches)} caps batches, "
            f"{self.statistics['total_tasks']} total tasks"
        )

        # Add non-caps batches to main queue
        for batch_id, tasks in batches.items():
            await self.queue.put((batch_id, tasks))

        # Add caps batches to caps queue (will be processed after normal tasks)
        for batch_id, tasks in caps_batches.items():
            await self.caps_queue.put((batch_id, tasks))

        # Start worker tasks for normal batches
        self.active_workers = []
        num_normal_workers = min(self.max_workers, len(batches))
        for i in range(num_normal_workers):
            worker = asyncio.create_task(
                self._worker(f"worker_{i}", task_manager, game_info, use_caps=False)
            )
            self.active_workers.append(worker)

        # Start monitoring task
        asyncio.create_task(self._monitor_execution_with_caps(task_manager, game_info))

        return {
            'status': 'started',
            'total_batches': self.statistics['total_batches'],
            'total_tasks': self.statistics['total_tasks'],
            'workers': num_normal_workers
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

        # Clear queues
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        while not self.caps_queue.empty():
            try:
                self.caps_queue.get_nowait()
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

        # Get real-time task status from task_manager
        task_manager = pipeline_session_manager.get_tasks(self.current_session_id)
        if task_manager and task_manager.df is not None:
            stats = task_manager.get_statistics()
            total_tasks = stats['total']
            completed_tasks = stats['by_status'].get('completed', 0)
            failed_tasks = stats['by_status'].get('failed', 0)
            pending_tasks = stats['by_status'].get('pending', 0)
        else:
            # Fallback to statistics if task_manager not available
            total_tasks = self.statistics['total_tasks']
            completed_tasks = self.statistics['completed_tasks']
            failed_tasks = self.statistics['failed_tasks']
            pending_tasks = total_tasks - completed_tasks - failed_tasks

        # Calculate progress
        progress = 0.0
        if total_tasks > 0:
            progress = (completed_tasks / total_tasks) * 100

        # Calculate estimated time
        estimated_remaining = None
        if completed_tasks > 0 and self.statistics['start_time']:
            elapsed = (datetime.now() - self.statistics['start_time']).total_seconds()
            avg_time_per_task = elapsed / completed_tasks
            remaining_tasks = total_tasks - completed_tasks
            estimated_remaining = int(avg_time_per_task * remaining_tasks)

        return {
            'status': self.status.value,
            'session_id': self.current_session_id,
            'progress': {
                'total': total_tasks,
                'completed': completed_tasks,
                'failed': failed_tasks,
                'pending': pending_tasks
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
        game_info: Dict[str, Any],
        use_caps: bool = False
    ) -> None:
        """Worker coroutine for processing batches."""
        self.logger.info(f"{worker_name} started (caps={use_caps})")
        executor = RetryableBatchExecutor(self.llm_provider)

        # Choose queue based on worker type
        task_queue = self.caps_queue if use_caps else self.queue

        try:
            while self.status in [ExecutionStatus.RUNNING, ExecutionStatus.PAUSED]:
                # Check if paused
                if self.status == ExecutionStatus.PAUSED:
                    await asyncio.sleep(1)
                    continue

                try:
                    # Get batch from queue with timeout
                    batch_id, tasks = await asyncio.wait_for(
                        task_queue.get(),
                        timeout=1.0
                    )

                    self.logger.info(f"{worker_name} processing batch {batch_id}")

                    # Execute batch with session_id for WebSocket progress updates
                    result = await executor.execute_batch(
                        batch_id,
                        tasks,
                        task_manager,
                        self.current_session_id,
                        game_info,
                        glossary_config=self.glossary_config  # ✨ Pass glossary config
                    )

                    # Update statistics
                    self.statistics['completed_batches'] += 1
                    self.statistics['completed_tasks'] += result['successful']
                    self.statistics['failed_tasks'] += result['failed']

                    if result['failed'] > 0:
                        self.statistics['failed_batches'] += 1

                except asyncio.TimeoutError:
                    # No more batches in queue
                    if task_queue.empty():
                        break
                    continue

                except Exception as e:
                    self.logger.error(f"{worker_name} error: {str(e)}")
                    self.statistics['failed_batches'] += 1

        except asyncio.CancelledError:
            self.logger.info(f"{worker_name} cancelled")

        self.logger.info(f"{worker_name} finished")

    async def _monitor_execution_with_caps(
        self,
        task_manager: TaskDataFrameManager,
        game_info: Dict[str, Any]
    ) -> None:
        """Monitor execution and start caps workers after normal tasks complete."""
        while self.status == ExecutionStatus.RUNNING:
            # Check if all normal workers are done
            normal_workers_done = all(worker.done() for worker in self.active_workers)

            # If normal workers are done and we have caps tasks, start caps workers
            if normal_workers_done and not self.caps_queue.empty():
                self.logger.info("Normal tasks completed, starting CAPS processing")

                # Start caps workers
                caps_workers = []
                num_caps_workers = min(self.max_workers, self.caps_queue.qsize())
                for i in range(num_caps_workers):
                    worker = asyncio.create_task(
                        self._worker(f"caps_worker_{i}", task_manager, game_info, use_caps=True)
                    )
                    caps_workers.append(worker)

                # Add caps workers to active workers
                self.active_workers.extend(caps_workers)

                # Continue monitoring

            # Check if all workers (including caps) are done
            if all(worker.done() for worker in self.active_workers):
                # ✅ IMPORTANT: Save output_state BEFORE updating status to COMPLETED
                # This ensures parent session has output_file_path before any child session tries to inherit
                if self.current_session_id:
                    try:
                        # Use pipeline_session_manager (NEW architecture)
                        from utils.pipeline_session_manager import pipeline_session_manager
                        from models.pipeline_session import TransformationStage
                        import copy

                        task_manager = pipeline_session_manager.get_tasks(self.current_session_id)
                        session = pipeline_session_manager.get_session(self.current_session_id)

                        if task_manager and task_manager.df is not None:
                            # Get task file path from metadata
                            task_file_path = session.metadata.get('task_file_path') if session else None

                            if task_file_path:
                                # Save to file
                                task_manager.df.to_parquet(task_file_path, index=False)
                                self.logger.info(f"✅ Saved final task_manager to {task_file_path} ({len(task_manager.df)} tasks)")

                        # ✅ Merge translation results back to ExcelDataFrame
                        if session and session.input_state and task_manager:
                            # Create a copy of input_state for output
                            output_excel_df = copy.deepcopy(session.input_state)

                            # Get completed tasks
                            completed_tasks = task_manager.df[task_manager.df['status'] == 'completed']

                            # Merge results back to Excel sheets
                            for _, task in completed_tasks.iterrows():
                                sheet_name = task['sheet_name']
                                row_idx = int(task['row_idx'])
                                col_idx = int(task['col_idx'])
                                result = task['result']

                                # Update the DataFrame in output_excel_df
                                if sheet_name in output_excel_df.sheets:
                                    output_excel_df.sheets[sheet_name].iloc[row_idx, col_idx] = result

                            # ✅ Persist output_state to file FIRST before setting in memory
                            # This ensures metadata has output_file_path before any export request arrives
                            try:
                                from pathlib import Path
                                import pickle

                                data_dir = Path(__file__).parent.parent.parent / 'data' / 'sessions'
                                data_dir.mkdir(parents=True, exist_ok=True)
                                output_file = data_dir / f'{self.current_session_id}_output.pkl'

                                with open(output_file, 'wb') as f:
                                    pickle.dump(output_excel_df, f)

                                # Store file path and completion timestamp in metadata BEFORE setting output_state
                                session.metadata['output_file_path'] = str(output_file)
                                session.metadata['output_state_timestamp'] = datetime.now().isoformat()

                                self.logger.info(f"✅ Saved output_state to {output_file}")
                            except Exception as e:
                                self.logger.error(f"Failed to save output_state to file: {e}")

                            # Now set as output_state in memory
                            pipeline_session_manager.set_output_state(self.current_session_id, output_excel_df)
                            self.logger.info(f"✅ Merged {len(completed_tasks)} translation results to output_state")

                        # ✅ Update session.stage to COMPLETED
                        if session:
                            session.update_stage(TransformationStage.COMPLETED)
                            pipeline_session_manager._sync_to_cache(session)
                            self.logger.info(f"✅ Updated session stage to COMPLETED")

                    except Exception as e:
                        self.logger.error(f"Failed to save final state: {e}")

                # ✅ NOW update execution status to COMPLETED (after output_state is saved)
                self.status = ExecutionStatus.COMPLETED
                self.statistics['end_time'] = datetime.now()

                # Log final progress (100%)
                final_status = self.get_status()
                self.logger.info(
                    f"Progress: {final_status['completion_rate']:.1f}% "
                    f"({final_status['progress']['completed']}/{final_status['progress']['total']})"
                )
                self.logger.info("Execution completed")
                break

            # Check more frequently to reduce race window with Progress Tracker
            # Progress Tracker checks every 2s, so we check every 1s to ensure
            # output_state is saved before any WebSocket completion message
            await asyncio.sleep(1)

            # Log detailed progress every 10 iterations (every 10 seconds)
            if hasattr(self, '_monitor_iteration_count'):
                self._monitor_iteration_count += 1
            else:
                self._monitor_iteration_count = 1

            if self._monitor_iteration_count % 10 == 0:
                status = self.get_status()
                self.logger.info(
                    f"Progress: {status['completion_rate']:.1f}% "
                    f"({status['progress']['completed']}/{status['progress']['total']})"
                )

    def _group_tasks_by_batch_with_deps(
        self,
        task_manager: TaskDataFrameManager
    ) -> tuple[Dict[str, List[Dict[str, Any]]], Dict[str, List[Dict[str, Any]]]]:
        """
        Group pending tasks by batch_id, separating caps tasks.

        Returns:
            Tuple of (normal_batches, caps_batches)
        """
        normal_batches = {}
        caps_batches = {}

        # Get pending tasks
        pending_df = task_manager.get_pending_tasks()

        if pending_df is not None and not pending_df.empty:
            # Group by batch_id
            for batch_id, group in pending_df.groupby('batch_id'):
                tasks = group.to_dict('records')

                # Check if this is a caps batch
                if tasks and tasks[0].get('task_type') == 'caps':
                    caps_batches[batch_id] = tasks
                else:
                    normal_batches[batch_id] = tasks

        return normal_batches, caps_batches

    def _group_tasks_by_batch(
        self,
        task_manager: TaskDataFrameManager
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group pending tasks by batch_id (legacy method for compatibility)."""
        batches = {}

        # Get pending tasks
        pending_df = task_manager.get_pending_tasks()

        if pending_df is not None and not pending_df.empty:
            # Group by batch_id
            for batch_id, group in pending_df.groupby('batch_id'):
                batches[batch_id] = group.to_dict('records')

        return batches


# Note: Global worker_pool instance removed - use WorkerPoolManager instead
# from services.executor.worker_pool_manager import worker_pool_manager