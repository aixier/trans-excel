"""Pipeline session manager - Manages transformation sessions.

Each session represents ONE transformation in the pipeline.
Sessions can be chained through parent_session_id.
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import logging
import pandas as pd

from models.pipeline_session import PipelineSession, TransformationStage
from models.excel_dataframe import ExcelDataFrame
from models.task_dataframe import TaskDataFrameManager

logger = logging.getLogger(__name__)


class PipelineSessionManager:
    """Manage pipeline transformation sessions.

    Key improvements over previous architecture:
    - Each session = ONE transformation
    - Sessions are chained via parent_session_id
    - Simpler structure, easier to test
    """

    _instance = None
    _sessions: Dict[str, PipelineSession] = {}
    _session_timeout = timedelta(hours=8)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._init_cache()
        return cls._instance

    @classmethod
    def _init_cache(cls):
        """Initialize session cache (lazy loading)."""
        if not hasattr(cls, '_cache'):
            try:
                from utils.session_cache import session_cache
                cls._cache = session_cache
                logger.info("PipelineSessionManager initialized with cache support")
            except Exception as e:
                logger.warning(f"Failed to initialize cache: {e}")
                cls._cache = None

    def create_session(self, parent_session_id: Optional[str] = None) -> PipelineSession:
        """Create a new transformation session.

        Args:
            parent_session_id: If chaining, the parent session ID

        Returns:
            New PipelineSession instance
        """
        session = PipelineSession(parent_session_id=parent_session_id)

        # If parent exists, register as child
        if parent_session_id:
            parent = self.get_session(parent_session_id)
            if parent:
                parent.add_child_session(session.session_id)
                session.input_source = 'parent_session'
                # Sync parent to cache
                self._sync_to_cache(parent)
            else:
                logger.warning(f"Parent session {parent_session_id} not found")

        self._sessions[session.session_id] = session
        self._sync_to_cache(session)

        logger.info(f"Created session {session.session_id}, parent={parent_session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[PipelineSession]:
        """Get session by ID (with cache support).

        Args:
            session_id: Session ID

        Returns:
            PipelineSession or None if not found
        """
        # Fast path: memory cache
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.update_access_time()
            self._sync_to_cache(session)
            return session

        # Slow path: disk cache
        if hasattr(self, '_cache') and self._cache:
            try:
                cached_data = self._cache.get_session(session_id)
                if cached_data:
                    session = PipelineSession.from_dict(cached_data)
                    self._sessions[session_id] = session
                    logger.info(f"Restored session {session_id} from cache")
                    return session
            except Exception as e:
                logger.error(f"Failed to restore session from cache: {e}")

        return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted successfully
        """
        if session_id in self._sessions:
            # Also delete from cache
            if hasattr(self, '_cache') and self._cache:
                try:
                    self._cache.delete_session(session_id)
                except Exception as e:
                    logger.error(f"Failed to delete session from cache: {e}")

            del self._sessions[session_id]
            logger.info(f"Deleted session {session_id}")
            return True
        return False

    def _sync_to_cache(self, session: PipelineSession):
        """Sync session metadata to cache.

        Args:
            session: Session to sync
        """
        if hasattr(self, '_cache') and self._cache:
            try:
                self._cache.set_session(session.session_id, session.to_dict())
            except Exception as e:
                logger.error(f"Failed to sync session to cache: {e}")

    # --- Input State Management ---

    def set_input_from_file(self, session_id: str, excel_df: ExcelDataFrame) -> bool:
        """Set input state from uploaded file.

        Args:
            session_id: Session ID
            excel_df: Excel DataFrame

        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if session:
            session.input_state = excel_df
            session.input_source = 'file'
            session.update_stage(TransformationStage.INPUT_LOADED)
            self._sync_to_cache(session)
            return True
        return False

    def set_input_from_parent(self, session_id: str) -> bool:
        """Set input state from parent session's output.

        Args:
            session_id: Session ID

        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if not session or not session.parent_session_id:
            return False

        parent = self.get_session(session.parent_session_id)
        if not parent or not parent.output_state:
            logger.error(f"Parent session {session.parent_session_id} has no output")
            return False

        session.input_state = parent.output_state
        session.input_source = 'parent_session'
        session.update_stage(TransformationStage.INPUT_LOADED)
        self._sync_to_cache(session)
        logger.info(f"Session {session_id} inherited input from parent {session.parent_session_id}")
        return True

    def get_input_state(self, session_id: str) -> Optional[ExcelDataFrame]:
        """Get input state (with lazy loading).

        Args:
            session_id: Session ID

        Returns:
            ExcelDataFrame or None
        """
        session = self.get_session(session_id)
        if not session:
            return None

        # Fast path: already in memory
        if session.input_state:
            return session.input_state

        # Slow path: load from file
        input_file_path = session.metadata.get('input_file_path')
        if input_file_path:
            try:
                import os
                if os.path.exists(input_file_path):
                    session.input_state = ExcelDataFrame.load_from_pickle(input_file_path)
                    logger.info(f"Loaded input_state from {input_file_path}")
                    return session.input_state
            except Exception as e:
                logger.error(f"Failed to load input_state: {e}")

        return None

    # --- Task Management ---

    def set_tasks(self, session_id: str, tasks: TaskDataFrameManager, statistics: Dict = None) -> bool:
        """Set generated tasks.

        Args:
            session_id: Session ID
            tasks: Task DataFrame manager
            statistics: Task generation statistics

        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if session:
            session.tasks = tasks
            session.task_statistics = statistics or {}
            session.update_stage(TransformationStage.SPLIT_COMPLETE)
            self._sync_to_cache(session)
            return True
        return False

    def get_tasks(self, session_id: str) -> Optional[TaskDataFrameManager]:
        """Get tasks (with lazy loading).

        Args:
            session_id: Session ID

        Returns:
            TaskDataFrameManager or None
        """
        session = self.get_session(session_id)
        if not session:
            return None

        # Fast path: already in memory
        if session.tasks:
            return session.tasks

        # Slow path: load from file
        task_file_path = session.metadata.get('task_file_path')
        if task_file_path:
            try:
                import os
                if os.path.exists(task_file_path):
                    task_manager = TaskDataFrameManager()
                    task_manager.df = pd.read_parquet(task_file_path)
                    session.tasks = task_manager
                    logger.info(f"Loaded tasks from {task_file_path}")
                    return task_manager
            except Exception as e:
                logger.error(f"Failed to load tasks: {e}")

        return None

    # --- Output State Management ---

    def set_output_state(self, session_id: str, output_state: ExcelDataFrame, statistics: Dict = None) -> bool:
        """Set output state after execution.

        Args:
            session_id: Session ID
            output_state: Result Excel DataFrame
            statistics: Execution statistics

        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if session:
            session.output_state = output_state
            session.execution_statistics = statistics or {}
            session.update_stage(TransformationStage.COMPLETED)
            self._sync_to_cache(session)
            return True
        return False

    def get_output_state(self, session_id: str) -> Optional[ExcelDataFrame]:
        """Get output state (with lazy loading).

        Args:
            session_id: Session ID

        Returns:
            ExcelDataFrame or None
        """
        session = self.get_session(session_id)
        if not session:
            return None

        # Fast path: already in memory
        if session.output_state:
            return session.output_state

        # Slow path: load from file
        output_file_path = session.metadata.get('output_file_path')
        if output_file_path:
            try:
                import os
                if os.path.exists(output_file_path):
                    session.output_state = ExcelDataFrame.load_from_pickle(output_file_path)
                    logger.info(f"Loaded output_state from {output_file_path}")
                    return session.output_state
            except Exception as e:
                logger.error(f"Failed to load output_state: {e}")

        return None

    # --- Metadata ---

    def set_metadata(self, session_id: str, key: str, value) -> bool:
        """Set metadata value.

        Args:
            session_id: Session ID
            key: Metadata key
            value: Metadata value

        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if session:
            session.metadata[key] = value
            self._sync_to_cache(session)
            return True
        return False

    def get_metadata(self, session_id: str, key: str):
        """Get metadata value.

        Args:
            session_id: Session ID
            key: Metadata key

        Returns:
            Metadata value or None
        """
        session = self.get_session(session_id)
        return session.metadata.get(key) if session else None

    # --- Utilities ---

    def get_session_chain(self, session_id: str) -> list:
        """Get the full chain of sessions from root to this session.

        Args:
            session_id: Session ID

        Returns:
            List of session IDs from root to current
        """
        chain = []
        current_id = session_id

        while current_id:
            session = self.get_session(current_id)
            if not session:
                break
            chain.insert(0, current_id)  # Add to front
            current_id = session.parent_session_id

        return chain

    def cleanup_old_sessions(self):
        """Remove sessions that have timed out."""
        current_time = datetime.now()
        expired = []

        for session_id, session in self._sessions.items():
            if current_time - session.last_accessed > self._session_timeout:
                expired.append(session_id)

        for session_id in expired:
            self.delete_session(session_id)

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")


# Global instance
pipeline_session_manager = PipelineSessionManager()
