"""Base processor class for data transformations.

Architecture Principles:
1. Processors ONLY return results, don't update task status
2. Processors don't modify data_state
3. Use context to get dependencies from previous tasks
4. Each processor must implement get_operation_type()
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Processor(ABC):
    """Abstract base class for all data processors.

    A Processor transforms input data according to a specific operation.
    It receives a task and optional context, and returns the processed result.

    Key principles:
    - Pure transformation: process(task, context) -> result
    - No side effects: Don't modify task status or data state
    - Context-aware: Can access previous task results via context
    - Operation-typed: Each processor declares its operation type
    """

    def __init__(self):
        """Initialize the processor."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def process(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Process a single task and return the result.

        This is the core method that each processor must implement.

        Args:
            task: Task dictionary containing:
                - task_id: Unique task identifier
                - operation: Operation type (translate, uppercase, etc.)
                - source_text: Input text to process
                - sheet_name, row_idx, col_idx: Position information
                - target_lang: Target language (for translation)
                - task_type: Task type (normal, yellow, blue)
                - Other task-specific fields

            context: Optional context dictionary containing:
                - previous_tasks: Results from previous processing stages
                - all_tasks: Complete task history
                - data_state: Current data state (read-only)
                - Other context-specific data

        Returns:
            str: The processed result text

        Raises:
            ValueError: If task data is invalid
            RuntimeError: If processing fails

        Note:
            - Do NOT modify task['status'] or task['result']
            - Do NOT modify context or data_state
            - Only return the processed string result
        """
        pass

    def process_batch(
        self,
        tasks: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Process multiple tasks in batch.

        Default implementation processes tasks one by one.
        Override this method for batch-optimized processing.

        Args:
            tasks: List of task dictionaries
            context: Optional context dictionary

        Returns:
            List[str]: List of processed results, in same order as input tasks

        Example:
            >>> processor = SomeProcessor()
            >>> tasks = [task1, task2, task3]
            >>> results = processor.process_batch(tasks, context)
            >>> # results = [result1, result2, result3]
        """
        results = []
        for task in tasks:
            try:
                result = self.process(task, context)
                results.append(result)
            except Exception as e:
                self.logger.error(
                    f"Failed to process task {task.get('task_id', 'unknown')}: {e}"
                )
                # Return empty string on error, let caller handle retry
                results.append("")
        return results

    @abstractmethod
    def get_operation_type(self) -> str:
        """Return the operation type this processor handles.

        Returns:
            str: Operation type identifier (e.g., 'translate', 'uppercase', 'trim')

        Example:
            >>> processor = UppercaseProcessor()
            >>> processor.get_operation_type()
            'uppercase'
        """
        pass

    def validate_task(self, task: Dict[str, Any]) -> bool:
        """Validate task data before processing.

        Override this method to add custom validation logic.

        Args:
            task: Task dictionary to validate

        Returns:
            bool: True if task is valid, False otherwise
        """
        required_fields = ['task_id', 'operation', 'source_text']

        for field in required_fields:
            if field not in task:
                self.logger.warning(
                    f"Task {task.get('task_id', 'unknown')} missing required field: {field}"
                )
                return False

        # Check if operation matches this processor
        if task.get('operation') != self.get_operation_type():
            self.logger.warning(
                f"Task {task['task_id']} operation '{task.get('operation')}' "
                f"does not match processor type '{self.get_operation_type()}'"
            )
            return False

        return True

    def get_source_text(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Get the source text for processing.

        This helper method provides a standard way to retrieve source text,
        with support for context-based dependencies.

        Args:
            task: Task dictionary
            context: Optional context with previous results

        Returns:
            str: Source text to process

        Logic:
            1. If task has 'depends_on' and context has 'previous_tasks',
               get result from the dependency task
            2. Otherwise, use task['source_text']

        Example:
            >>> # Task depends on a previous translation
            >>> task = {
            ...     'task_id': 'T002',
            ...     'source_text': 'original',
            ...     'depends_on': 'T001'
            ... }
            >>> context = {
            ...     'previous_tasks': {
            ...         'T001': {'result': 'translated text'}
            ...     }
            ... }
            >>> processor.get_source_text(task, context)
            'translated text'
        """
        # Check for dependency in context
        if context and 'previous_tasks' in context:
            depends_on = task.get('depends_on')
            if depends_on:
                previous_tasks = context['previous_tasks']
                if depends_on in previous_tasks:
                    dependency_task = previous_tasks[depends_on]
                    result = dependency_task.get('result', '')
                    if result:
                        self.logger.debug(
                            f"Task {task.get('task_id')} using result from dependency {depends_on}"
                        )
                        return result

        # Fall back to task's own source_text
        return task.get('source_text', '')

    def __repr__(self) -> str:
        """String representation of the processor."""
        return f"{self.__class__.__name__}(operation='{self.get_operation_type()}')"
