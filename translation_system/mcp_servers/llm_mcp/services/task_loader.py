"""
Task Loader Service for LLM MCP Server
"""

import json
import logging
from typing import List, Dict, Any, Union
from pathlib import Path
import pandas as pd
from io import BytesIO

logger = logging.getLogger(__name__)


class TaskLoader:
    """Load and parse translation tasks from various formats."""

    def load_tasks(self, data: Union[bytes, str, Path], format: str = 'auto') -> List[Dict[str, Any]]:
        """Load tasks from file data."""
        try:
            # Auto-detect format if needed
            if format == 'auto':
                format = self._detect_format(data)

            if format == 'excel':
                return self._load_excel_tasks(data)
            elif format == 'json':
                return self._load_json_tasks(data)
            elif format == 'csv':
                return self._load_csv_tasks(data)
            else:
                raise ValueError(f"Unsupported format: {format}")

        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
            raise

    def _detect_format(self, data: Union[bytes, str, Path]) -> str:
        """Detect file format from data."""
        if isinstance(data, Path):
            suffix = data.suffix.lower()
            if suffix in ['.xlsx', '.xls']:
                return 'excel'
            elif suffix == '.json':
                return 'json'
            elif suffix == '.csv':
                return 'csv'

        # Try to detect from content
        if isinstance(data, bytes):
            # Check for Excel magic bytes
            if data[:4] == b'PK\x03\x04':  # XLSX
                return 'excel'
            elif data[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':  # XLS
                return 'excel'

            # Try to decode as text
            try:
                text = data.decode('utf-8')
                if text.strip().startswith('{') or text.strip().startswith('['):
                    return 'json'
                return 'csv'
            except:
                return 'excel'

        return 'excel'  # Default

    def _load_excel_tasks(self, data: Union[bytes, str, Path]) -> List[Dict[str, Any]]:
        """Load tasks from Excel file."""
        # Convert to DataFrame
        if isinstance(data, bytes):
            df = pd.read_excel(BytesIO(data))
        elif isinstance(data, (str, Path)):
            df = pd.read_excel(data)
        else:
            raise ValueError("Invalid data type for Excel loading")

        # Convert DataFrame to task list
        tasks = []
        for idx, row in df.iterrows():
            task = {
                'task_id': str(row.get('task_id', f'task_{idx}')),
                'batch_id': str(row.get('batch_id', 'batch_1')),
                'source_lang': str(row.get('source_lang', 'EN')),
                'target_lang': str(row.get('target_lang', 'ZH')),
                'source_text': str(row.get('source_text', '')),
                'target_text': str(row.get('target_text', '')),
                'task_type': str(row.get('task_type', 'normal')),
                'status': 'pending',
                'retry_count': 0
            }

            # Add context if present
            if 'context' in row and pd.notna(row['context']):
                try:
                    task['context'] = json.loads(row['context']) if isinstance(row['context'], str) else row['context']
                except:
                    task['context'] = {'raw': str(row['context'])}

            # Add metadata
            if 'sheet_name' in row:
                task['sheet_name'] = str(row['sheet_name'])
            if 'row_index' in row:
                task['row_index'] = int(row['row_index'])
            if 'column_name' in row:
                task['column_name'] = str(row['column_name'])

            tasks.append(task)

        logger.info(f"Loaded {len(tasks)} tasks from Excel")
        return tasks

    def _load_json_tasks(self, data: Union[bytes, str, Path]) -> List[Dict[str, Any]]:
        """Load tasks from JSON file."""
        if isinstance(data, bytes):
            data = data.decode('utf-8')

        if isinstance(data, (str, Path)):
            if isinstance(data, Path):
                with open(data, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
            else:
                tasks = json.loads(data)
        else:
            raise ValueError("Invalid data type for JSON loading")

        # Ensure each task has required fields
        for idx, task in enumerate(tasks):
            task.setdefault('task_id', f'task_{idx}')
            task.setdefault('batch_id', 'batch_1')
            task.setdefault('status', 'pending')
            task.setdefault('retry_count', 0)
            task.setdefault('task_type', 'normal')

        logger.info(f"Loaded {len(tasks)} tasks from JSON")
        return tasks

    def _load_csv_tasks(self, data: Union[bytes, str, Path]) -> List[Dict[str, Any]]:
        """Load tasks from CSV file."""
        # Convert to DataFrame
        if isinstance(data, bytes):
            df = pd.read_csv(BytesIO(data))
        elif isinstance(data, (str, Path)):
            df = pd.read_csv(data)
        else:
            raise ValueError("Invalid data type for CSV loading")

        # Process similar to Excel
        return self._dataframe_to_tasks(df)

    def _dataframe_to_tasks(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert DataFrame to task list."""
        tasks = []
        for idx, row in df.iterrows():
            task = {
                'task_id': str(row.get('task_id', f'task_{idx}')),
                'batch_id': str(row.get('batch_id', 'batch_1')),
                'source_lang': str(row.get('source_lang', 'EN')),
                'target_lang': str(row.get('target_lang', 'ZH')),
                'source_text': str(row.get('source_text', '')),
                'target_text': str(row.get('target_text', '')),
                'task_type': str(row.get('task_type', 'normal')),
                'status': 'pending',
                'retry_count': 0
            }
            tasks.append(task)

        return tasks

    def validate_tasks(self, tasks: List[Dict[str, Any]]) -> tuple[bool, str]:
        """Validate task list."""
        if not tasks:
            return False, "No tasks provided"

        required_fields = ['task_id', 'source_text', 'source_lang', 'target_lang']

        for idx, task in enumerate(tasks):
            for field in required_fields:
                if field not in task or not task[field]:
                    return False, f"Task {idx} missing required field: {field}"

            # Validate language codes
            if len(task['source_lang']) != 2 or len(task['target_lang']) != 2:
                return False, f"Task {idx} has invalid language codes"

        return True, "Valid"


# Global task loader instance
task_loader = TaskLoader()