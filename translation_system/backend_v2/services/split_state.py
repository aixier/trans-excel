"""Split state management module.

This module provides state management for the task splitting phase,
tracking progress, status, and readiness for the next stage.
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class SplitStatus(Enum):
    """Split process status.

    Tracks the overall status of the splitting operation.
    """
    NOT_STARTED = "not_started"
    PROCESSING = "processing"    # Computing tasks
    SAVING = "saving"            # ✨ KEY: Saving to storage (fixes race condition)
    COMPLETED = "completed"      # Complete and verified
    FAILED = "failed"


class SplitStage(Enum):
    """Split internal stages.

    Tracks the detailed progress within the splitting operation.
    """
    ANALYZING = "analyzing"       # Analyzing sheets
    ALLOCATING = "allocating"     # Allocating batches
    CREATING_DF = "creating_df"   # Creating DataFrame
    SAVING = "saving"             # ✨ KEY: Saving data
    VERIFYING = "verifying"       # Verifying integrity
    DONE = "done"


class SplitProgress:
    """Split progress manager - independent and testable.

    This class manages the state and progress of the task splitting phase.
    It is the single source of truth for whether splitting is ready for
    the next stage (execution).

    Attributes:
        session_id: Unique session identifier
        status: Current split status
        stage: Current split stage
        progress: Progress percentage (0-100)
        message: User-facing message
        ready_for_next_stage: ✨ KEY: Whether ready for execution
        metadata: Additional metadata (task count, batch count, etc.)
        error: Error message if failed
        updated_at: Last update timestamp
    """

    def __init__(self, session_id: str):
        """Initialize split progress.

        Args:
            session_id: Unique session identifier
        """
        self.session_id = session_id
        self.status = SplitStatus.NOT_STARTED
        self.stage = SplitStage.ANALYZING
        self.progress: float = 0.0  # 0-100
        self.message: str = ""
        self.ready_for_next_stage: bool = False  # ✨ KEY: Default False
        self.metadata: Dict[str, Any] = {}
        self.error: Optional[str] = None
        self.updated_at = datetime.now()

    def update(self,
               status: Optional[SplitStatus] = None,
               stage: Optional[SplitStage] = None,
               progress: Optional[float] = None,
               message: Optional[str] = None):
        """Update progress fields.

        Args:
            status: New status (optional)
            stage: New stage (optional)
            progress: New progress percentage (optional)
            message: New message (optional)
        """
        if status is not None:
            self.status = status
        if stage is not None:
            self.stage = stage
        if progress is not None:
            self.progress = progress
        if message is not None:
            self.message = message
        self.updated_at = datetime.now()

    def mark_saving(self):
        """Mark as saving - KEY METHOD to fix race condition.

        This method is called BEFORE saving to storage, ensuring that
        the frontend doesn't proceed to execution while saving is in progress.

        This fixes the 0-42 second race condition window.
        """
        self.status = SplitStatus.SAVING
        self.stage = SplitStage.SAVING
        self.ready_for_next_stage = False  # ✨ Must be False during save
        self.updated_at = datetime.now()

    def mark_completed(self, metadata: Dict[str, Any]):
        """Mark as completed - ONLY method that sets ready_for_next_stage=True.

        This method is called AFTER successful save and verification,
        indicating that the session is truly ready for execution.

        Args:
            metadata: Completion metadata (task_count, batch_count, etc.)
        """
        self.status = SplitStatus.COMPLETED
        self.stage = SplitStage.DONE
        self.progress = 100.0
        self.ready_for_next_stage = True  # ✨ Only here is it True
        self.metadata = metadata
        self.updated_at = datetime.now()

    def mark_failed(self, error: str):
        """Mark as failed.

        Args:
            error: Error message
        """
        self.status = SplitStatus.FAILED
        self.error = error
        self.ready_for_next_stage = False
        self.updated_at = datetime.now()

    def is_ready(self) -> bool:
        """Check if ready for next stage - VALIDATION METHOD.

        This method should be called by execute_api to verify that
        splitting is truly complete before allowing execution to start.

        Returns:
            True only if status is COMPLETED and ready flag is True
        """
        return (
            self.status == SplitStatus.COMPLETED and
            self.ready_for_next_stage is True
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for API responses.

        Returns:
            Dictionary containing all progress fields
        """
        data = {
            "session_id": self.session_id,
            "status": self.status.value,
            "stage": self.stage.value,
            "progress": self.progress,
            "message": self.message,
            "ready_for_next_stage": self.ready_for_next_stage,  # ✨ KEY field
            "updated_at": self.updated_at.isoformat()
        }
        if self.error:
            data["error"] = self.error
        if self.metadata:
            data["metadata"] = self.metadata
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SplitProgress':
        """Deserialize from dictionary.

        Args:
            data: Dictionary containing progress fields

        Returns:
            SplitProgress instance
        """
        from datetime import datetime

        session_id = data["session_id"]
        progress = cls(session_id)

        progress.status = SplitStatus(data["status"])
        progress.stage = SplitStage(data["stage"])
        progress.progress = data["progress"]
        progress.message = data["message"]
        progress.ready_for_next_stage = data["ready_for_next_stage"]
        progress.updated_at = datetime.fromisoformat(data["updated_at"])

        if "error" in data:
            progress.error = data["error"]
        if "metadata" in data:
            progress.metadata = data["metadata"]

        return progress
