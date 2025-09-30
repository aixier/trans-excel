"""Task persister for automatic persistence to MySQL."""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import pandas as pd

# 禁用持久化服务 - 改为纯内存运行
# from database.mysql_connector import mysql_connector
from models.task_dataframe import TaskDataFrameManager, TaskStatus
from utils.session_manager import session_manager

logger = logging.getLogger(__name__)


class TaskPersister:
    """Automatically persist task states to MySQL."""

    def __init__(self, persist_interval: int = 30):
        """
        Initialize task persister.

        Args:
            persist_interval: Interval between persistence operations (seconds)
        """
        self.persist_interval = persist_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        self.active_sessions: Dict[str, asyncio.Task] = {}
        self.persisted_tasks: Dict[str, Set[str]] = {}  # Track persisted task IDs
        self.task_versions: Dict[str, Dict[str, int]] = {}  # Track task version numbers
        self.session_created: Set[str] = set()  # Track sessions already created in DB

    async def start_auto_persist(self, session_id: str):
        """
        Start automatic persistence for a session.

        Args:
            session_id: Session ID
        """
        # 禁用持久化服务 - 改为纯内存运行
        self.logger.info(f"Auto-persistence disabled (memory-only mode) for session {session_id}")
        return

        # # Stop existing persistence task if any
        # await self.stop_auto_persist(session_id)
        #
        # # Initialize tracking structures
        # self.persisted_tasks[session_id] = set()
        # self.task_versions[session_id] = {}
        #
        # # Create and store the persistence task
        # task = asyncio.create_task(self._persist_loop(session_id))
        # self.active_sessions[session_id] = task
        #
        # self.logger.info(f"Started auto-persistence for session {session_id}")

    async def stop_auto_persist(self, session_id: str):
        """
        Stop automatic persistence for a session.

        Args:
            session_id: Session ID
        """
        # 禁用持久化服务 - 改为纯内存运行
        self.logger.info(f"Auto-persistence already disabled (memory-only mode) for session {session_id}")
        return

        # if session_id in self.active_sessions:
        #     task = self.active_sessions[session_id]
        #     task.cancel()
        #     try:
        #         await task
        #     except asyncio.CancelledError:
        #         pass
        #     del self.active_sessions[session_id]
        #
        #     # Clean up tracking structures
        #     self.persisted_tasks.pop(session_id, None)
        #     self.task_versions.pop(session_id, None)
        #
        #     self.logger.info(f"Stopped auto-persistence for session {session_id}")

    async def _persist_loop(self, session_id: str):
        """
        Persistence loop for a session.

        Args:
            session_id: Session ID
        """
        while True:
            try:
                await asyncio.sleep(self.persist_interval)
                await self.persist_tasks(session_id)
                
                # Check if execution is complete
                task_manager = session_manager.get_task_manager(session_id)
                if task_manager and task_manager.df is not None:
                    df = task_manager.df
                    pending = len(df[df['status'] == TaskStatus.PENDING])
                    processing = len(df[df['status'] == TaskStatus.PROCESSING])
                    
                    if pending == 0 and processing == 0:
                        # All tasks completed, do final persistence
                        await self.persist_tasks(session_id, force=True)
                        self.logger.info(f"Session {session_id} completed, stopping auto-persistence")
                        break
                        
            except asyncio.CancelledError:
                # Task was cancelled, do final persistence
                await self.persist_tasks(session_id, force=True)
                raise
            except Exception as e:
                self.logger.error(f"Error in persistence loop for session {session_id}: {e}")
                await asyncio.sleep(self.persist_interval)

    async def persist_tasks(self, session_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Persist tasks to MySQL.

        Args:
            session_id: Session ID
            force: Force persistence of all tasks

        Returns:
            Persistence statistics
        """
        # 禁用持久化服务 - 改为纯内存运行
        # 返回空统计
        return {
            'new_tasks': 0,
            'updated_tasks': 0,
            'unchanged_tasks': 0,
            'failed': 0
        }

        # start_time = datetime.now()
        # stats = {
        #     'new_tasks': 0,
        #     'updated_tasks': 0,
        #     'unchanged_tasks': 0,
        #     'failed': 0
        # }
        #
        # try:
        #     # Get task manager
            task_manager = session_manager.get_task_manager(session_id)
            if not task_manager or task_manager.df is None:
                self.logger.warning(f"No task manager found for session {session_id}")
                return stats

            df = task_manager.df

            # Ensure session record exists in database (for foreign key constraint)
            await self._ensure_session_exists(session_id)

            # Get persisted task set for this session
            persisted = self.persisted_tasks.get(session_id, set())
            versions = self.task_versions.get(session_id, {})

            # Separate new and existing tasks
            new_tasks = []
            updated_tasks = []

            for idx, task in df.iterrows():
                task_id = task['task_id']
                task_dict = task.to_dict()
                task_dict['session_id'] = session_id
                
                # Calculate task version (simple hash of important fields)
                version = self._calculate_task_version(task_dict)
                
                if task_id not in persisted:
                    # New task
                    new_tasks.append(task_dict)
                    persisted.add(task_id)
                    versions[task_id] = version
                    stats['new_tasks'] += 1
                    
                elif force or versions.get(task_id) != version:
                    # Task has been updated or force update
                    updated_tasks.append(task_dict)
                    versions[task_id] = version
                    stats['updated_tasks'] += 1
                    
                else:
                    # Task unchanged
                    stats['unchanged_tasks'] += 1

            # Persist new tasks using idempotent insert
            if new_tasks:
                await mysql_connector.insert_tasks_idempotent(new_tasks)
                self.logger.debug(f"Inserted {len(new_tasks)} new tasks for session {session_id}")

            # Batch update existing tasks (optimized from individual updates)
            if updated_tasks:
                # Prepare batch updates with session_id
                batch_updates = []
                for task in updated_tasks:
                    update_dict = {
                        'task_id': task['task_id'],
                        'session_id': session_id,  # Add session_id for batch update
                        'status': task.get('status'),
                        'result': task.get('result'),
                        'confidence': task.get('confidence'),
                        'token_count': task.get('token_count'),
                        'cost': task.get('cost', 0),
                        'llm_model': task.get('llm_model'),
                        'error_message': task.get('error_message'),
                        'retry_count': task.get('retry_count', 0),
                        'duration_ms': task.get('duration_ms'),
                        'is_final': task.get('is_final', False),
                        'start_time': task.get('start_time'),
                        'end_time': task.get('end_time')
                    }
                    batch_updates.append(update_dict)

                # Execute batch update in a single query
                affected = await mysql_connector.batch_update_tasks(batch_updates)
                self.logger.debug(f"Batch updated {affected} tasks for session {session_id}")

            # Update session statistics
            await self._update_session_stats(session_id, df)

            # Store updated tracking structures
            self.persisted_tasks[session_id] = persisted
            self.task_versions[session_id] = versions

            stats['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            
            if stats['new_tasks'] > 0 or stats['updated_tasks'] > 0:
                self.logger.info(
                    f"Persisted tasks for session {session_id}: "
                    f"{stats['new_tasks']} new, {stats['updated_tasks']} updated"
                )

            return stats

        except Exception as e:
            self.logger.error(f"Failed to persist tasks for session {session_id}: {e}")
            stats['failed'] = 1
            return stats

    async def _ensure_session_exists(self, session_id: str):
        """
        Ensure session record exists in database before persisting tasks.
        Uses idempotent creation to handle retries and concurrent attempts.

        Args:
            session_id: Session ID
        """
        try:
            # Get session info from memory
            session_data = session_manager.get_session(session_id)
            task_manager = session_manager.get_task_manager(session_id)

            if not session_data or not task_manager:
                self.logger.warning(f"Session data not found in memory for {session_id}")
                return

            # Prepare session data dict
            filename = getattr(session_data, 'filename', 'unknown.xlsx')
            total_tasks = len(task_manager.df) if task_manager.df is not None else 0

            session_dict = {
                'session_id': session_id,
                'filename': filename,
                'file_path': getattr(session_data, 'file_path', ''),
                'status': 'executing',
                'total_tasks': total_tasks,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'processing_tasks': 0,
                'llm_provider': getattr(session_data, 'llm_provider', ''),
                'game_info': getattr(session_data, 'game_info', {}),
                'metadata': getattr(session_data, 'metadata', {})
            }

            # Use idempotent creation - safe for retries and concurrent calls
            await mysql_connector.create_session_idempotent(session_dict)

            # Mark as created (this is just a cache optimization)
            self.session_created.add(session_id)
            self.logger.debug(f"Session record ensured for {session_id}")

        except Exception as e:
            # Don't add to session_created set on failure
            self.session_created.discard(session_id)
            self.logger.error(f"Failed to ensure session exists: {e}")
            # Re-raise to prevent task persistence from continuing
            raise RuntimeError(f"Cannot persist tasks: session record creation failed - {e}")

    def _calculate_task_version(self, task: Dict[str, Any]) -> int:
        """
        Calculate a version number for a task based on its important fields.

        Args:
            task: Task dictionary

        Returns:
            Version number (hash)
        """
        # Include only fields that indicate a meaningful change
        important_fields = [
            'status', 'result', 'confidence', 'token_count',
            'error_message', 'retry_count', 'is_final'
        ]
        
        version_string = '|'.join(
            str(task.get(field, '')) for field in important_fields
        )
        
        return hash(version_string)

    async def _update_session_stats(self, session_id: str, df: pd.DataFrame):
        """
        Update session statistics in database.

        Args:
            session_id: Session ID
            df: Task DataFrame
        """
        try:
            # Calculate statistics
            total = len(df)
            completed = len(df[df['status'] == TaskStatus.COMPLETED])
            failed = len(df[df['status'] == TaskStatus.FAILED])
            processing = len(df[df['status'] == TaskStatus.PROCESSING])

            # Determine session status
            if processing > 0:
                session_status = 'executing'
            elif total == completed + failed and total > 0:
                session_status = 'completed' if failed == 0 else 'completed_with_errors'
            else:
                session_status = 'executing'

            # Update session in database
            await mysql_connector.update_session(
                session_id,
                {
                    'status': session_status,
                    'total_tasks': total,
                    'completed_tasks': completed,
                    'failed_tasks': failed,
                    'processing_tasks': processing
                }
            )

            # Also call stored procedure for comprehensive update
            await mysql_connector.update_session_statistics(session_id)

        except Exception as e:
            self.logger.error(f"Failed to update session stats: {e}")

    async def persist_single_task(self, session_id: str, task_id: str):
        """
        Immediately persist a single task.

        Args:
            session_id: Session ID
            task_id: Task ID
        """
        try:
            task_manager = session_manager.get_task_manager(session_id)
            if not task_manager:
                return

            task_data = task_manager.get_task(task_id)
            if not task_data:
                return

            # Check if task exists in database
            if task_id in self.persisted_tasks.get(session_id, set()):
                # Update existing task
                await mysql_connector.update_task(
                    task_id,
                    {
                        'status': task_data.get('status'),
                        'result': task_data.get('result'),
                        'confidence': task_data.get('confidence'),
                        'token_count': task_data.get('token_count'),
                        'cost': task_data.get('cost', 0),
                        'llm_model': task_data.get('llm_model'),
                        'error_message': task_data.get('error_message'),
                        'duration_ms': task_data.get('duration_ms'),
                        'is_final': task_data.get('is_final', False)
                    }
                )
            else:
                # Insert new task
                task_data['session_id'] = session_id
                await mysql_connector.insert_tasks([task_data])
                
                # Track as persisted
                if session_id not in self.persisted_tasks:
                    self.persisted_tasks[session_id] = set()
                self.persisted_tasks[session_id].add(task_id)

        except Exception as e:
            self.logger.error(f"Failed to persist single task {task_id}: {e}")

    async def load_tasks_from_db(self, session_id: str) -> pd.DataFrame:
        """
        Load tasks from database for a session.

        Args:
            session_id: Session ID

        Returns:
            DataFrame with tasks
        """
        try:
            tasks = await mysql_connector.get_tasks_by_session(session_id)
            if tasks:
                df = pd.DataFrame(tasks)
                # Track loaded tasks as persisted
                self.persisted_tasks[session_id] = set(df['task_id'].tolist())
                return df
            return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Failed to load tasks from database: {e}")
            return pd.DataFrame()

    def get_persistence_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get persistence status for a session.

        Args:
            session_id: Session ID

        Returns:
            Persistence status information
        """
        return {
            'auto_persist_active': session_id in self.active_sessions,
            'persisted_task_count': len(self.persisted_tasks.get(session_id, set())),
            'persist_interval': self.persist_interval
        }


# Global task persister instance
task_persister = TaskPersister()