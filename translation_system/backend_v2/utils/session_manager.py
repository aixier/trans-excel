"""Session management for storing DataFrame and game info in memory."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import logging

from models.excel_dataframe import ExcelDataFrame
from models.task_dataframe import TaskDataFrameManager
from models.game_info import GameInfo
from models.session_state import SessionStage, SessionStatus
from services.split_state import SplitProgress
from services.execution_state import ExecutionProgress

logger = logging.getLogger(__name__)


class SessionData:
    """Container for session data with integrated state management."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()

        # Data storage
        self.excel_df: Optional[ExcelDataFrame] = None
        self.task_manager: Optional[TaskDataFrameManager] = None
        self.game_info: Optional[GameInfo] = None
        self.analysis: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

        # ✨ State management modules (Plan B integration)
        self.session_status = SessionStatus(session_id)
        self.split_progress: Optional[SplitProgress] = None
        self.execution_progress: Optional[ExecutionProgress] = None

    def update_access_time(self):
        """Update last accessed time."""
        self.last_accessed = datetime.now()

    def init_split_progress(self) -> SplitProgress:
        """Initialize split progress tracking.

        Returns:
            SplitProgress instance for this session
        """
        if not self.split_progress:
            self.split_progress = SplitProgress(self.session_id)
        return self.split_progress

    def init_execution_progress(self) -> ExecutionProgress:
        """Initialize execution progress tracking.

        Returns:
            ExecutionProgress instance for this session
        """
        if not self.execution_progress:
            self.execution_progress = ExecutionProgress(self.session_id)
        return self.execution_progress

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session to dictionary (excluding heavy DataFrames).

        Used for multi-worker session sharing via diskcache.
        Only serializes lightweight metadata and state information.

        Returns:
            Dictionary containing session metadata (without DataFrames)
        """
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'analysis': self.analysis,
            'metadata': self.metadata,
            'session_status': self.session_status.to_dict(),
            'split_progress': self.split_progress.to_dict() if self.split_progress else None,
            'execution_progress': self.execution_progress.to_dict() if self.execution_progress else None,
            # ❌ Not including: excel_df, task_manager, game_info (heavy data)
            # But we include file paths for lazy loading
            'task_file_path': self.metadata.get('task_file_path'),
            'excel_file_path': self.metadata.get('excel_file_path'),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Deserialize session from dictionary.

        Args:
            data: Dictionary containing session metadata

        Returns:
            SessionData instance (without DataFrames, need to load separately)
        """
        session = cls(data['session_id'])
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.last_accessed = datetime.fromisoformat(data['last_accessed'])
        session.analysis = data.get('analysis', {})
        session.metadata = data.get('metadata', {})

        # Restore state modules
        if data.get('session_status'):
            session.session_status = SessionStatus.from_dict(data['session_status'])
        if data.get('split_progress'):
            session.split_progress = SplitProgress.from_dict(data['split_progress'])
        if data.get('execution_progress'):
            session.execution_progress = ExecutionProgress.from_dict(data['execution_progress'])

        # Note: excel_df, task_manager, game_info need to be loaded separately
        return session


