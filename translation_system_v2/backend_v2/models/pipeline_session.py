"""Pipeline-based session management - Each session represents ONE transformation.

This module implements the architecture principle: "Data State Continuity"
- Each session manages ONE transformation: input_state → tasks → output_state
- Sessions can be chained through parent_session_id
- Input can come from file OR parent session's output
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

from models.excel_dataframe import ExcelDataFrame
from models.task_dataframe import TaskDataFrameManager


class TransformationStage(Enum):
    """Stage of a single transformation session."""
    CREATED = "created"              # Session created, input not loaded
    INPUT_LOADED = "input_loaded"     # Input state loaded (from file or parent)
    SPLIT_COMPLETE = "split_complete" # Tasks generated
    EXECUTING = "executing"           # Transformation in progress
    COMPLETED = "completed"           # Output state ready
    FAILED = "failed"                # Transformation failed


@dataclass
class PipelineSession:
    """Session for ONE transformation in the pipeline.

    Represents: input_state → [rules] → tasks → [processor] → output_state

    Attributes:
        session_id: Unique identifier for this transformation
        created_at: Creation timestamp
        last_accessed: Last access timestamp
        stage: Current transformation stage

        # Input
        input_state: Current data state (ExcelDataFrame)
        input_source: Where input came from ('file' or 'parent_session')
        parent_session_id: If chained, the parent session ID

        # Configuration
        rules: List of rule names applied (e.g., ['empty', 'yellow'])
        processor: Processor name used (e.g., 'llm_qwen', 'uppercase')

        # Output
        tasks: Generated task table (TaskDataFrameManager)
        task_statistics: Task generation statistics
        output_state: Result data state (ExcelDataFrame)
        execution_statistics: Execution statistics

        # Metadata
        metadata: Additional information (file paths, etc.)

        # Chaining
        child_session_ids: Sessions created from this session's output
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    stage: TransformationStage = TransformationStage.CREATED

    # Input
    input_state: Optional[ExcelDataFrame] = None
    input_source: str = ""  # 'file' or 'parent_session'
    parent_session_id: Optional[str] = None

    # Configuration
    rules: List[str] = field(default_factory=list)
    processor: Optional[str] = None

    # Output
    tasks: Optional[TaskDataFrameManager] = None
    task_statistics: Dict[str, Any] = field(default_factory=dict)
    output_state: Optional[ExcelDataFrame] = None
    execution_statistics: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Chaining
    child_session_ids: List[str] = field(default_factory=list)

    def update_access_time(self):
        """Update last accessed timestamp."""
        self.last_accessed = datetime.now()

    def update_stage(self, stage: TransformationStage):
        """Update transformation stage."""
        self.stage = stage
        self.last_accessed = datetime.now()

    def add_child_session(self, child_session_id: str):
        """Register a child session (created from this session's output)."""
        if child_session_id not in self.child_session_ids:
            self.child_session_ids.append(child_session_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary (excluding heavy DataFrames).

        Returns:
            Dictionary with session metadata (DataFrames excluded)
        """
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'stage': self.stage.value,

            'input_source': self.input_source,
            'parent_session_id': self.parent_session_id,

            'rules': self.rules,
            'processor': self.processor,

            'task_statistics': self.task_statistics,
            'execution_statistics': self.execution_statistics,

            'metadata': self.metadata,
            'child_session_ids': self.child_session_ids,

            # File paths for lazy loading
            'input_file_path': self.metadata.get('input_file_path'),
            'task_file_path': self.metadata.get('task_file_path'),
            'output_file_path': self.metadata.get('output_file_path'),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineSession':
        """Deserialize from dictionary.

        Args:
            data: Dictionary containing session metadata

        Returns:
            PipelineSession instance (DataFrames need to be loaded separately)
        """
        session = cls(session_id=data['session_id'])
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.last_accessed = datetime.fromisoformat(data['last_accessed'])
        session.stage = TransformationStage(data['stage'])

        session.input_source = data.get('input_source', '')
        session.parent_session_id = data.get('parent_session_id')

        session.rules = data.get('rules', [])
        session.processor = data.get('processor')

        session.task_statistics = data.get('task_statistics', {})
        session.execution_statistics = data.get('execution_statistics', {})

        session.metadata = data.get('metadata', {})
        session.child_session_ids = data.get('child_session_ids', [])

        return session

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of this session for API responses.

        Returns:
            Dictionary with key session information
        """
        return {
            'session_id': self.session_id,
            'stage': self.stage.value,
            'created_at': self.created_at.isoformat(),
            'input_source': self.input_source,
            'parent_session_id': self.parent_session_id,
            'rules': self.rules,
            'processor': self.processor,
            'task_count': len(self.tasks.df) if self.tasks and self.tasks.df is not None else 0,
            'has_output': self.output_state is not None,
            'child_sessions': len(self.child_session_ids),
        }
