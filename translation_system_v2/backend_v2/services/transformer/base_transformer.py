"""Basic implementation of Transformer.

This module provides a straightforward implementation of the Transformer
interface that processes tasks sequentially and handles errors gracefully.

Use Cases:
    - Simple transformations (uppercase, trim, etc.)
    - When batch optimization is not needed
    - Testing and debugging
    - Default implementation for new processors

Performance:
    - Processes tasks one by one
    - Single-threaded execution
    - Suitable for up to 10,000 tasks
    - For larger workloads, consider BatchTransformer
"""

from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime

from services.data_state import DataState
from services.processors import Processor
from .transformer import Transformer, TransformerError, InvalidTaskError, ProcessorError


class BaseTransformer(Transformer):
    """
    Basic transformer implementation with sequential processing.

    This implementation processes tasks one by one, making it simple
    and reliable for most use cases. It provides comprehensive error
    handling and detailed logging.

    Features:
        - Sequential task processing
        - Comprehensive error handling
        - Detailed progress logging
        - Full task status tracking
        - Context passing to processors

    Examples:
        >>> # Create with any processor
        >>> processor = UppercaseProcessor()
        >>> transformer = BaseTransformer(processor)

        >>> # Execute tasks
        >>> new_state = transformer.execute(data_state, tasks)

        >>> # With context for dependencies
        >>> new_state = transformer.execute(
        ...     data_state,
        ...     tasks,
        ...     context={'previous_tasks': prev_tasks}
        ... )

        >>> # Check results
        >>> print(f"Completed: {(tasks['status'] == 'completed').sum()}")
        >>> print(f"Failed: {(tasks['status'] == 'failed').sum()}")
    """

    def execute(
        self,
        data_state: DataState,
        tasks: pd.DataFrame,
        context: Optional[Dict[str, Any]] = None
    ) -> DataState:
        """
        Execute tasks sequentially and return new data state.

        Args:
            data_state: Current data state (will NOT be modified)
            tasks: TaskDataFrame with tasks to execute (will be modified)
            context: Optional context for passing dependencies

        Returns:
            DataState: New data state with updated cells

        Raises:
            InvalidTaskError: If task validation fails
            TransformerError: If critical error occurs

        Processing Flow:
            1. Validate tasks
            2. Copy data state
            3. For each task:
               a. Validate individual task
               b. Call processor.process(task, context)
               c. Update data state with result
               d. Update task with result and status='completed'
               e. If error: Update task with error_message and status='failed'
            4. Log summary statistics
            5. Return new data state

        Examples:
            >>> transformer = BaseTransformer(UppercaseProcessor())
            >>> new_state = transformer.execute(state, tasks)
            >>> # tasks DataFrame is now updated with results
        """
        # 1. Validate tasks
        if not self.validate_tasks(tasks):
            raise InvalidTaskError("Task validation failed")

        # Handle empty tasks
        if len(tasks) == 0:
            self.logger.info("No tasks to execute")
            return data_state.copy()

        self.logger.info(
            f"Starting execution of {len(tasks)} tasks using "
            f"{self.processor.__class__.__name__}"
        )

        # 2. Copy data state (preserve immutability)
        new_state = data_state.copy()
        self.logger.debug("Data state copied successfully")

        # 3. Process each task
        completed_count = 0
        failed_count = 0
        start_time = datetime.now()

        for idx, task_row in tasks.iterrows():
            # Convert Series to dict for processor
            task = task_row.to_dict()
            task_id = task.get('task_id', f'row_{idx}')

            try:
                # Validate individual task
                if not self._validate_single_task(task):
                    raise ValueError(f"Invalid task data: {task_id}")

                # Call processor to transform data
                task_start = datetime.now()
                result = self.processor.process(task, context)
                task_duration = (datetime.now() - task_start).total_seconds() * 1000

                # Update data state with result
                self._update_data_state(new_state, task, result)

                # Update task status
                tasks.loc[idx, 'result'] = result
                tasks.loc[idx, 'status'] = 'completed'
                tasks.loc[idx, 'updated_at'] = datetime.now()

                # Add timing info if columns exist
                if 'duration_ms' in tasks.columns:
                    tasks.loc[idx, 'duration_ms'] = int(task_duration)
                if 'end_time' in tasks.columns:
                    tasks.loc[idx, 'end_time'] = datetime.now()

                completed_count += 1

                # Log progress every 100 tasks
                if completed_count % 100 == 0:
                    self.logger.info(f"Processed {completed_count}/{len(tasks)} tasks")

            except Exception as e:
                # Handle error gracefully - don't stop execution
                error_msg = str(e)
                self.logger.error(
                    f"Task {task_id} failed: {error_msg}",
                    exc_info=True
                )

                # Update task with error status
                tasks.loc[idx, 'status'] = 'failed'
                tasks.loc[idx, 'error_message'] = error_msg
                tasks.loc[idx, 'updated_at'] = datetime.now()

                if 'result' in tasks.columns:
                    tasks.loc[idx, 'result'] = ''  # Empty result on failure

                failed_count += 1

        # 4. Log summary
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(
            f"Execution completed: {completed_count} succeeded, "
            f"{failed_count} failed, {duration:.2f}s total"
        )

        if failed_count > 0:
            self.logger.warning(
                f"{failed_count} tasks failed. Check error_message column for details."
            )

        # 5. Return new data state
        return new_state

    def _validate_single_task(self, task: Dict[str, Any]) -> bool:
        """
        Validate a single task before processing.

        Args:
            task: Task dictionary to validate

        Returns:
            bool: True if valid, False otherwise

        Checks:
            - Has required fields
            - Fields are not None
            - Operation matches processor
        """
        # Check required fields
        required_fields = ['task_id', 'sheet_name', 'row_idx', 'col_idx', 'source_text']
        for field in required_fields:
            if field not in task:
                self.logger.error(f"Task missing field: {field}")
                return False
            if task[field] is None and field != 'source_text':  # source_text can be None
                self.logger.error(f"Task has None value for: {field}")
                return False

        # Check operation matches processor (optional check)
        task_operation = task.get('operation')
        processor_operation = self.processor.get_operation_type()
        if task_operation and task_operation != processor_operation:
            self.logger.warning(
                f"Task operation '{task_operation}' doesn't match "
                f"processor type '{processor_operation}'. Proceeding anyway."
            )

        return True

    def _update_data_state(
        self,
        state: DataState,
        task: Dict[str, Any],
        result: str
    ) -> None:
        """
        Update data state with transformation result.

        Args:
            state: DataState to update (modified in-place)
            task: Task containing location info
            result: Transformation result to write

        Raises:
            KeyError: If sheet doesn't exist
            IndexError: If row/col is out of bounds
        """
        sheet_name = task['sheet_name']
        row_idx = int(task['row_idx'])
        col_idx = int(task['col_idx'])

        try:
            state.set_cell_value(sheet_name, row_idx, col_idx, result)
            self.logger.debug(
                f"Updated cell {sheet_name}[{row_idx},{col_idx}] with result"
            )
        except (KeyError, IndexError) as e:
            # Re-raise with more context
            raise TransformerError(
                f"Failed to update cell {sheet_name}[{row_idx},{col_idx}]: {e}"
            ) from e
