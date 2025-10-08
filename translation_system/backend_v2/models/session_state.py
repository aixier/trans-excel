"""Session state management module.

This module provides state management for translation sessions,
tracking the global stage of each session in the workflow.
"""

from enum import Enum
from typing import Dict, Any
from datetime import datetime


class SessionStage(Enum):
    """Session global stage - coarse-grained state tracking.

    Represents the main stages in the translation workflow:
    CREATED -> ANALYZED -> SPLIT_COMPLETE -> EXECUTING -> COMPLETED
    """
    CREATED = "created"              # Session created, ready for upload
    ANALYZED = "analyzed"            # Analysis complete, ready for split
    SPLIT_COMPLETE = "split_complete"  # Split complete, ready for execution
    EXECUTING = "executing"          # Execution in progress
    COMPLETED = "completed"          # All complete, ready for download
    FAILED = "failed"                # Session failed

    def can_split(self) -> bool:
        """Check if session can start splitting tasks.

        Returns:
            True if session is in ANALYZED stage
        """
        return self == SessionStage.ANALYZED

    def can_execute(self) -> bool:
        """Check if session can start execution.

        Returns:
            True if session is in SPLIT_COMPLETE stage
        """
        return self == SessionStage.SPLIT_COMPLETE

    def can_download(self) -> bool:
        """Check if session can download results.

        Returns:
            True if session is in COMPLETED stage
        """
        return self == SessionStage.COMPLETED


class SessionStatus:
    """Session status container - single source of truth for session state.

    Attributes:
        session_id: Unique session identifier
        stage: Current session stage
        updated_at: Last update timestamp
    """

    def __init__(self, session_id: str):
        """Initialize session status.

        Args:
            session_id: Unique session identifier
        """
        self.session_id = session_id
        self.stage = SessionStage.CREATED
        self.updated_at = datetime.now()

    def update_stage(self, stage: SessionStage):
        """Update session stage.

        Args:
            stage: New session stage
        """
        self.stage = stage
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for API responses.

        Returns:
            Dictionary containing session status fields
        """
        return {
            "session_id": self.session_id,
            "stage": self.stage.value,
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionStatus':
        """Deserialize from dictionary.

        Args:
            data: Dictionary containing session status fields

        Returns:
            SessionStatus instance
        """
        session_id = data["session_id"]
        status = cls(session_id)
        status.stage = SessionStage(data["stage"])
        status.updated_at = datetime.fromisoformat(data["updated_at"])
        return status
