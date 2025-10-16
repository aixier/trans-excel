"""Excel writer service for writing translation results back to Excel."""

import logging
import asyncio
from typing import Dict, Any, Optional, List
import pandas as pd
from pathlib import Path
from datetime import datetime

from models.excel_dataframe import ExcelDataFrame
from models.task_dataframe import TaskDataFrameManager, TaskStatus
from utils.pipeline_session_manager import pipeline_session_manager

logger = logging.getLogger(__name__)


class ExcelWriter:
    """Write translation results back to original Excel files."""

    def __init__(self):
        """Initialize Excel writer."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.color_mapping = {
            'completed': '#D3D3D3',  # Light gray for completed
            'failed': '#FFB6C1',      # Light red for failed
            'processing': '#FFFFE0',  # Light yellow for processing
            'pending': None           # Keep original color
        }

    async def write_back_results(
        self,
        session_id: str,
        task_df: pd.DataFrame = None
    ) -> Dict[str, Any]:
        """
        Write translation results back to original Excel DataFrame.

        Args:
            session_id: Session ID
            task_df: Task DataFrame (if None, get from session manager)

        Returns:
            Write-back statistics
        """
        start_time = datetime.now()
        self.logger.info(f"Starting write-back for session {session_id}")

        try:
            # Get Excel DataFrames manager
            excel_manager = pipeline_session_manager.get_excel_manager(session_id)
            if not excel_manager:
                raise ValueError(f"No Excel manager found for session {session_id}")

            # Get task DataFrame if not provided
            if task_df is None:
                task_manager = pipeline_session_manager.get_tasks(session_id)
                if not task_manager or task_manager.df is None:
                    raise ValueError(f"No task manager found for session {session_id}")
                task_df = task_manager.df

            # Statistics
            stats = {
                'total_tasks': len(task_df),
                'written_back': 0,
                'skipped': 0,
                'failed': 0,
                'sheets_updated': set()
            }

            # Process each task
            for idx, task in task_df.iterrows():
                try:
                    if task['status'] == TaskStatus.COMPLETED and task.get('result'):
                        # Write result back to cell
                        success = await self._write_single_result(
                            excel_manager,
                            task
                        )
                        if success:
                            stats['written_back'] += 1
                            stats['sheets_updated'].add(task.get('sheet_name', 'Unknown'))
                        else:
                            stats['failed'] += 1
                    else:
                        stats['skipped'] += 1

                except Exception as e:
                    self.logger.error(f"Failed to write task {task.get('task_id')}: {e}")
                    stats['failed'] += 1

            # Convert set to list for JSON serialization
            stats['sheets_updated'] = list(stats['sheets_updated'])
            stats['duration_seconds'] = (datetime.now() - start_time).total_seconds()

            self.logger.info(
                f"Write-back completed: {stats['written_back']} written, "
                f"{stats['skipped']} skipped, {stats['failed']} failed"
            )

            return stats

        except Exception as e:
            self.logger.error(f"Write-back failed: {str(e)}")
            raise

    async def _write_single_result(
        self,
        excel_manager: ExcelDataFramesManager,
        task: pd.Series
    ) -> bool:
        """
        Write a single translation result back to Excel.

        Args:
            excel_manager: Excel DataFrames manager
            task: Task series with translation result

        Returns:
            True if successful
        """
        try:
            # Extract position information
            sheet_name = task.get('sheet_name')
            row = task.get('row')
            col = task.get('col')
            result = task.get('result')

            if not all([sheet_name, row is not None, col is not None, result]):
                self.logger.warning(
                    f"Missing position info for task {task.get('task_id')}: "
                    f"sheet={sheet_name}, row={row}, col={col}"
                )
                return False

            # Get the sheet DataFrame
            sheet_df = excel_manager.dataframes.get(sheet_name)
            if sheet_df is None:
                self.logger.error(f"Sheet {sheet_name} not found in Excel manager")
                return False

            # Write the result
            try:
                # Ensure indices are within bounds
                if row >= len(sheet_df) or col >= len(sheet_df.columns):
                    self.logger.error(
                        f"Position out of bounds: row={row}/{len(sheet_df)}, "
                        f"col={col}/{len(sheet_df.columns)}"
                    )
                    return False

                # Write the translated text
                sheet_df.iloc[row, col] = result

                # Update cell color if style tracking is enabled
                if hasattr(excel_manager, 'cell_styles'):
                    self._update_cell_style(
                        excel_manager,
                        sheet_name,
                        row,
                        col,
                        task['status']
                    )

                return True

            except Exception as e:
                self.logger.error(f"Failed to write to DataFrame: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Error in _write_single_result: {e}")
            return False

    def _update_cell_style(
        self,
        excel_manager: ExcelDataFramesManager,
        sheet_name: str,
        row: int,
        col: int,
        status: str
    ):
        """
        Update cell style based on translation status.

        Args:
            excel_manager: Excel DataFrames manager
            sheet_name: Sheet name
            row: Row index
            col: Column index
            status: Task status
        """
        try:
            if not hasattr(excel_manager, 'cell_styles'):
                excel_manager.cell_styles = {}

            if sheet_name not in excel_manager.cell_styles:
                excel_manager.cell_styles[sheet_name] = {}

            # Store style information
            cell_key = f"{row},{col}"
            excel_manager.cell_styles[sheet_name][cell_key] = {
                'background_color': self.color_mapping.get(status.lower()),
                'status': status,
                'updated_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.warning(f"Failed to update cell style: {e}")

    async def write_batch_results(
        self,
        session_id: str,
        batch_id: str
    ) -> Dict[str, Any]:
        """
        Write results for a specific batch.

        Args:
            session_id: Session ID
            batch_id: Batch ID

        Returns:
            Write-back statistics
        """
        # Get task manager
        task_manager = pipeline_session_manager.get_tasks(session_id)
        if not task_manager or task_manager.df is None:
            raise ValueError(f"No task manager found for session {session_id}")

        # Filter tasks by batch
        task_df = task_manager.df
        batch_tasks = task_df[task_df['batch_id'] == batch_id]

        if batch_tasks.empty:
            self.logger.warning(f"No tasks found for batch {batch_id}")
            return {'written_back': 0, 'skipped': 0, 'failed': 0}

        # Write back batch results
        return await self.write_back_results(session_id, batch_tasks)

    async def mark_cells_completed(
        self,
        session_id: str,
        task_ids: List[str]
    ):
        """
        Mark specific cells as completed by updating their style.

        Args:
            session_id: Session ID
            task_ids: List of task IDs to mark as completed
        """
        excel_manager = pipeline_session_manager.get_excel_manager(session_id)
        task_manager = pipeline_session_manager.get_tasks(session_id)

        if not excel_manager or not task_manager:
            self.logger.error("Managers not found for marking cells")
            return

        task_df = task_manager.df
        for task_id in task_ids:
            task = task_df[task_df['task_id'] == task_id]
            if not task.empty:
                task = task.iloc[0]
                self._update_cell_style(
                    excel_manager,
                    task['sheet_name'],
                    task['row'],
                    task['col'],
                    'completed'
                )

    def get_write_back_progress(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get write-back progress for a session.

        Args:
            session_id: Session ID

        Returns:
            Progress statistics
        """
        try:
            task_manager = pipeline_session_manager.get_tasks(session_id)
            if not task_manager or task_manager.df is None:
                return {'total': 0, 'written': 0, 'pending': 0}

            task_df = task_manager.df
            completed = task_df[task_df['status'] == TaskStatus.COMPLETED]

            # Check which have been written back
            # This would require tracking write-back status
            # For now, assume all completed tasks are written
            return {
                'total': len(task_df),
                'written': len(completed),
                'pending': len(task_df) - len(completed),
                'by_sheet': self._get_sheet_statistics(task_df)
            }

        except Exception as e:
            self.logger.error(f"Failed to get write-back progress: {e}")
            return {'total': 0, 'written': 0, 'pending': 0}

    def _get_sheet_statistics(self, task_df: pd.DataFrame) -> Dict[str, Dict[str, int]]:
        """
        Get statistics by sheet.

        Args:
            task_df: Task DataFrame

        Returns:
            Statistics by sheet
        """
        stats = {}
        for sheet_name in task_df['sheet_name'].unique():
            sheet_tasks = task_df[task_df['sheet_name'] == sheet_name]
            stats[sheet_name] = {
                'total': len(sheet_tasks),
                'completed': len(sheet_tasks[sheet_tasks['status'] == TaskStatus.COMPLETED]),
                'failed': len(sheet_tasks[sheet_tasks['status'] == TaskStatus.FAILED]),
                'pending': len(sheet_tasks[sheet_tasks['status'] == TaskStatus.PENDING])
            }
        return stats


# Global Excel writer instance
excel_writer = ExcelWriter()