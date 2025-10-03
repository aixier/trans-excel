"""Task splitter service - split Excel into translation tasks."""

import pandas as pd
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from utils.language_mapper import LanguageMapper, detect_languages
from services.excel_loader import ExcelLoader
from utils.color_detector import is_yellow_color, is_blue_color
from models.task_models import TaskType, TaskSummary

logger = logging.getLogger(__name__)


class TaskSplitterService:
    """Split Excel into translation tasks with language column compatibility and color detection."""

    def __init__(self):
        self.language_mapper = LanguageMapper()
        self.excel_loader = ExcelLoader()

    def split_excel(
        self,
        excel_path: str = None,
        excel_df: 'ExcelDataFrame' = None,
        source_lang: Optional[str] = None,
        target_langs: Optional[List[str]] = None,
        extract_context: bool = True,
        context_options: Dict[str, bool] = None
    ) -> Dict[str, Any]:
        """
        Split Excel file into translation tasks.

        Args:
            excel_path: Path to Excel file (optional if excel_df provided)
            excel_df: ExcelDataFrame object (optional if excel_path provided)
            source_lang: Source language code (CH/EN), None for auto-detect
            target_langs: Target language codes (PT/TH/VN/etc), None for all available
            extract_context: Whether to extract context
            context_options: Context extraction options

        Returns:
            Dict with tasks and summary
        """
        # Load Excel data
        if excel_df:
            # Use provided ExcelDataFrame
            logger.info(f"Splitting Excel from ExcelDataFrame: {excel_df.filename}")
            logger.info(f"Excel has {len(excel_df.sheets)} sheets")
            excel_data = excel_df.sheets
            color_map = excel_df.color_map
            comment_map = excel_df.comment_map
            logger.info(f"Color map has {len(color_map)} sheets")
            logger.info(f"Comment map has {len(comment_map)} sheets")
        elif excel_path:
            # Load from file
            logger.info(f"Splitting Excel from file: {excel_path}")
            excel_data, color_map, comment_map = self.excel_loader.load_excel_with_colors(excel_path)
        else:
            raise ValueError("Either excel_path or excel_df must be provided")

        all_tasks = []
        task_id_counter = 1

        # Process each sheet
        for sheet_name, df in excel_data.items():
            logger.info(f"Processing sheet: {sheet_name}")

            # Detect language columns
            columns = [str(col) for col in df.columns]
            lang_columns = detect_languages(columns)

            if not lang_columns:
                logger.warning(f"No language columns found in sheet: {sheet_name}")
                continue

            logger.info(f"Detected language columns: {lang_columns}")

            # Identify source and target columns
            source_col, target_cols = self._identify_columns(
                lang_columns,
                source_lang,
                target_langs
            )

            if not source_col:
                logger.warning(f"No source column found in sheet: {sheet_name}")
                continue

            if not target_cols:
                logger.warning(f"No target columns found in sheet: {sheet_name}")
                continue

            logger.info(f"Source column: {source_col} ({lang_columns[source_col]})")
            logger.info(f"Target columns: {target_cols}")

            # Extract tasks from this sheet WITH COLOR MAP
            sheet_tasks = self._extract_tasks(
                df,
                sheet_name,
                source_col,
                target_cols,
                lang_columns,
                task_id_counter,
                extract_context,
                context_options or {},
                color_map,  # Pass color map
                comment_map  # Pass comment map
            )

            all_tasks.extend(sheet_tasks)
            task_id_counter += len(sheet_tasks)

        # Allocate batches before generating summary
        logger.info(f"Allocating batches for {len(all_tasks)} tasks...")
        all_tasks = self.allocate_batches(all_tasks)

        # Generate summary
        summary = self._generate_summary(all_tasks)

        logger.info(f"Task splitting completed: {summary['total_tasks']} tasks, {summary['batch_count']} batches")

        return {
            'tasks': all_tasks,
            'summary': summary
        }

    def _identify_columns(
        self,
        lang_columns: Dict[str, str],
        source_lang: Optional[str],
        target_langs: Optional[List[str]]
    ) -> tuple[Optional[str], List[str]]:
        """
        Identify source and target columns.

        Args:
            lang_columns: Dict mapping column name to standard language code
            source_lang: Desired source language
            target_langs: Desired target languages

        Returns:
            (source_column, [target_columns])
        """
        # Reverse map: standard code -> column name
        code_to_col = {code: col for col, code in lang_columns.items()}

        # Find source column
        source_col = None
        if source_lang:
            # User specified source language
            source_col = code_to_col.get(source_lang.upper())
        else:
            # Auto-detect: prefer CH, then EN
            for lang in ['CH', 'EN']:
                if lang in code_to_col:
                    source_col = code_to_col[lang]
                    break

        # Find target columns
        target_cols = []
        if target_langs:
            # User specified target languages
            for lang in target_langs:
                col = code_to_col.get(lang.upper())
                if col:
                    target_cols.append(col)
        else:
            # All columns except source
            target_cols = [
                col for col, code in lang_columns.items()
                if col != source_col
            ]

        return source_col, target_cols

    def _extract_tasks(
        self,
        df: pd.DataFrame,
        sheet_name: str,
        source_col: str,
        target_cols: List[str],
        lang_columns: Dict[str, str],
        start_id: int,
        extract_context: bool,
        context_options: Dict[str, bool],
        color_map: Dict[str, Dict[Tuple[int, int], str]],
        comment_map: Dict[str, Dict[Tuple[int, int], str]]
    ) -> List[Dict[str, Any]]:
        """Extract tasks from DataFrame with color detection."""
        tasks = []
        task_id = start_id

        # Get source language code
        source_lang = lang_columns[source_col]

        # Get column indices
        col_names = list(df.columns)
        source_col_idx = col_names.index(source_col)

        for idx, row in df.iterrows():
            source_text = str(row[source_col]) if pd.notna(row[source_col]) else ""

            # Skip empty source text
            if not source_text or source_text.strip() == "" or source_text.lower() == 'nan':
                continue

            # Check source cell color (for yellow re-translation detection)
            # Get color from color_map directly
            source_cell_color = color_map.get(sheet_name, {}).get((int(idx), source_col_idx))
            source_is_yellow = source_cell_color and is_yellow_color(source_cell_color)
            source_is_blue = source_cell_color and is_blue_color(source_cell_color)

            # If source cell is blue, create blue shortening task
            if source_is_blue:
                context = {}
                if extract_context and context_options:
                    context = self._extract_context(df, idx, source_col, source_col, context_options)

                task = {
                    'task_id': f"task_{task_id:06d}",
                    'source_lang': source_lang,
                    'source_text': source_text,
                    'target_lang': source_lang,  # Blue task targets same language
                    'target_text': "",
                    'task_type': TaskType.BLUE.value,
                    'sheet_name': sheet_name,
                    'row_idx': int(idx),
                    'source_col': source_col,
                    'target_col': source_col,  # Same column
                    'char_count': len(source_text),
                    'context': context,
                    'batch_id': None,
                    'status': 'pending'
                }
                tasks.append(task)
                task_id += 1

            # Create tasks for each target language
            for target_col in target_cols:
                target_lang = lang_columns[target_col]
                target_value = row[target_col] if target_col in row.index else None
                target_col_idx = col_names.index(target_col)

                # Get target cell color from color_map directly
                target_cell_color = color_map.get(sheet_name, {}).get((int(idx), target_col_idx))

                # **CRITICAL LOGIC**: Determine if needs translation
                needs_translation = False
                task_type = TaskType.NORMAL

                # Priority 1: Target cell has yellow/blue color
                if target_cell_color:
                    if is_yellow_color(target_cell_color):
                        needs_translation = True
                        task_type = TaskType.YELLOW
                    elif is_blue_color(target_cell_color):
                        needs_translation = True
                        task_type = TaskType.BLUE

                # Priority 2: Source cell is yellow (re-translation needed)
                elif source_is_yellow:
                    needs_translation = True
                    task_type = TaskType.YELLOW

                # Priority 3: Empty target cell
                elif pd.isna(target_value) or str(target_value).strip() == '' or str(target_value).lower() == 'nan':
                    needs_translation = True
                    task_type = TaskType.NORMAL

                # Skip if no translation needed
                if not needs_translation:
                    continue

                target_text = str(target_value) if pd.notna(target_value) else ""

                # Extract context if enabled
                context = {}
                if extract_context and context_options:
                    context = self._extract_context(
                        df,
                        idx,
                        source_col,
                        target_col,
                        context_options
                    )

                task = {
                    'task_id': f"task_{task_id:06d}",
                    'source_lang': source_lang,
                    'source_text': source_text,
                    'target_lang': target_lang,
                    'target_text': target_text,
                    'task_type': task_type.value,
                    'sheet_name': sheet_name,
                    'row_idx': int(idx),
                    'source_col': source_col,
                    'target_col': target_col,
                    'char_count': len(source_text),
                    'context': context,
                    'batch_id': None,  # Will be assigned later
                    'status': 'pending'
                }

                tasks.append(task)
                task_id += 1

        return tasks

    def _determine_task_type(self, target_text: str) -> TaskType:
        """
        Determine task type based on target cell content.

        For now, we assume:
        - If target has text: NORMAL (already translated, might need update)
        - If target is empty: NORMAL (needs translation)

        In backend_v2, task type is determined by cell color.
        Here we don't have color info, so all tasks are NORMAL.
        """
        # TODO: Integrate with color detection if Excel color info is available
        return TaskType.NORMAL

    def _extract_context(
        self,
        df: pd.DataFrame,
        row_idx: int,
        source_col: str,
        target_col: str,
        options: Dict[str, bool]
    ) -> Dict[str, Any]:
        """Extract context information."""
        context = {}

        # Game info (first row)
        if options.get('game_info', False):
            if row_idx == 0:
                context['game_info'] = f"Row 0: {df.iloc[0].to_dict()}"

        # Comments (not available in basic pandas read)
        if options.get('comments', False):
            context['comments'] = None  # Requires openpyxl integration

        # Neighbors (adjacent cells)
        if options.get('neighbors', False):
            neighbors = {}
            if row_idx > 0:
                neighbors['prev'] = str(df.iloc[row_idx - 1][source_col])
            if row_idx < len(df) - 1:
                neighbors['next'] = str(df.iloc[row_idx + 1][source_col])
            context['neighbors'] = neighbors

        # Content analysis
        if options.get('content_analysis', False):
            context['content_type'] = self._analyze_content_type(
                str(df.iloc[row_idx][source_col])
            )

        # Sheet type
        if options.get('sheet_type', False):
            context['sheet_type'] = self._infer_sheet_type(df.columns.tolist())

        return context

    def _analyze_content_type(self, text: str) -> str:
        """Analyze content type (UI/dialogue/item/etc)."""
        text_lower = text.lower()

        if any(keyword in text_lower for keyword in ['button', 'menu', 'tab', 'label']):
            return 'UI'
        elif any(keyword in text_lower for keyword in ['says', 'asks', 'replies']):
            return 'Dialogue'
        elif any(keyword in text_lower for keyword in ['sword', 'shield', 'potion', 'item']):
            return 'Item'
        else:
            return 'General'

    def _infer_sheet_type(self, columns: List[str]) -> str:
        """Infer sheet type from column names."""
        columns_str = ' '.join(columns).lower()

        if 'ui' in columns_str:
            return 'UI'
        elif 'dialogue' in columns_str or 'dialog' in columns_str:
            return 'Dialogue'
        elif 'item' in columns_str:
            return 'Item'
        else:
            return 'General'

    def _generate_summary(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate task summary with batch distribution."""
        summary = TaskSummary()

        summary.total_tasks = len(tasks)

        # Task breakdown by type
        for task in tasks:
            task_type = task['task_type']
            summary.task_breakdown[task_type] = summary.task_breakdown.get(task_type, 0) + 1

        # Language distribution (task count)
        for task in tasks:
            target_lang = task['target_lang']
            summary.language_distribution[target_lang] = \
                summary.language_distribution.get(target_lang, 0) + 1

        # Batch distribution by language (batch count)
        batch_distribution = {}
        for task in tasks:
            if task.get('batch_id'):
                lang = task['target_lang']
                batch_id = task['batch_id']
                if lang not in batch_distribution:
                    batch_distribution[lang] = set()
                batch_distribution[lang].add(batch_id)

        # Convert sets to counts
        batch_distribution = {lang: len(batches) for lang, batches in batch_distribution.items()}

        # Type batch distribution (批次数量按任务类型)
        type_batch_distribution = {}
        for task in tasks:
            if task.get('batch_id'):
                task_type = task['task_type']
                batch_id = task['batch_id']
                if task_type not in type_batch_distribution:
                    type_batch_distribution[task_type] = set()
                type_batch_distribution[task_type].add(batch_id)

        # Convert sets to counts
        type_batch_distribution = {t: len(batches) for t, batches in type_batch_distribution.items()}

        # Total batch count
        unique_batches = len(set(task['batch_id'] for task in tasks if task.get('batch_id')))
        summary.batch_count = unique_batches

        # Total characters
        summary.total_chars = sum(task['char_count'] for task in tasks)

        # Estimate cost (rough: $0.01 per 1000 chars)
        summary.estimated_cost = (summary.total_chars / 1000) * 0.01

        # Build result dict
        result = summary.to_dict()
        result['batch_distribution'] = batch_distribution  # 语言批次分布
        result['type_batch_distribution'] = type_batch_distribution  # 类型批次分布

        return result


    def allocate_batches(self, tasks: List[Dict[str, Any]], max_chars_per_batch: int = 50000) -> List[Dict[str, Any]]:
        """
        Allocate tasks to batches.

        Args:
            tasks: List of tasks
            max_chars_per_batch: Maximum characters per batch

        Returns:
            Tasks with batch_id assigned
        """
        # Group by target language first
        by_lang = {}
        for task in tasks:
            lang = task['target_lang']
            if lang not in by_lang:
                by_lang[lang] = []
            by_lang[lang].append(task)

        batch_counter = 1

        # Allocate batches per language
        for lang, lang_tasks in by_lang.items():
            current_batch = []
            current_chars = 0

            for task in lang_tasks:
                task_chars = task['char_count']

                if current_chars + task_chars > max_chars_per_batch and current_batch:
                    # Assign batch ID to current batch
                    batch_id = f"batch_{batch_counter:03d}"
                    for t in current_batch:
                        t['batch_id'] = batch_id
                    batch_counter += 1

                    # Start new batch
                    current_batch = [task]
                    current_chars = task_chars
                else:
                    current_batch.append(task)
                    current_chars += task_chars

            # Assign remaining tasks
            if current_batch:
                batch_id = f"batch_{batch_counter:03d}"
                for t in current_batch:
                    t['batch_id'] = batch_id
                batch_counter += 1

        # Update batch_count in summary
        unique_batches = len(set(task['batch_id'] for task in tasks))
        logger.info(f"Allocated {unique_batches} batches")

        return tasks


# Create singleton instance
task_splitter_service = TaskSplitterService()
