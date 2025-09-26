"""Session management for storing DataFrame and game info in memory."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from models.excel_dataframe import ExcelDataFrame
from models.task_dataframe import TaskDataFrameManager
from models.game_info import GameInfo


class SessionData:
    """Container for session data."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.excel_df: Optional[ExcelDataFrame] = None
        self.task_manager: Optional[TaskDataFrameManager] = None
        self.game_info: Optional[GameInfo] = None
        self.analysis: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

    def update_access_time(self):
        """Update last accessed time."""
        self.last_accessed = datetime.now()


class SessionManager:
    """Manage sessions with DataFrame and game info."""

    _instance = None
    _sessions: Dict[str, SessionData] = {}
    _session_timeout = timedelta(hours=1)  # Default 1 hour timeout

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_session(self) -> str:
        """Create a new session and return session ID."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = SessionData(session_id)
        self._cleanup_old_sessions()
        return session_id

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data by ID."""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.update_access_time()
            return session
        return None

    def set_excel_df(self, session_id: str, excel_df: ExcelDataFrame) -> bool:
        """Set Excel DataFrame for a session."""
        session = self.get_session(session_id)
        if session:
            session.excel_df = excel_df
            return True
        return False

    def get_excel_df(self, session_id: str) -> Optional[ExcelDataFrame]:
        """Get Excel DataFrame from session."""
        session = self.get_session(session_id)
        return session.excel_df if session else None

    def set_task_manager(self, session_id: str, task_manager: TaskDataFrameManager) -> bool:
        """Set task manager for a session."""
        session = self.get_session(session_id)
        if session:
            session.task_manager = task_manager
            return True
        return False

    def get_task_manager(self, session_id: str) -> Optional[TaskDataFrameManager]:
        """Get task manager from session."""
        session = self.get_session(session_id)
        return session.task_manager if session else None

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