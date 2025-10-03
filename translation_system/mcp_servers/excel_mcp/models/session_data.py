"""Session data model for excel_mcp."""

from datetime import datetime
from typing import Any, Dict, Optional, List
from enum import Enum


class SessionStatus(Enum):
    """Session status enum."""
    QUEUED = "queued"
    ANALYZING = "analyzing"
    SPLITTING = "splitting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionData:
    """Session data for storing analysis and task splitting state and results."""

    def __init__(self, session_id: str):
        """
        Initialize session data.

        Args:
            session_id: Unique session identifier
        """
        self.session_id = session_id
        self.status = SessionStatus.QUEUED
        self.progress = 0
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()

        # Excel data
        self.excel_df: Optional[Any] = None  # Will hold Excel DataFrame
        self.file_info: Optional[Dict[str, Any]] = None

        # Analysis results
        self.analysis: Optional[Dict[str, Any]] = None
        self.has_analysis: bool = False

        # Task splitting results (NEW)
        self.tasks: List[Dict[str, Any]] = []
        self.tasks_summary: Optional[Dict[str, Any]] = None
        self.has_tasks: bool = False

        # Error information
        self.error: Optional[Dict[str, str]] = None

        # Metadata
        self.metadata: Dict[str, Any] = {}

    def update_last_accessed(self):
        """Update last accessed timestamp."""
        self.last_accessed = datetime.now()

    def is_expired(self, timeout_hours: int = 8) -> bool:
        """
        Check if session is expired.

        Args:
            timeout_hours: Timeout in hours (default: 8)

        Returns:
            True if expired, False otherwise
        """
        elapsed = datetime.now() - self.last_accessed
        return elapsed.total_seconds() > timeout_hours * 3600

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert session data to dictionary.

        Returns:
            Dictionary representation
        """
        result = {
            "session_id": self.session_id,
            "status": self.status.value,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "has_analysis": self.has_analysis,
            "has_tasks": self.has_tasks,
            "file_info": self.file_info,
            "error": self.error,
            "metadata": self.metadata
        }

        # Include analysis result if available
        if self.has_analysis and self.analysis:
            result["analysis"] = self.analysis

        # Include tasks result if available
        if self.has_tasks:
            result["tasks"] = {
                "summary": self.tasks_summary,
                "count": len(self.tasks)
            }

        return result
