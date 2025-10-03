"""
Result Exporter Service for LLM MCP Server
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class ResultExporter:
    """Export translation results to various formats."""

    def __init__(self, export_dir: str = None):
        self.export_dir = Path(export_dir or '/mnt/d/work/trans_excel/translation_system/mcp_servers/llm_mcp/exports')
        self.export_dir.mkdir(exist_ok=True)

    def export(
        self,
        tasks: List[Dict[str, Any]],
        session_id: str,
        format: str = 'excel',
        merge_source: bool = True
    ) -> Path:
        """Export translation results."""
        try:
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"translated_{session_id}_{timestamp}"

            if format == 'excel':
                return self._export_excel(tasks, filename, merge_source)
            elif format == 'json':
                return self._export_json(tasks, filename)
            elif format == 'csv':
                return self._export_csv(tasks, filename, merge_source)
            else:
                raise ValueError(f"Unsupported format: {format}")

        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise

    def _export_excel(self, tasks: List[Dict], filename: str, merge_source: bool) -> Path:
        """Export to Excel format."""
        output_path = self.export_dir / f"{filename}.xlsx"

        # Prepare data
        data = []
        for task in tasks:
            row = {
                'task_id': task.get('task_id'),
                'batch_id': task.get('batch_id'),
                'source_lang': task.get('source_lang'),
                'target_lang': task.get('target_lang'),
                'task_type': task.get('task_type', 'normal'),
                'status': task.get('status', 'pending')
            }

            # Add text columns
            if merge_source:
                row['source_text'] = task.get('source_text', '')

            row['target_text'] = task.get('target_text', '')

            # Add metadata
            if task.get('sheet_name'):
                row['sheet_name'] = task['sheet_name']
            if task.get('row_index') is not None:
                row['row_index'] = task['row_index']
            if task.get('column_name'):
                row['column_name'] = task['column_name']

            # Add statistics
            if task.get('tokens_used'):
                row['tokens'] = task['tokens_used']
            if task.get('cost'):
                row['cost'] = task['cost']
            if task.get('error'):
                row['error'] = task['error']

            data.append(row)

        # Create DataFrame and save
        df = pd.DataFrame(data)

        # Group by sheet if sheet_name exists
        if 'sheet_name' in df.columns and df['sheet_name'].notna().any():
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Group by sheet
                for sheet_name in df['sheet_name'].unique():
                    if pd.notna(sheet_name):
                        sheet_df = df[df['sheet_name'] == sheet_name].copy()
                        # Remove sheet_name column from output
                        sheet_df = sheet_df.drop('sheet_name', axis=1)
                        # Sort by row_index if exists
                        if 'row_index' in sheet_df.columns:
                            sheet_df = sheet_df.sort_values('row_index')
                        sheet_df.to_excel(writer, sheet_name=str(sheet_name), index=False)

                # Add tasks without sheet_name
                no_sheet_df = df[df['sheet_name'].isna()]
                if not no_sheet_df.empty:
                    no_sheet_df.to_excel(writer, sheet_name='Other', index=False)

                # Add summary sheet
                summary_df = self._create_summary_df(tasks)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
        else:
            # Single sheet export
            df.to_excel(output_path, index=False)

        logger.info(f"Exported {len(tasks)} tasks to {output_path}")
        return output_path

    def _export_json(self, tasks: List[Dict], filename: str) -> Path:
        """Export to JSON format."""
        output_path = self.export_dir / f"{filename}.json"

        # Clean up tasks for JSON export
        clean_tasks = []
        for task in tasks:
            clean_task = {
                k: v for k, v in task.items()
                if v is not None and k not in ['_id', '__v']
            }
            clean_tasks.append(clean_task)

        # Write JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(clean_tasks, f, ensure_ascii=False, indent=2)

        logger.info(f"Exported {len(tasks)} tasks to {output_path}")
        return output_path

    def _export_csv(self, tasks: List[Dict], filename: str, merge_source: bool) -> Path:
        """Export to CSV format."""
        output_path = self.export_dir / f"{filename}.csv"

        # Prepare data similar to Excel
        data = []
        for task in tasks:
            row = {
                'task_id': task.get('task_id'),
                'batch_id': task.get('batch_id'),
                'source_lang': task.get('source_lang'),
                'target_lang': task.get('target_lang'),
                'task_type': task.get('task_type'),
                'status': task.get('status')
            }

            if merge_source:
                row['source_text'] = task.get('source_text', '')

            row['target_text'] = task.get('target_text', '')

            # Add metadata
            for key in ['sheet_name', 'row_index', 'column_name', 'tokens', 'cost', 'error']:
                if key in task:
                    row[key] = task[key]

            data.append(row)

        # Create DataFrame and save
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

        logger.info(f"Exported {len(tasks)} tasks to {output_path}")
        return output_path

    def _create_summary_df(self, tasks: List[Dict]) -> pd.DataFrame:
        """Create summary statistics DataFrame."""
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.get('status') == 'completed')
        failed_tasks = sum(1 for t in tasks if t.get('status') == 'failed')
        pending_tasks = sum(1 for t in tasks if t.get('status') == 'pending')

        total_tokens = sum(t.get('tokens_used', 0) for t in tasks)
        total_cost = sum(t.get('cost', 0) for t in tasks)

        # Language pair statistics
        lang_pairs = {}
        for task in tasks:
            pair = f"{task.get('source_lang')}->{task.get('target_lang')}"
            if pair not in lang_pairs:
                lang_pairs[pair] = {'total': 0, 'completed': 0, 'failed': 0}
            lang_pairs[pair]['total'] += 1
            if task.get('status') == 'completed':
                lang_pairs[pair]['completed'] += 1
            elif task.get('status') == 'failed':
                lang_pairs[pair]['failed'] += 1

        # Create summary data
        summary_data = [
            {'Metric': 'Total Tasks', 'Value': total_tasks},
            {'Metric': 'Completed Tasks', 'Value': completed_tasks},
            {'Metric': 'Failed Tasks', 'Value': failed_tasks},
            {'Metric': 'Pending Tasks', 'Value': pending_tasks},
            {'Metric': 'Success Rate', 'Value': f"{(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"},
            {'Metric': 'Total Tokens', 'Value': total_tokens},
            {'Metric': 'Total Cost', 'Value': f"${total_cost:.4f}"},
            {'Metric': '', 'Value': ''},  # Separator
            {'Metric': 'Language Pairs', 'Value': ''},
        ]

        # Add language pair stats
        for pair, stats in lang_pairs.items():
            summary_data.append({
                'Metric': f"  {pair}",
                'Value': f"{stats['completed']}/{stats['total']} ({stats['completed']/stats['total']*100:.1f}%)"
            })

        return pd.DataFrame(summary_data)


# Global result exporter instance
result_exporter = ResultExporter()