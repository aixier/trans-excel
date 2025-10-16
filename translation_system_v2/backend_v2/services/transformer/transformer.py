"""Abstract base class for data transformers.

This module defines the core abstraction for executing tasks and transforming
data states. Transformers are responsible for orchestrating the execution of
tasks using processors and updating data states accordingly.

Architecture Principles:
    - Transformer executes tasks, doesn't create them (Splitter creates tasks)
    - Transformer doesn't implement transformation logic (Processor does that)
    - Always preserve input state immutability (return new state)
    - Update task status and results
    - Handle errors gracefully

Key Concepts:
    - Input: DataState + TaskDataFrame + Processor
    - Output: New DataState (with updated cells)
    - Side effect: TaskDataFrame updated (status, result, error_message)

Examples:
    >>> # Basic usage
    >>> processor = UppercaseProcessor()
    >>> transformer = BaseTransformer(processor)
    >>> new_state = transformer.execute(data_state, tasks)

    >>> # With context (for dependencies)
    >>> new_state = transformer.execute(
    ...     data_state,
    ...     tasks,
    ...     context={'previous_tasks': prev_tasks}
    ... )
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import pandas as pd

from services.data_state import DataState
from services.processors import Processor

logger = logging.getLogger(__name__)


class TransformerError(Exception):
    """Base exception for transformer errors."""
    pass


class InvalidTaskError(TransformerError):
    """Exception raised when task data is invalid."""
    pass


class ProcessorError(TransformerError):
    """Exception raised when processor execution fails."""
    pass


class Transformer(ABC):
    """
    Abstract base class for data transformers.

    A Transformer executes tasks by calling a Processor on each task,
    updating the data state with results, and tracking task completion status.

    Design Principles:
        1. Immutability: Copy input data_state, return new state
        2. Pure execution: Don't create tasks, just execute them
        3. Error handling: Single task failure doesn't stop others
        4. Context passing: Pass context to processor for dependencies

    Attributes:
        processor: Processor instance that handles transformation logic

    Examples:
        >>> # Create transformer with processor
        >>> processor = UppercaseProcessor()
        >>> transformer = BaseTransformer(processor)

        >>> # Execute tasks
        >>> data_state = ExcelState(...)
        >>> tasks = TaskDataFrame(...)
        >>> new_state = transformer.execute(data_state, tasks)

        >>> # Check results
        >>> assert all(tasks['status'] == 'completed')
        >>> assert new_state is not data_state  # New object returned
    """

    def __init__(self, processor: Processor):
        """
        Initialize transformer with a processor.

        Args:
            processor: Processor instance that handles transformation logic
                      (e.g., LLMProcessor, UppercaseProcessor)

        Examples:
            >>> processor = UppercaseProcessor()
            >>> transformer = BaseTransformer(processor)
        """
        self.processor = processor
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def execute(
        self,
        data_state: DataState,
        tasks: pd.DataFrame,
        context: Optional[Dict[str, Any]] = None
    ) -> DataState:
        """
        Execute tasks and return new data state.

        This is the core method that must be implemented by subclasses.

        Args:
            data_state: Current data state (will NOT be modified)
            tasks: TaskDataFrame with tasks to execute (will be modified)
                   Required columns: task_id, sheet_name, row_idx, col_idx,
                                   source_text, operation, status
            context: Optional context dictionary for passing dependencies:
                    - previous_tasks: Results from previous stages
                    - all_tasks: Complete task history
                    - config: Configuration data
                    - session_id: Session identifier

        Returns:
            DataState: New data state with updated cell values

        Side Effects:
            Updates task DataFrame with:
            - result: Processed result text
            - status: 'completed' or 'failed'
            - error_message: Error description if failed

        Raises:
            TransformerError: If transformation fails completely
            InvalidTaskError: If task data is invalid

        Processing Logic:
            1. Copy input data_state (preserve immutability)
            2. Validate tasks
            3. For each task:
               a. Call processor.process(task, context)
               b. Update data_state with result
               c. Update task status
               d. Handle errors (don't stop on single failure)
            4. Return new data_state

        Examples:
            >>> # Basic execution
            >>> new_state = transformer.execute(state, tasks)

            >>> # With context for dependencies
            >>> new_state = transformer.execute(
            ...     state,
            ...     tasks,
            ...     context={
            ...         'previous_tasks': prev_tasks,
            ...         'session_id': 'abc123'
            ...     }
            ... )

            >>> # Check results
            >>> completed = tasks[tasks['status'] == 'completed']
            >>> failed = tasks[tasks['status'] == 'failed']
            >>> print(f"Completed: {len(completed)}, Failed: {len(failed)}")

        Note:
            - Input data_state is never modified
            - Task DataFrame is modified in-place
            - Single task failure doesn't stop execution
            - Returns new DataState even if all tasks fail
        """
        pass

    def validate_tasks(self, tasks: pd.DataFrame) -> bool:
        """
        Validate task DataFrame before execution.

        Args:
            tasks: TaskDataFrame to validate

        Returns:
            bool: True if valid, False otherwise

        Validation checks:
            - Tasks is not None
            - Tasks is not empty
            - Required columns exist
            - Data types are correct

        Examples:
            >>> if transformer.validate_tasks(tasks):
            ...     new_state = transformer.execute(state, tasks)
        """
        if tasks is None:
            self.logger.error("Tasks is None")
            return False

        if len(tasks) == 0:
            self.logger.warning("Tasks is empty")
            return True  # Empty is valid, just nothing to do

        # Check required columns
        required_columns = [
            'task_id',
            'sheet_name',
            'row_idx',
            'col_idx',
            'source_text',
            'operation',
            'status'
        ]

        missing_columns = [col for col in required_columns if col not in tasks.columns]
        if missing_columns:
            self.logger.error(f"Missing required columns: {missing_columns}")
            return False

        return True

    def get_processor_type(self) -> str:
        """
        Get the type of processor used by this transformer.

        Returns:
            str: Processor operation type

        Examples:
            >>> transformer = BaseTransformer(UppercaseProcessor())
            >>> transformer.get_processor_type()
            'uppercase'
        """
        return self.processor.get_operation_type()

    def __repr__(self) -> str:
        """String representation of the transformer."""
        return (f"{self.__class__.__name__}("
                f"processor={self.processor.__class__.__name__})")