class SessionManager:
    """Manage sessions with DataFrame and game info.

    Architecture:
        - Memory cache: Fast access for current worker
        - diskcache: Shared storage across all workers
        - DataFrames: Kept in memory only, loaded on demand
    """

    _instance = None
    _sessions: Dict[str, SessionData] = {}
    _session_timeout = timedelta(hours=8)  # 8 hours timeout

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize diskcache for multi-worker session sharing
            cls._init_cache()
        return cls._instance

    @classmethod
    def _init_cache(cls):
        """Initialize session cache (lazy loading to avoid circular import)."""
        if not hasattr(cls, '_cache'):
            try:
                from utils.session_cache import session_cache
                cls._cache = session_cache
                logger.info("SessionManager initialized with diskcache support")
            except Exception as e:
                logger.warning(f"Failed to initialize session cache: {e}")
                logger.warning("Multi-worker session sharing will not work")
                cls._cache = None

    def create_session(self) -> str:
        """Create a new session and return session ID."""
        session_id = str(uuid.uuid4())
        session = SessionData(session_id)
        self._sessions[session_id] = session

        # Sync to cache for multi-worker visibility
        self._sync_to_cache(session)

        self._cleanup_old_sessions()
        logger.info(f"Created session {session_id} (synced to cache)")
        return session_id

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data by ID (with multi-worker support).

        Strategy:
            1. Check memory cache (fast path)
            2. Check diskcache (cross-worker)
            3. Return None if not found

        Note:
            DataFrames (excel_df, task_manager) are not in cache,
            they need to be loaded separately using get/set methods.
        """
        # Fast path: Check memory cache first
        if session_id in self._sessions:
            session = self._sessions[session_id]

            # ✅ Refresh all state objects from cache (for cross-worker updates)
            # This ensures we always have the latest state without reloading DataFrames
            if hasattr(self, '_cache') and self._cache:
                try:
                    cached_data = self._cache.get_session(session_id)
                    if cached_data:
                        # Refresh metadata (task_file_path, excel_file_path, etc.)
                        if 'metadata' in cached_data:
                            session.metadata.update(cached_data['metadata'])
                            logger.debug(f"Refreshed metadata from cache for session {session_id}")

                        # Refresh session_status (stage updates like ANALYZED, SPLIT_COMPLETE)
                        if 'session_status' in cached_data:
                            session.session_status = SessionStatus.from_dict(cached_data['session_status'])
                            logger.debug(f"Refreshed session_status from cache for session {session_id}")

                        # Refresh split_progress (split state)
                        if 'split_progress' in cached_data and cached_data['split_progress']:
                            session.split_progress = SplitProgress.from_dict(cached_data['split_progress'])
                            logger.debug(f"Refreshed split_progress from cache for session {session_id}")

                        # Refresh execution_progress (execution state)
                        if 'execution_progress' in cached_data and cached_data['execution_progress']:
                            session.execution_progress = ExecutionProgress.from_dict(cached_data['execution_progress'])
                            logger.debug(f"Refreshed execution_progress from cache for session {session_id}")
                except Exception as e:
                    logger.debug(f"Failed to refresh state from cache: {e}")

            session.update_access_time()
            # Update cache with latest access time
            self._sync_to_cache(session)
            return session

        # Slow path: Check diskcache (may be from another worker)
        if hasattr(self, '_cache') and self._cache:
            try:
                cached_data = self._cache.get_session(session_id)
                if cached_data:
                    # Restore session from cache
                    session = SessionData.from_dict(cached_data)
                    # Add to memory cache
                    self._sessions[session_id] = session
                    logger.info(f"Restored session {session_id} from cache")
                    return session
            except Exception as e:
                logger.error(f"Failed to restore session {session_id} from cache: {e}")

        return None

    def _sync_to_cache(self, session: SessionData):
        """Synchronize session metadata to cache.

        Args:
            session: SessionData instance to sync
        """
        if hasattr(self, '_cache') and self._cache:
            try:
                self._cache.set_session(session.session_id, session.to_dict())
            except Exception as e:
                logger.error(f"Failed to sync session {session.session_id} to cache: {e}")

    def set_excel_df(self, session_id: str, excel_df: ExcelDataFrame) -> bool:
        """Set Excel DataFrame for a session."""
        session = self.get_session(session_id)
        if session:
            session.excel_df = excel_df
            return True
        return False

    def get_excel_df(self, session_id: str) -> Optional[ExcelDataFrame]:
        """Get Excel DataFrame from session.

        Supports lazy loading from file if not in memory (for cross-worker access).
        """
        session = self.get_session(session_id)
        if not session:
            return None

        # Fast path: excel_df already in memory
        if session.excel_df:
            return session.excel_df

        # Slow path: try to load from file (cross-worker scenario)
        excel_file_path = session.metadata.get('excel_file_path')
        logger.info(f"[DEBUG] get_excel_df for {session_id}: excel_file_path={excel_file_path}")

        if excel_file_path:
            try:
                import os
                from models.excel_dataframe import ExcelDataFrame

                logger.info(f"Attempting to load excel_df from file: {excel_file_path}")
                if os.path.exists(excel_file_path):
                    logger.info(f"Loading excel_df from file for session {session_id} (cross-worker)")
                    excel_df = ExcelDataFrame.load_from_pickle(excel_file_path)
                    # Cache in memory for future requests
                    session.excel_df = excel_df
                    logger.info(f"Loaded excel_df from {excel_file_path}")
                    return excel_df
                else:
                    logger.warning(f"Excel file not found: {excel_file_path}")
            except Exception as e:
                logger.error(f"Failed to load excel_df from file: {e}", exc_info=True)
        else:
            logger.warning(f"No excel_file_path in metadata for session {session_id}")

        return None

    def get_excel_manager(self, session_id: str) -> Optional[ExcelDataFrame]:
        """Get Excel manager from session (alias for get_excel_df)."""
        return self.get_excel_df(session_id)

    def set_task_manager(self, session_id: str, task_manager: TaskDataFrameManager) -> bool:
        """Set task manager for a session."""
        session = self.get_session(session_id)
        if session:
            session.task_manager = task_manager
            return True
        return False

    def get_task_manager(self, session_id: str) -> Optional[TaskDataFrameManager]:
        """Get task manager from session.

        Supports lazy loading from file if not in memory (for cross-worker access).
        """
        session = self.get_session(session_id)
        if not session:
            return None

        # Fast path: task_manager already in memory
        if session.task_manager:
            return session.task_manager

        # Slow path: try to load from file (cross-worker scenario)
        task_file_path = session.metadata.get('task_file_path')
        logger.info(f"[DEBUG] get_task_manager for {session_id}: task_file_path={task_file_path}, metadata={session.metadata}")

        if task_file_path:
            try:
                import os
                from pathlib import Path
                import pandas as pd
                from models.task_dataframe import TaskDataFrameManager

                logger.info(f"Attempting to load task_manager from file: {task_file_path}")
                if os.path.exists(task_file_path):
                    logger.info(f"Loading task_manager from file for session {session_id} (cross-worker)")
                    task_manager = TaskDataFrameManager()
                    task_manager.df = pd.read_parquet(task_file_path)
                    # Cache in memory for future requests
                    session.task_manager = task_manager
                    logger.info(f"Loaded {len(task_manager.df)} tasks from {task_file_path}")
                    return task_manager
                else:
                    logger.warning(f"Task file not found: {task_file_path}")
            except Exception as e:
                logger.error(f"Failed to load task_manager from file: {e}", exc_info=True)
        else:
            logger.warning(f"No task_file_path in metadata for session {session_id}")

        return None

    def set_game_info(self, session_id: str, game_info: GameInfo) -> bool:
        """Set game info for a session."""
        session = self.get_session(session_id)
        if session:
            session.game_info = game_info
            return True
        return False

    def get_game_info(self, session_id: str) -> Optional[GameInfo]:
        """Get game info from session."""
        session = self.get_session(session_id)
        return session.game_info if session else None

    def set_analysis(self, session_id: str, analysis: Dict[str, Any]) -> bool:
        """Set analysis results for a session."""
        session = self.get_session(session_id)
        if session:
            session.analysis = analysis
            # Sync to cache (analysis is part of session metadata)
            self._sync_to_cache(session)
            return True
        return False

    def get_analysis(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis results from session."""
        session = self.get_session(session_id)
        return session.analysis if session else None

    def set_metadata(self, session_id: str, key: str, value: Any) -> bool:
        """Set metadata value for a session."""
        session = self.get_session(session_id)
        if session:
            session.metadata[key] = value
            # Sync to cache for cross-worker visibility
            self._sync_to_cache(session)
            return True
        return False

    def get_metadata(self, session_id: str, key: str) -> Any:
        """Get metadata value from session."""
        session = self.get_session(session_id)
        return session.metadata.get(key) if session else None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def _cleanup_old_sessions(self):
        """Remove sessions that have timed out."""
        current_time = datetime.now()
        expired_sessions = []

        for session_id, session in self._sessions.items():
            if current_time - session.last_accessed > self._session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self._sessions[session_id]

    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all active sessions."""
        self._cleanup_old_sessions()

        sessions_info = {}
        for session_id, session in self._sessions.items():
            sessions_info[session_id] = {
                'created_at': session.created_at.isoformat(),
                'last_accessed': session.last_accessed.isoformat(),
                'has_excel': session.excel_df is not None,
                'has_tasks': session.task_manager is not None,
                'has_game_info': session.game_info is not None,
                'metadata': session.metadata
            }

        return sessions_info

    def clear_all_sessions(self):
        """Clear all sessions (for testing/reset)."""
        self._sessions.clear()


# Global instance
session_manager = SessionManager()