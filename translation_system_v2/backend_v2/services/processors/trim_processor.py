"""Trim processor for whitespace removal.

This processor removes leading and trailing whitespace from text,
useful for cleaning up translation results or normalizing input data.
"""

from typing import Dict, Any, Optional, List
from .processor import Processor


class TrimProcessor(Processor):
    """Processor that removes leading and trailing whitespace.

    Use cases:
    - Cleaning translation results
    - Normalizing user input
    - Pre-processing before translation
    - Post-processing after translation

    Features:
    - Removes spaces, tabs, newlines from both ends
    - Preserves internal whitespace
    - Handles Unicode whitespace characters

    Example:
        >>> processor = TrimProcessor()
        >>> task = {
        ...     'task_id': 'TRIM_001',
        ...     'operation': 'trim',
        ...     'source_text': '  hello world  \\n'
        ... }
        >>> processor.process(task)
        'hello world'

        >>> # Unicode whitespace
        >>> task = {
        ...     'task_id': 'TRIM_002',
        ...     'operation': 'trim',
        ...     'source_text': '\\u3000你好世界\\u3000'  # Full-width space
        ... }
        >>> processor.process(task)
        '你好世界'
    """

    def get_operation_type(self) -> str:
        """Return the operation type.

        Returns:
            str: 'trim'
        """
        return 'trim'

    def process(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Remove leading and trailing whitespace.

        Args:
            task: Task dictionary containing:
                - task_id: Task identifier
                - operation: Must be 'trim'
                - source_text: Text to trim
                - depends_on: Optional dependency task ID

            context: Optional context containing:
                - previous_tasks: Dict mapping task_id to task data

        Returns:
            str: Trimmed text

        Raises:
            ValueError: If task validation fails

        Processing logic:
            1. Validate task data
            2. Get source text (from dependency or task itself)
            3. Remove leading and trailing whitespace
            4. Return result

        Note:
            - Python's str.strip() handles all Unicode whitespace
            - Returns empty string if input is only whitespace
            - Preserves internal whitespace (spaces between words)
        """
        # Validate task
        if not self.validate_task(task):
            raise ValueError(f"Invalid task data for trim processing: {task.get('task_id')}")

        # Get source text (handles context dependency)
        source_text = self.get_source_text(task, context)

        # Handle None
        if source_text is None:
            self.logger.debug(
                f"Task {task.get('task_id')} has None source text, returning empty string"
            )
            return ""

        # Trim whitespace
        result = source_text.strip()

        # Log if whitespace was removed
        if result != source_text:
            removed_prefix = len(source_text) - len(source_text.lstrip())
            removed_suffix = len(source_text) - len(source_text.rstrip())
            self.logger.debug(
                f"Trimmed task {task.get('task_id')}: "
                f"removed {removed_prefix} leading and {removed_suffix} trailing chars"
            )

        return result

    def process_batch(
        self,
        tasks: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Process multiple tasks in batch.

        Trim processing is very fast, so we use the default implementation.

        Args:
            tasks: List of tasks to process
            context: Optional context with previous results

        Returns:
            List[str]: List of trimmed texts
        """
        return super().process_batch(tasks, context)
