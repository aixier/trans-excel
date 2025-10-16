"""Base class for split rules.

This module defines the abstract base class for all split rules.
Rules are used to identify cells that require specific operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class SplitRule(ABC):
    """Abstract base class for split rules.

    A split rule determines which cells match certain conditions
    and creates corresponding tasks for matched cells.
    """

    @abstractmethod
    def match(self, cell: Any, context: Dict[str, Any]) -> bool:
        """Check if a cell matches this rule.

        Args:
            cell: Cell object or cell value to check
            context: Context information including:
                - sheet_name: Name of the sheet
                - row_idx: Row index
                - col_idx: Column index
                - column_name: Name of the column
                - color: Cell background color (if available)

        Returns:
            bool: True if the cell matches this rule
        """
        pass

    @abstractmethod
    def create_task(self, cell: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task for a matched cell.

        Args:
            cell: Cell object or cell value
            context: Context information (same as match method)

        Returns:
            Dict containing task information:
                - task_id: Unique task identifier
                - operation: Operation type (translate/uppercase/trim)
                - priority: Task priority (1-10)
                - sheet_name: Sheet name
                - row_idx: Row index
                - col_idx: Column index
                - cell_ref: Cell reference (e.g., 'A1')
                - source_text: Source text for the operation
                - source_lang: Source language
                - target_lang: Target language
                - status: Task status (always 'pending' initially)
                - metadata: Additional metadata (optional)
        """
        pass

    def get_priority(self) -> int:
        """Get the priority of this rule.

        Returns:
            int: Priority value (1-10, higher = more urgent)
        """
        return 5

    def get_operation_type(self) -> str:
        """Get the operation type this rule handles.

        Returns:
            str: Operation type (translate/uppercase/trim/etc.)
        """
        return 'unknown'

    def get_rule_name(self) -> str:
        """Get the name of this rule.

        Returns:
            str: Rule name (class name by default)
        """
        return self.__class__.__name__


class SplitterError(Exception):
    """Base exception for splitter errors."""
    pass


class InvalidDataStateError(SplitterError):
    """Raised when data state is invalid."""
    pass


class RuleConflictError(SplitterError):
    """Raised when rules conflict with each other."""
    pass


class RuleError(SplitterError):
    """Raised when a rule encounters an error."""
    pass
