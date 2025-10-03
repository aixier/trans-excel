"""Session data model for task_mcp."""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class SessionStatus(str, Enum):
    """Session status enum."""
    QUEUED = 'queued'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class TaskType(str, Enum):
    """Task type enum based on cell color."""
    NORMAL = 'normal'      # No color - standard translation
    YELLOW = 'yellow'      # Yellow background - retranslation
    BLUE = 'blue'          # Blue background - shorten


@dataclass
class TaskSplitSession:
    """Session data for task splitting."""

    session_id: str
    token: str
    status: SessionStatus = SessionStatus.QUEUED
    progress: int = 0  # 0-100

    # Input parameters
    excel_url: Optional[str] = None
    excel_path: Optional[str] = None
    source_lang: Optional[str] = None
    target_langs: List[str] = field(default_factory=list)
    extract_context: bool = True
    context_options: Dict[str, bool] = field(default_factory=dict)

    # Results
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    # Export info
    export_path: Optional[str] = None
    download_url: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'status': self.status.value,
            'progress': self.progress,
            'source_lang': self.source_lang,
            'target_langs': self.target_langs,
            'extract_context': self.extract_context,
            'context_options': self.context_options,
            'summary': self.summary,
            'error_message': self.error_message,
            'download_url': self.download_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

    def update_status(self, status: SessionStatus, progress: int = None):
        """Update session status."""
        self.status = status
        if progress is not None:
            self.progress = progress
        self.updated_at = datetime.now()
        if status == SessionStatus.COMPLETED:
            self.completed_at = datetime.now()


@dataclass
class TaskSummary:
    """Summary of task splitting results."""

    total_tasks: int = 0
    task_breakdown: Dict[str, int] = field(default_factory=dict)  # normal/yellow/blue
    language_distribution: Dict[str, int] = field(default_factory=dict)  # PT/TH/VN
    batch_count: int = 0
    total_chars: int = 0
    estimated_cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_tasks': self.total_tasks,
            'task_breakdown': self.task_breakdown,
            'language_distribution': self.language_distribution,
            'batch_count': self.batch_count,
            'total_chars': self.total_chars,
            'estimated_cost': self.estimated_cost
        }
