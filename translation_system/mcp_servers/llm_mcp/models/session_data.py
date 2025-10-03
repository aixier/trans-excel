"""
Session Data Models for LLM MCP Server
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class SessionStatus(Enum):
    """Session status enumeration."""
    PENDING = "pending"
    TRANSLATING = "translating"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class TranslationSession:
    """Translation session data model."""

    session_id: str
    session_type: str = "llm"
    status: SessionStatus = SessionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Task data
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    progress: float = 0.0

    # Configuration
    provider: Optional[str] = None
    model: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)

    # Statistics
    translation_stats: Optional[Dict[str, Any]] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Control flags
    should_stop: bool = False
    is_paused: bool = False

    def update_progress(self, completed: int, total: int):
        """Update session progress."""
        if total > 0:
            self.progress = (completed / total) * 100
            self.updated_at = datetime.now()

    def update_stats(self, stats: Dict[str, Any]):
        """Update translation statistics."""
        if not self.translation_stats:
            self.translation_stats = {}
        self.translation_stats.update(stats)
        self.updated_at = datetime.now()


@dataclass
class TranslationResult:
    """Translation result from LLM."""
    text: str
    tokens_used: int = 0
    cost: float = 0.0
    provider: str = ""
    model: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)