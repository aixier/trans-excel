"""Task splitting service - core logic for task generation."""

import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from models.excel_dataframe import ExcelDataFrame
from models.task_dataframe import TaskDataFrameManager
from models.game_info import GameInfo
from utils.color_detector import is_yellow_color, is_blue_color
from services.context_extractor import ContextExtractor
from services.batch_allocator import BatchAllocator
from services.language_detector import LanguageDetector


class TaskSplitter:
    """Split Excel into translation tasks."""

    def __init__(self, excel_df: ExcelDataFrame, game_info: GameInfo = None, extract_context: bool = True, context_options: Dict[str, bool] = None, max_chars_per_batch: int = None):
        """
        Initialize task splitter.

        Args:
            excel_df: Excel data structure
            game_info: Game information for context
            extract_context: Whether to extract row context (slower but provides more info)
            context_options: Dict specifying which context types to extract (only applies when extract_context=True)
            max_chars_per_batch: Custom batch size (None = use config default)
        """
        self.excel_df = excel_df
        self.game_info = game_info
        self.extract_context = extract_context
        self.context_extractor = ContextExtractor(game_info, context_options) if extract_context else None
        self.batch_allocator = BatchAllocator(max_chars_per_batch)
        self.language_detector = LanguageDetector()
        self.task_manager = TaskDataFrameManager()

    def split_tasks(
        self,
        source_lang: str = None,
        target_langs: List[str] = None
    ) -> TaskDataFrameManager:
        """
        Split Excel into tasks and create task DataFrame.

        Args:
            source_lang: Source language (CH/EN), None for auto-detect
            target_langs: Target languages (PT/TH/VN), None for all available

        Returns:
            TaskDataFrameManager with all tasks
        """
        all_tasks = []
        task_counter = 0

        # Process each sheet
        for sheet_name in self.excel_df.get_sheet_names():
            sheet_tasks = self._process_sheet(
                sheet_name,
                source_lang,
                target_langs,
                task_counter
            )
            all_tasks.extend(sheet_tasks)
            task_counter += len(sheet_tasks)

        # Allocate batches
        all_tasks = self.batch_allocator.allocate_batches(all_tasks)

        # Create DataFrame
        for task in all_tasks:
            self.task_manager.add_task(task)

        return self.task_manager

    def _process_sheet(
        self,
        sheet_name: str,
        source_lang: str,
        target_langs: List[str],
        start_counter: int
    ) -> List[Dict[str, Any]]:
        """Process a single sheet and generate tasks."""
        df = self.excel_df.get_sheet(sheet_name)
        if df is None:
            return []

        tasks = []

        # Pre-fetch color map for this sheet (already loaded in memory)
        sheet_color_map = self.excel_df.color_map.get(sheet_name, {})

        # Check for explicit language columns by name
        column_names = [str(col).upper() for col in df.columns]
        has_explicit_columns = False

        # Map column names to indices
        col_mapping = {}
        for idx, col in enumerate(column_names):
            if col in ['CH', 'CN', '中文']:
                col_mapping['CH'] = idx
                has_explicit_columns = True
            elif col in ['EN', 'ENGLISH', '英文']:
                col_mapping['EN'] = idx
                has_explicit_columns = True
            elif col in ['TH', 'THAI', '泰语', '泰文']:
                col_mapping['TH'] = idx
                has_explicit_columns = True
            elif col in ['PT', 'PT-BR', 'PORTUGUESE', '葡萄牙语']:
                col_mapping['PT'] = idx
                has_explicit_columns = True
            elif col in ['VN', 'VI', 'VIETNAMESE', '越南语']:
                col_mapping['VN'] = idx
                has_explicit_columns = True
            elif col in ['TR', 'TURKISH', '土耳其语', '土耳其文']:
                col_mapping['TR'] = idx
                has_explicit_columns = True
            elif col in ['IND', 'ID', 'INDONESIAN', '印尼语', '印度尼西亚语']:
                col_mapping['IND'] = idx
                has_explicit_columns = True
            elif col in ['ES', 'SPANISH', '西班牙语', '西语']:
                col_mapping['ES'] = idx
                has_explicit_columns = True
            elif col in ['TW', '繁体', '繁中', 'TAIWAN', 'TCHINESE', '繁體中文', '繁體']:
                col_mapping['TW'] = idx
                has_explicit_columns = True

        # If we have explicit columns, use them directly
        if has_explicit_columns:
            # Determine source column based on source_lang or default to CH if exists
            if source_lang == 'CH' and 'CH' in col_mapping:
                source_col_idx = col_mapping['CH']
                actual_source_lang = 'CH'
            elif source_lang == 'EN' and 'EN' in col_mapping:
                source_col_idx = col_mapping['EN']
                actual_source_lang = 'EN'
            elif 'CH' in col_mapping:  # Default to CH if available
                source_col_idx = col_mapping['CH']
                actual_source_lang = 'CH'
            elif 'EN' in col_mapping:  # Otherwise try EN
                source_col_idx = col_mapping['EN']
                actual_source_lang = 'EN'
            else:
                # Fall back to language detection
                lang_analysis = self.language_detector.analyze_sheet(df)
                lang_columns = lang_analysis['language_columns']
                if lang_columns['source_columns']:
                    source_col_idx = lang_columns['source_columns'][0]
                    actual_source_lang = source_lang or 'CH'
                else:
                    return []

            # Process each row with explicit columns - optimized version
            # Convert DataFrame to numpy array for faster access
            df_values = df.values

            for row_idx in range(len(df_values)):
                # Get source text (direct array access)
                source_text = df_values[row_idx, source_col_idx]
                if pd.isna(source_text) or not str(source_text).strip():
                    continue

                source_text = str(source_text)

                # Check source cell color (important for yellow re-translation)
                source_cell_color = sheet_color_map.get((row_idx, source_col_idx))
                source_is_yellow = source_cell_color and is_yellow_color(source_cell_color)
                source_is_blue = source_cell_color and is_blue_color(source_cell_color)

                # ✨ Check if EN column is yellow (EN as final version)
                en_reference = None
                en_is_yellow = False
                en_as_source = False  # ✨ EN作为主源文本
                en_col_idx = col_mapping.get('EN')

                if en_col_idx is not None:
                    # Check if EN cell is yellow
                    en_cell_color = sheet_color_map.get((row_idx, en_col_idx))
                    if en_cell_color and is_yellow_color(en_cell_color):
                        en_is_yellow = True
                        # EN is yellow → use as main source (not just reference)
                        en_value = df_values[row_idx, en_col_idx] if en_col_idx < len(df.columns) else None
                        if pd.notna(en_value) and str(en_value).strip():
                            en_reference = str(en_value)

                            # ✅ If only EN is yellow (CH not yellow), EN becomes main source
                            if not source_is_yellow:
                                en_as_source = True

                # If source cell has blue color, create a blue task for shortening
                if source_is_blue:
                    task = self._create_task(
                        sheet_name,
                        row_idx,
                        source_col_idx,
                        source_col_idx,
                        source_text,
                        actual_source_lang,
                        actual_source_lang,
                        start_counter + len(tasks),
                        'blue'
                    )
                    tasks.append(task)

                # Check each target language
                for target_lang in target_langs:
                    # ✨ Skip EN if it's yellow (already finalized), unless in CAPS sheet
                    # In CAPS sheet, we still need to process yellow EN for uppercase conversion
                    if target_lang == 'EN' and en_is_yellow and 'caps' not in sheet_name.lower():
                        continue  # EN is yellow = already finalized, skip (unless CAPS sheet)

                    if target_lang in col_mapping:
                        target_col = col_mapping[target_lang]

                        # Get target cell value (direct array access)
                        target_value = df_values[row_idx, target_col]

                        # Check target cell color
                        target_color = sheet_color_map.get((row_idx, target_col))

                        # Determine if needs translation and task type
                        needs_translation = False
                        task_type = 'normal'

                        # ✅ Priority 1: Target cell is blue → Shortening task
                        if target_color and is_blue_color(target_color):
                            needs_translation = True
                            task_type = 'blue'

                        # ✅ Priority 2: Check sheet name for special types (caps) - moved up for CAPS priority
                        elif 'caps' in sheet_name.lower():
                            if source_text and source_text.strip():
                                needs_translation = True
                                task_type = 'caps'  # ✨ CAPS task type

                        # ✅ Priority 3: Target cell is yellow → Skip (already modified, final version)
                        elif target_color and is_yellow_color(target_color):
                            needs_translation = False
                            continue  # Yellow target = already finalized, skip translation

                        # ✅ Priority 4: Source or EN is yellow → Force re-translate (regardless of content)
                        elif source_is_yellow or en_is_yellow:
                            needs_translation = True
                            task_type = 'yellow'  # Force re-translate all right columns

                        # Priority 5: Empty target cell needs normal translation
                        elif pd.isna(target_value) or str(target_value).strip() == '':
                            if source_text and source_text.strip():
                                needs_translation = True
                                task_type = 'normal'

                        if needs_translation:
                            # ✅ Determine actual source text and language
                            # If EN is yellow and CH is not, use EN as main source
                            if en_as_source:
                                actual_task_source = en_reference
                                actual_task_source_lang = 'EN'
                                actual_reference = source_text  # CH becomes context reference
                            else:
                                actual_task_source = source_text
                                actual_task_source_lang = actual_source_lang
                                actual_reference = en_reference or ''

                            # Create task with type
                            task = self._create_task(
                                sheet_name,
                                row_idx,
                                source_col_idx,
                                target_col,
                                actual_task_source,  # ✨ 可能是EN内容
                                actual_task_source_lang,  # ✨ 可能是'EN'
                                target_lang,
                                start_counter + len(tasks),
                                task_type,
                                reference_en=actual_reference  # ✨ CH作为参考
                            )
                            tasks.append(task)

                # ✨ Special handling for CAPS sheets with yellow EN cells
                # In CAPS sheets, even if EN is yellow (used as source),
                # we also need to create a CH→EN yellow task for re-translation and uppercase
                if 'caps' in sheet_name.lower() and en_is_yellow:
                    # EN is yellow but CH is also source, create CH→EN yellow task
                    en_col_idx = col_mapping.get('EN')
                    if en_col_idx is not None and 'CH' in col_mapping:
                        task = self._create_task(
                            sheet_name,
                            row_idx,
                            col_mapping['CH'],  # CH as source
                            en_col_idx,         # EN as target
                            source_text,        # CH text as source
                            'CH',               # Source language is CH
                            'EN',               # Target language is EN
                            start_counter + len(tasks),
                            'yellow',           # Yellow task for re-translation
                            reference_en=en_reference  # Current EN as reference
                        )
                        tasks.append(task)

        else:
            # Fall back to language detection
            lang_analysis = self.language_detector.analyze_sheet(df)
            lang_columns = lang_analysis['language_columns']

            # Use detected languages if not specified
            if not source_lang and lang_analysis['source_languages']:
                source_lang = lang_analysis['source_languages'][0]

            if not target_langs:
                target_langs = lang_analysis['target_languages']

            # If no language info, return empty
            if not source_lang or not target_langs:
                return []

            # Process each row
            for row_idx in range(len(df)):
                # Find source text
                source_text = None
                source_col = None

                for col_idx in lang_columns['source_columns']:
                    value = df.iloc[row_idx, col_idx]
                    if pd.notna(value) and isinstance(value, str) and value.strip():
                        source_text = value
                        source_col = col_idx
                        break

                # Skip if no source text
                if not source_text:
                    continue

                # Check if source cell itself has blue color (needs shortening)
                source_cell_color = self.excel_df.get_cell_color(sheet_name, row_idx, source_col)
                if source_cell_color and is_blue_color(source_cell_color):
                    # Create a blue task for shortening the source text itself
                    task = self._create_task(
                        sheet_name,
                        row_idx,
                        source_col,
                        source_col,  # Target is the same as source
                        source_text,
                        source_lang,
                        source_lang,  # Target lang is same as source lang
                        start_counter + len(tasks),
                        'blue'  # This is a blue shortening task
                    )
                    tasks.append(task)

            # Check each target language
            for target_lang in target_langs:
                # Find target column for this language
                target_columns = lang_columns.get(f'{target_lang}_columns', [])

                for target_col in target_columns:
                    # Check if translation is needed
                    needs_translation = self._check_needs_translation(
                        sheet_name, row_idx, target_col, source_text
                    )

                    if needs_translation:
                        # Determine task type based on TARGET cell color (not source)
                        task_type = self._determine_task_type(sheet_name, row_idx, target_col)

                        # Create task with type
                        task = self._create_task(
                            sheet_name,
                            row_idx,
                            source_col,
                            target_col,
                            source_text,
                            source_lang,
                            target_lang,
                            start_counter + len(tasks),
                            task_type
                        )
                        tasks.append(task)

        return tasks

    def _check_needs_translation(
        self,
        sheet_name: str,
        row_idx: int,
        col_idx: int,
        source_text: str
    ) -> bool:
        """Check if a cell needs translation."""
        df = self.excel_df.get_sheet(sheet_name)
        if df is None:
            return False

        # Get current value
        current_value = df.iloc[row_idx, col_idx] if col_idx < len(df.columns) else None

        # Check cell color
        color = self.excel_df.get_cell_color(sheet_name, row_idx, col_idx)

        # Yellow cells always need translation
        if color and is_yellow_color(color):
            return True

        # Blue cells need translation
        if color and is_blue_color(color):
            return True

        # Empty cells need translation if source has content
        if pd.isna(current_value) or str(current_value).strip() == '':
            return bool(source_text and source_text.strip())

        # If already has content and no color marking, skip
        return False

    def _determine_task_type(
        self,
        sheet_name: str,
        row_idx: int,
        col_idx: int
    ) -> str:
        """Determine task type based on cell color and sheet name."""
        # First check cell colors (highest priority)
        color = self.excel_df.get_cell_color(sheet_name, row_idx, col_idx)

        if color and is_yellow_color(color):
            return 'yellow'  # Yellow re-translation task
        elif color and is_blue_color(color):
            return 'blue'    # Blue shortening task

        # ✨ Check sheet name for special task types
        sheet_lower = sheet_name.lower()
        if 'caps' in sheet_lower:
            return 'caps'    # ✨ CAPS post-processing task

        return 'normal'  # Normal translation task

    def _create_task(
        self,
        sheet_name: str,
        row_idx: int,
        source_col: int,
        target_col: int,
        source_text: str,
        source_lang: str,
        target_lang: str,
        task_num: int,
        task_type: str = 'normal',
        reference_en: str = ''  # ✨ EN参考翻译
    ) -> Dict[str, Any]:
        """Create a single task dictionary (optimized version)."""
        # Cache frequently used values
        text_len = len(source_text)
        now = datetime.now()

        # Fast cell reference calculation
        col_num = target_col + 1
        col_letter = ''
        while col_num > 0:
            col_num -= 1
            col_letter = chr(col_num % 26 + ord('A')) + col_letter
            col_num //= 26
        cell_ref = f"{col_letter}{row_idx + 2}"

        # Fast priority calculation based on task type
        if task_type == 'yellow':
            priority = 9
        elif task_type == 'blue':
            priority = 7
        elif task_type == 'caps':  # ✨ CAPS 任务优先级
            priority = 5
        else:  # normal
            priority = 6

        # Fast group_id determination
        sheet_lower = sheet_name.lower()
        if 'ui' in sheet_lower:
            group_id = 'GROUP_UI_001'
        elif 'dialog' in sheet_lower:
            group_id = 'GROUP_DIALOG_001'
        elif text_len <= 20:
            group_id = 'GROUP_SHORT_001'
        elif text_len <= 100:
            group_id = 'GROUP_MEDIUM_001'
        else:
            group_id = 'GROUP_LONG_001'

        # Extract context (optional, this is the slowest part)
        if self.extract_context and self.context_extractor:
            source_context = self.context_extractor.extract_context(
                self.excel_df, sheet_name, row_idx, source_col
            )
        else:
            source_context = ""

        # Build task dict directly (avoid intermediate variables)
        return {
            'task_id': f"TASK_{task_num:04d}",
            'batch_id': '',
            'group_id': group_id,
            'task_type': task_type,
            'source_lang': source_lang,
            'source_text': source_text,
            'source_context': source_context,
            'game_context': self.game_info.to_context_string() if self.game_info else "",
            'reference_en': reference_en,  # ✨ 英文参考
            'target_lang': target_lang,
            'excel_id': self.excel_df.excel_id,
            'sheet_name': sheet_name,
            'row_idx': row_idx,
            'col_idx': target_col,
            'cell_ref': cell_ref,
            'status': 'pending',
            'priority': priority,
            'result': '',
            'confidence': 0.0,
            'char_count': text_len,
            'created_at': now,
            'updated_at': now,
            'start_time': None,
            'end_time': None,
            'duration_ms': 0,
            'retry_count': 0,
            'error_message': '',
            'llm_model': '',
            'token_count': 0,
            'cost': 0.0,
            'reviewer_notes': '',
            'is_final': False
        }

    def _determine_group_id(self, sheet_name: str, source_text: str) -> str:
        """Determine group_id based on sheet and content."""
        sheet_lower = sheet_name.lower()

        # Sheet-based grouping
        if 'ui' in sheet_lower:
            return 'GROUP_UI_001'
        elif 'dialog' in sheet_lower:
            return 'GROUP_DIALOG_001'
        elif 'item' in sheet_lower:
            return 'GROUP_ITEM_001'
        elif 'skill' in sheet_lower:
            return 'GROUP_SKILL_001'
        elif 'quest' in sheet_lower:
            return 'GROUP_QUEST_001'

        # Content-based grouping
        if len(source_text) <= 20:
            return 'GROUP_SHORT_001'
        elif len(source_text) <= 100:
            return 'GROUP_MEDIUM_001'
        else:
            return 'GROUP_LONG_001'

    def _get_cell_reference(self, row_idx: int, col_idx: int) -> str:
        """Convert row/col indices to Excel cell reference (e.g., A1)."""
        # Convert column index to letter(s)
        col_letter = ''
        col_num = col_idx + 1
        while col_num > 0:
            col_num -= 1
            col_letter = chr(col_num % 26 + ord('A')) + col_letter
            col_num //= 26

        # Row is 1-indexed
        return f"{col_letter}{row_idx + 2}"  # +2 because row 0 is header, Excel is 1-indexed

    def _determine_priority(self, sheet_name: str, source_text: str, task_type: str = 'normal') -> int:
        """
        Determine task priority (1-10, higher is more important).

        Priority order:
        1. Yellow tasks (re-translation) - highest priority (9-10)
        2. Blue tasks (shortening) - high priority (7-8)
        3. Normal tasks (new translation) - normal priority (5-6)

        Within each type, UI and short texts get +1 priority.
        """
        # Base priority by task type
        if task_type == 'yellow':
            base_priority = 9  # Yellow re-translation is highest priority
        elif task_type == 'blue':
            base_priority = 7  # Blue shortening is high priority
        elif task_type == 'caps':  # ✨ CAPS 任务优先级
            base_priority = 5  # CAPS post-processing task
        else:  # normal
            base_priority = 6  # Normal translation is standard priority

        # Additional priority adjustments based on content
        sheet_lower = sheet_name.lower()

        # UI text gets +1 priority within its type
        if 'ui' in sheet_lower:
            base_priority = min(10, base_priority + 1)

        # Short text (<=20 chars) gets slight boost within normal tasks
        elif task_type == 'normal' and len(source_text) <= 20:
            base_priority = min(10, base_priority + 1)

        return base_priority