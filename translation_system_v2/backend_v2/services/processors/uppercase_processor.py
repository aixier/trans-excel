"""Uppercase processor for CAPS transformation.

This processor converts text to uppercase, typically used for CAPS sheets.
It supports dependency on previous tasks, allowing it to uppercase translated
results rather than original source text.
"""

from typing import Dict, Any, Optional, List
from .processor import Processor


class UppercaseProcessor(Processor):
    """Processor that converts text to uppercase.

    Use cases:
    - CAPS sheet transformation
    - Converting translated text to uppercase
    - Post-processing step after translation

    Dependency handling:
    - If context contains 'previous_tasks' and task has 'depends_on',
      it will uppercase the result from the dependency task
    - Otherwise, it uppercases task['source_text']

    Example:
        >>> processor = UppercaseProcessor()
        >>> task = {
        ...     'task_id': 'CAPS_001',
        ...     'operation': 'uppercase',
        ...     'source_text': 'hello world'
        ... }
        >>> processor.process(task)
        'HELLO WORLD'

        >>> # With dependency
        >>> task = {
        ...     'task_id': 'CAPS_001',
        ...     'operation': 'uppercase',
        ...     'source_text': '你好世界',
        ...     'depends_on': 'TRANS_001'
        ... }
        >>> context = {
        ...     'previous_tasks': {
        ...         'TRANS_001': {'result': 'Hello World'}
        ...     }
        ... }
        >>> processor.process(task, context)
        'HELLO WORLD'
    """

    def get_operation_type(self) -> str:
        """Return the operation type.

        Returns:
            str: 'uppercase'
        """
        return 'uppercase'

    def process(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Convert text to uppercase.

        Args:
            task: Task dictionary containing:
                - task_id: Task identifier
                - operation: Must be 'uppercase'
                - source_text: Text to uppercase (fallback)
                - depends_on: Optional dependency task ID

            context: Optional context containing:
                - previous_tasks: Dict mapping task_id to task data
                  If task depends on another task, uses its result

        Returns:
            str: Uppercased text

        Raises:
            ValueError: If task validation fails

        Processing logic:
            1. Validate task data
            2. Get source text (from dependency or task itself)
            3. Convert to uppercase
            4. Return result

        Note:
            - Handles None and empty strings gracefully
            - Works with any Unicode text (Chinese, Thai, etc.)
            - Only ASCII characters are affected by upper()
        """
        # Validate task
        if not self.validate_task(task):
            raise ValueError(f"Invalid task data for uppercase processing: {task.get('task_id')}")

        # Get source text (handles context dependency)
        source_text = self.get_source_text(task, context)

        # Handle empty text
        if not source_text:
            self.logger.debug(
                f"Task {task.get('task_id')} has empty source text, returning empty string"
            )
            return ""

        # Convert to uppercase
        result = source_text.upper()

        self.logger.debug(
            f"Uppercased task {task.get('task_id')}: "
            f"'{source_text[:50]}...' -> '{result[:50]}...'"
        )

        return result

    def process_batch(
        self,
        tasks: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Process multiple tasks in batch.

        Uppercase processing is simple and fast, so we use the default
        implementation (process each task individually).

        Args:
            tasks: List of tasks to process
            context: Optional context with previous results

        Returns:
            List[str]: List of uppercased texts
        """
        # Use default implementation for simplicity
        return super().process_batch(tasks, context)
