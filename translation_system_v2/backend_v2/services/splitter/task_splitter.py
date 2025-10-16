"""Task splitter implementation.

This module contains the TaskSplitter class that applies rules to data state
and generates a task DataFrame.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
import logging

from .split_rule import SplitRule, InvalidDataStateError, RuleConflictError
from models.task_dataframe import TaskDataFrameManager, TASK_DF_COLUMNS

logger = logging.getLogger(__name__)


class TaskSplitter:
    """Task splitter that applies rules to data state to generate tasks.

    The splitter is responsible for:
    1. Iterating through all cells in the data state
    2. Applying rules to identify cells that need processing
    3. Creating tasks for matched cells
    4. Returning a TaskDataFrame with all tasks
    """

    def __init__(self):
        """Initialize the task splitter."""
        self.task_manager = TaskDataFrameManager()

    def split(
        self,
        data_state: Any,
        rules: List[SplitRule]
    ) -> pd.DataFrame:
        """Split data state into tasks based on rules.

        Args:
            data_state: Current data state (Excel/JSON format)
            rules: List of split rules to apply

        Returns:
            pd.DataFrame: TaskDataFrame with all generated tasks

        Raises:
            InvalidDataStateError: If data_state is invalid
            RuleConflictError: If rules conflict
        """
        if not rules:
            logger.warning("No rules provided to splitter")
            return self.task_manager.create_empty_dataframe()

        # Validate data state
        self._validate_data_state(data_state)

        # Sort rules by priority (descending)
        sorted_rules = sorted(rules, key=lambda r: r.get_priority(), reverse=True)

        logger.info(f"Starting split with {len(sorted_rules)} rules")

        # Track which cells have been matched to avoid duplicates
        matched_cells = set()

        # Collect all tasks
        all_tasks = []

        # Iterate through all sheets
        sheets = self._get_sheets(data_state)

        for sheet_name, sheet_data in sheets.items():
            logger.debug(f"Processing sheet: {sheet_name}")

            # Get metadata for this sheet
            metadata = self._get_sheet_metadata(data_state, sheet_name)

            # Iterate through all cells
            for row_idx, row in sheet_data.iterrows():
                for col_idx, cell_value in enumerate(row):
                    # Build context
                    context = {
                        'sheet_name': sheet_name,
                        'row_idx': row_idx,
                        'col_idx': col_idx,
                        'column_name': sheet_data.columns[col_idx] if col_idx < len(sheet_data.columns) else '',
                        'cell_value': cell_value,
                        'color': self._get_cell_color(data_state, sheet_name, row_idx, col_idx),
                        'row_data': row,
                        'metadata': metadata
                    }

                    # Create cell identifier
                    cell_id = (sheet_name, row_idx, col_idx)

                    # Skip if already matched by a higher priority rule
                    if cell_id in matched_cells:
                        continue

                    # Apply rules in priority order
                    for rule in sorted_rules:
                        try:
                            if rule.match(cell_value, context):
                                # Create task
                                task = rule.create_task(cell_value, context)

                                # Validate task
                                self._validate_task(task)

                                # Add to tasks list
                                all_tasks.append(task)

                                # Mark as matched
                                matched_cells.add(cell_id)

                                logger.debug(
                                    f"Rule {rule.get_rule_name()} matched cell "
                                    f"{sheet_name}[{row_idx}, {col_idx}]"
                                )

                                # Stop checking other rules for this cell (highest priority wins)
                                break

                        except Exception as e:
                            logger.error(
                                f"Error applying rule {rule.get_rule_name()} "
                                f"to cell {sheet_name}[{row_idx}, {col_idx}]: {e}"
                            )
                            # Continue with next rule

        # Add all tasks to task manager
        if all_tasks:
            self.task_manager.add_tasks_batch(all_tasks)
            logger.info(f"Created {len(all_tasks)} tasks from {len(matched_cells)} cells")

            # Sort tasks by priority (descending) for consistent ordering
            if self.task_manager.df is not None and len(self.task_manager.df) > 0:
                self.task_manager.df = self.task_manager.df.sort_values(
                    by=['priority', 'task_id'],
                    ascending=[False, True]
                ).reset_index(drop=True)
        else:
            logger.warning("No tasks created")

        return self.task_manager.df if self.task_manager.df is not None else self.task_manager.create_empty_dataframe()

    def _validate_data_state(self, data_state: Any) -> None:
        """Validate that data state is in correct format.

        Args:
            data_state: Data state to validate

        Raises:
            InvalidDataStateError: If data state is invalid
        """
        if data_state is None:
            raise InvalidDataStateError("Data state cannot be None")

        # Check for required attributes
        if not hasattr(data_state, 'sheets'):
            raise InvalidDataStateError("Data state must have 'sheets' attribute")

        if not isinstance(data_state.sheets, dict):
            raise InvalidDataStateError("Data state 'sheets' must be a dictionary")

        if not data_state.sheets:
            raise InvalidDataStateError("Data state must have at least one sheet")

    def _get_sheets(self, data_state: Any) -> Dict[str, pd.DataFrame]:
        """Get all sheets from data state.

        Args:
            data_state: Data state object

        Returns:
            Dict mapping sheet names to DataFrames
        """
        return data_state.sheets

    def _get_sheet_metadata(self, data_state: Any, sheet_name: str) -> Dict[str, Any]:
        """Get metadata for a specific sheet.

        Args:
            data_state: Data state object
            sheet_name: Name of the sheet

        Returns:
            Dict containing sheet metadata
        """
        if hasattr(data_state, 'metadata') and isinstance(data_state.metadata, dict):
            return data_state.metadata.get(sheet_name, {})
        return {}

    def _get_cell_color(
        self,
        data_state: Any,
        sheet_name: str,
        row_idx: int,
        col_idx: int
    ) -> Optional[str]:
        """Get the background color of a cell.

        Args:
            data_state: Data state object
            sheet_name: Name of the sheet
            row_idx: Row index
            col_idx: Column index

        Returns:
            Optional[str]: Color hex code (e.g., 'FFFF00') or None
        """
        if hasattr(data_state, 'metadata') and isinstance(data_state.metadata, dict):
            color_map = data_state.metadata.get('color_map', {})
            return color_map.get((sheet_name, row_idx, col_idx))
        return None

    def _validate_task(self, task: Dict[str, Any]) -> None:
        """Validate that a task has all required fields.

        Args:
            task: Task dictionary to validate

        Raises:
            ValueError: If task is missing required fields
        """
        required_fields = ['task_id', 'operation', 'priority', 'sheet_name',
                          'row_idx', 'col_idx', 'target_lang', 'status']

        for field in required_fields:
            if field not in task:
                raise ValueError(f"Task missing required field: {field}")

        # Validate types
        if not isinstance(task['priority'], int) or task['priority'] < 1 or task['priority'] > 10:
            raise ValueError(f"Task priority must be integer between 1-10, got {task['priority']}")

        if task['status'] != 'pending':
            raise ValueError(f"Task status must be 'pending' initially, got {task['status']}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the last split operation.

        Returns:
            Dict containing statistics
        """
        if self.task_manager.df is not None:
            return self.task_manager.get_statistics()
        return {
            'total': 0,
            'by_status': {},
            'by_language': {},
            'by_group': {}
        }
