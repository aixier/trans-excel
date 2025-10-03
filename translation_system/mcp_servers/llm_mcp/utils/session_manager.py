"""
Session Manager for LLM MCP Server
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import threading

from models.session_data import TranslationSession, SessionStatus


class SessionManager:
    """Manages translation sessions."""

    def __init__(self, max_sessions: int = 100, session_ttl_hours: int = 24):
        self.sessions: Dict[str, TranslationSession] = {}
        self.max_sessions = max_sessions
        self.session_ttl = timedelta(hours=session_ttl_hours)
        self._lock = threading.RLock()

    def create_session(self, session_type: str = "llm") -> TranslationSession:
        """Create a new translation session."""
        with self._lock:
            # Clean up old sessions if needed
            if len(self.sessions) >= self.max_sessions:
                self.cleanup_expired()

            # Generate unique session ID
            session_id = f"{session_type}_{uuid.uuid4().hex[:12]}"

            # Create new session
            session = TranslationSession(
                session_id=session_id,
                session_type=session_type
            )

            self.sessions[session_id] = session
            return session

    def get_session(self, session_id: str) -> Optional[TranslationSession]:
        """Get session by ID."""
        with self._lock:
            return self.sessions.get(session_id)

    def update_session(self, session_id: str, **kwargs):
        """Update session attributes."""
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                for key, value in kwargs.items():
                    if hasattr(session, key):
                        setattr(session, key, value)
                session.updated_at = datetime.now()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False

    def get_all_sessions(self) -> List[TranslationSession]:
        """Get all sessions."""
        with self._lock:
            return list(self.sessions.values())

    def get_active_sessions(self) -> List[TranslationSession]:
        """Get active translation sessions."""
        with self._lock:
            return [
                s for s in self.sessions.values()
                if s.status in [SessionStatus.TRANSLATING, SessionStatus.PAUSED]
            ]

    def get_session_count(self) -> int:
        """Get total session count."""
        with self._lock:
            return len(self.sessions)

    def cleanup_expired(self, force: bool = False) -> int:
        """Clean up expired sessions."""
        with self._lock:
            now = datetime.now()
            expired_ids = []

            for session_id, session in self.sessions.items():
                # Check if session is expired
                is_expired = (now - session.updated_at) > self.session_ttl

                # Check if session is completed/failed and old
                is_finished_old = (
                    session.status in [SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.STOPPED]
                    and (now - session.updated_at) > timedelta(hours=1)
                )

                if force or is_expired or is_finished_old:
                    expired_ids.append(session_id)

            # Delete expired sessions
            for session_id in expired_ids:
                del self.sessions[session_id]

            return len(expired_ids)

    def find_sessions_by_status(self, status: SessionStatus) -> List[TranslationSession]:
        """Find sessions by status."""
        with self._lock:
            return [
                s for s in self.sessions.values()
                if s.status == status
            ]

    def clear_all(self):
        """Clear all sessions."""
        with self._lock:
            self.sessions.clear()


# Global session manager instance
session_manager = SessionManager()