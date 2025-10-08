"""Execution state management module.

This module provides state management for the translation execution phase,
tracking progress, statistics, and readiness for monitoring and download.
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class ExecutionStatus(Enum):
    """Execution process status.

    Tracks the overall status of the translation execution.
    """
    IDLE = "idle"                    # Not started
    INITIALIZING = "initializing"    # Initializing workers
    RUNNING = "running"              # Execution in progress
    PAUSED = "paused"                # Paused by user
    STOPPED = "stopped"              # Stopped by user
    COMPLETED = "completed"          # All tasks completed
    FAILED = "failed"                # Execution failed


class ExecutionProgress:
    """Execution progress manager - independent and testable.

    This class manages the state and progress of the translation execution phase.
    It tracks when execution is ready for monitoring and when results are ready
    for download.

    Attributes:
        session_id: Unique session identifier
        status: Current execution status
        ready_for_monitoring: Whether monitoring can start
        ready_for_download: Whether results can be downloaded
        statistics: Task statistics (total, completed, failed, processing)
        error: Error message if failed
        updated_at: Last update timestamp
    """

    def __init__(self, session_id: str):
        """Initialize execution progress.

        Args:
            session_id: Unique session identifier
        """
        self.session_id = session_id
        self.status = ExecutionStatus.IDLE
        self.ready_for_monitoring: bool = False  # Can start monitoring
        self.ready_for_download: bool = False    # Can download results
        self.statistics: Dict[str, Any] = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "processing": 0
        }
        self.error: Optional[str] = None
        self.updated_at = datetime.now()

    def mark_initializing(self):
        """Mark as initializing.

        This is called when execution starts but workers are not yet ready.
        """
        self.status = ExecutionStatus.INITIALIZING
        self.ready_for_monitoring = False
        self.updated_at = datetime.now()

    def mark_running(self):
        """Mark as running - monitoring is ready.

        This is called when workers are initialized and execution has started.
        At this point, the frontend can start polling for progress updates.
        """
        self.status = ExecutionStatus.RUNNING
        self.ready_for_monitoring = True  # ✨ Can start monitoring
        self.updated_at = datetime.now()

    def mark_paused(self):
        """Mark as paused by user."""
        self.status = ExecutionStatus.PAUSED
        self.updated_at = datetime.now()

    def mark_stopped(self):
        """Mark as stopped by user."""
        self.status = ExecutionStatus.STOPPED
        self.updated_at = datetime.now()

    def mark_completed(self):
        """Mark as completed - download is ready.

        This is called when all tasks are complete and results are ready
        for download.
        """
        self.status = ExecutionStatus.COMPLETED
        self.ready_for_download = True  # ✨ Can download results
        self.updated_at = datetime.now()

    def mark_failed(self, error: str):
        """Mark as failed.

        Args:
            error: Error message
        """
        self.status = ExecutionStatus.FAILED
        self.error = error
        self.updated_at = datetime.now()

    def update_statistics(self, stats: Dict[str, Any]):
        """Update task statistics.

        Args:
            stats: Statistics dictionary with keys:
                   total, completed, failed, processing
        """
        self.statistics.update(stats)
        self.updated_at = datetime.now()

    def is_ready_for_monitoring(self) -> bool:
        """Check if ready for monitoring.

        Returns:
            True if monitoring can start (status is RUNNING)
        """
        return self.ready_for_monitoring

    def is_ready_for_download(self) -> bool:
        """Check if ready for download.

        Returns:
            True if download can start (status is COMPLETED)
        """
        return self.ready_for_download

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for API responses.

        Returns:
            Dictionary containing all execution progress fields
        """
        data = {
            "session_id": self.session_id,
            "status": self.status.value,
            "ready_for_monitoring": self.ready_for_monitoring,  # ✨ KEY field
            "ready_for_download": self.ready_for_download,      # ✨ KEY field
            "statistics": self.statistics,
            "updated_at": self.updated_at.isoformat()
        }
        if self.error:
            data["error"] = self.error
        return data
