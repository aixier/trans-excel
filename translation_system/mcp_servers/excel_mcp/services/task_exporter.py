"""Task exporter service - export tasks to Excel/JSON/CSV."""

import pandas as pd
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskExporter:
    """Export tasks to various formats."""

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize task exporter.

        Args:
            output_dir: Directory to save exported files
        """
        if output_dir is None:
            # Use the exports directory relative to the server location
            import os
            server_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.output_dir = server_dir / "exports"
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_to_excel(
        self,
        tasks: List[Dict[str, Any]],
        session_id: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Export tasks to Excel file.

        Args:
            tasks: List of tasks
            session_id: Session ID
            filename: Optional custom filename

        Returns:
            Path to exported Excel file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tasks_{session_id}_{timestamp}.xlsx"

        output_path = self.output_dir / filename

        # Convert tasks to DataFrame
        df = pd.DataFrame(tasks)

        # Flatten context dict to string
        if 'context' in df.columns:
            df['context'] = df['context'].apply(lambda x: json.dumps(x, ensure_ascii=False) if x else "")

        # Select and order columns
        columns = [
            'task_id',
            'batch_id',
            'source_lang',
            'source_text',
            'target_lang',
            'target_text',
            'task_type',
            'sheet_name',
            'row_idx',
            'source_col',
            'target_col',
            'char_count',
            'context',
            'status'
        ]

        # Only include columns that exist
        export_columns = [col for col in columns if col in df.columns]
        df_export = df[export_columns]

        # Export to Excel
        df_export.to_excel(output_path, index=False, engine='openpyxl')

        logger.info(f"Exported {len(tasks)} tasks to Excel: {output_path}")
        return str(output_path)

    def export_to_json(
        self,
        tasks: List[Dict[str, Any]],
        session_id: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Export tasks to JSON file.

        Args:
            tasks: List of tasks
            session_id: Session ID
            filename: Optional custom filename

        Returns:
            Path to exported JSON file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tasks_{session_id}_{timestamp}.json"

        output_path = self.output_dir / filename

        # Export to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported {len(tasks)} tasks to JSON: {output_path}")
        return str(output_path)

    def export_to_csv(
        self,
        tasks: List[Dict[str, Any]],
        session_id: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Export tasks to CSV file.

        Args:
            tasks: List of tasks
            session_id: Session ID
            filename: Optional custom filename

        Returns:
            Path to exported CSV file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tasks_{session_id}_{timestamp}.csv"

        output_path = self.output_dir / filename

        # Convert tasks to DataFrame
        df = pd.DataFrame(tasks)

        # Flatten context dict to string
        if 'context' in df.columns:
            df['context'] = df['context'].apply(lambda x: json.dumps(x, ensure_ascii=False) if x else "")

        # Export to CSV
        df.to_csv(output_path, index=False, encoding='utf-8')

        logger.info(f"Exported {len(tasks)} tasks to CSV: {output_path}")
        return str(output_path)

    def export(
        self,
        tasks: List[Dict[str, Any]],
        session_id: str,
        format: str = 'excel',
        filename: Optional[str] = None
    ) -> str:
        """
        Export tasks to specified format.

        Args:
            tasks: List of tasks
            session_id: Session ID
            format: Export format (excel/json/csv)
            filename: Optional custom filename

        Returns:
            Path to exported file
        """
        format = format.lower()

        if format == 'excel' or format == 'xlsx':
            return self.export_to_excel(tasks, session_id, filename)
        elif format == 'json':
            return self.export_to_json(tasks, session_id, filename)
        elif format == 'csv':
            return self.export_to_csv(tasks, session_id, filename)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = path.stat()
        return {
            'filename': path.name,
            'size': stat.st_size,
            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }


# Create singleton instance
task_exporter = TaskExporter()
