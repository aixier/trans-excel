"""Session manager for excel_mcp (memory-based, singleton)."""

import uuid
import logging
from typing import Dict, Optional
from datetime import datetime

from models.session_data import SessionData


logger = logging.getLogger(__name__)


class SessionManager:
    """Singleton session manager for storing sessions in memory."""

    _instance: Optional['SessionManager'] = None
    _sessions: Dict[str, SessionData] = {}

    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_session(self) -> str:
        """
        Create a new session.

        Returns:
            Session ID
        """
        session_id = f"excel_{uuid.uuid4().hex[:16]}"
        session = SessionData(session_id)
        self._sessions[session_id] = session

        logger.info(f"Created session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            SessionData if found, None otherwise
        """
        session = self._sessions.get(session_id)
        if session:
            session.update_last_accessed()
        return session

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session.

        Args:
            session_id: Session ID

        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False

    def cleanup_expired_sessions(self, timeout_hours: int = 8):
        """
        Clean up expired sessions.

        Args:
            timeout_hours: Timeout in hours (default: 8)
        """
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired(timeout_hours)
        ]

        for session_id in expired:
            self.delete_session(session_id)

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    def get_session_count(self) -> int:
        """Get total number of sessions."""
        return len(self._sessions)


# Global singleton instance
session_manager = SessionManager()
