"""Task splitting service - core logic for task generation - DataFrame Pipeline Architecture.

核心改动：
- 从 DataFrame 的 color_* 列读取颜色信息
- 不再使用 excel_df.color_map 和 excel_df.get_cell_color()
- 添加 _get_cell_color() 辅助方法直接从 DataFrame 读取
"""

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

    def __init__(self, excel_df: ExcelDataFrame, game_info: GameInfo = None, extract_context: bool = True, context_options: Dict[str, bool] = None, max_chars_per_batch: int = None, enabled_rules: List[str] = None):
        """
        Initialize task splitter.

        Args:
            excel_df: Excel data structure (with translations if from parent session)
            game_info: Game information for context
            extract_context: Whether to extract row context (slower but provides more info)
            context_options: Dict specifying which context types to extract (only applies when extract_context=True)
            max_chars_per_batch: Custom batch size (None = use config default)
            enabled_rules: List of enabled rule names (e.g., ['empty', 'yellow', 'blue'])
                          If None, defaults to ['empty', 'yellow', 'blue'] (translation rules)
        """
        self.excel_df = excel_df
        self.game_info = game_info
        self.extract_context = extract_context
        self.context_extractor = ContextExtractor(game_info, context_options) if extract_context else None
        self.batch_allocator = BatchAllocator(max_chars_per_batch)
        self.language_detector = LanguageDetector()
        self.task_manager = TaskDataFrameManager()

        # Store enabled rules
        self.enabled_rules = enabled_rules if enabled_rules is not None else ['empty', 'yellow', 'blue']

    def _get_cell_color(self, df: pd.DataFrame, row_idx: int, col_idx: int) -> Optional[str]:
        """
        Helper method to get cell color from DataFrame.

        Args:
            df: DataFrame containing the data
            row_idx: Row index
            col_idx: Column index

        Returns:
            Color string (e.g., '#FFFFFF00') or None
        """
        if col_idx >= len(df.columns):
            return None

        # Get the column name from index
        col_name = df.columns[col_idx]

        # Skip if this is already a color or comment column
        if col_name.startswith('color_') or col_name.startswith('comment_'):
            return None

        # Check if color column exists
        color_col_name = f'color_{col_name}'
        if color_col_name not in df.columns:
            return None

        # Get color value
        try:
            color = df.at[row_idx, color_col_name]
            if pd.notna(color):
                return str(color)
        except (KeyError, IndexError):
            pass

        return None

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

        # Get data columns only (exclude color_* and comment_*)
        data_cols = self.excel_df.get_data_columns(sheet_name)

        # Check for explicit language columns by name
        column_names_upper = [str(col).upper() for col in data_cols]
        has_explicit_columns = False

        # Map column names to indices (within data columns only)
        col_mapping = {}  # Maps language code -> actual DataFrame column index
        for data_idx, col in enumerate(column_names_upper):
            # Get actual DataFrame column index
            actual_col_idx = df.columns.get_loc(data_cols[data_idx])

            if col in ['CH', 'CN', '中文']:
                col_mapping['CH'] = actual_col_idx
                has_explicit_columns = True
            elif col in ['EN', 'ENGLISH', '英文']:
                col_mapping['EN'] = actual_col_idx
                has_explicit_columns = True
            elif col in ['TH', 'THAI', '泰语', '泰文']:
                col_mapping['TH'] = actual_col_idx
                has_explicit_columns = True
            elif col in ['PT', 'PT-BR', 'PORTUGUESE', '葡萄牙语']:
                col_mapping['PT'] = actual_col_idx
                has_explicit_columns = True
            elif col in ['VN', 'VI', 'VIETNAMESE', '越南语']:
                col_mapping['VN'] = actual_col_idx
                has_explicit_columns = True
            elif col in ['TR', 'TURKISH', '土耳其语', '土耳其文']:
                col_mapping['TR'] = actual_col_idx
                has_explicit_columns = True
            elif col in ['IND', 'ID', 'INDONESIAN', '印尼语', '印度尼西亚语']:
                col_mapping['IND'] = actual_col_idx
                has_explicit_columns = True
            elif col in ['ES', 'SPANISH', '西班牙语', '西语']:
                col_mapping['ES'] = actual_col_idx
                has_explicit_columns = True
            elif col in ['FR', 'FRENCH', '法语', '法文']:
                col_mapping['FR'] = actual_col_idx
                has_explicit_columns = True
            elif col in ['DE', 'GERMAN', '德语', '德文']:
                col_mapping['DE'] = actual_col_idx
                has_explicit_columns = True
            elif col in ['IT', 'ITALIAN', '意大利语', '意语']:
                col_mapping['IT'] = actual_col_idx
                has_explicit_columns = True
            elif col in ['JA', 'JP', 'JAPANESE', '日语', '日文']:
                col_mapping['JA'] = actual_col_idx
                has_explicit_columns = True
            elif col in ['KR', 'KO', 'KOREAN', '韩语', '韩文']:
                col_mapping['KR'] = actual_col_idx
                has_explicit_columns = True
            elif col in ['RU', 'RUSSIAN', '俄语', '俄文']:
                col_mapping['RU'] = actual_col_idx
                has_explicit_columns = True
            elif col in ['TW', '繁体', '繁中', 'TAIWAN', 'TCHINESE', '繁體中文', '繁體']:
                col_mapping['TW'] = actual_col_idx
                has_explicit_columns = True

        # If we have explicit columns, use them directly
        if has_explicit_columns:
            # ⚠️ CAPS Sheet特殊处理：如果是CAPS sheet，不需要source列，直接跳到CAPS逻辑
            is_caps_sheet = 'CAPS' in sheet_name.upper() and 'caps' in self.enabled_rules

            if not is_caps_sheet:
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
                        # 对于非CAPS sheet，找不到source列就跳过
                        # 但对于CAPS sheet，仍然继续执行CAPS逻辑
                        pass

            # Process each row with explicit columns (skip for CAPS-only sheets)
            if not is_caps_sheet:
                for row_idx in range(len(df)):
                    # Get source text
                    source_text = df.iloc[row_idx, source_col_idx]
                    if pd.isna(source_text) or not str(source_text).strip():
                        continue

                    source_text = str(source_text)

                    # Check source cell color (important for yellow re-translation)
                    source_cell_color = self._get_cell_color(df, row_idx, source_col_idx)
                    source_is_yellow = source_cell_color and is_yellow_color(source_cell_color)
                    source_is_blue = source_cell_color and is_blue_color(source_cell_color)

                    # ✨ Check if EN column is yellow or blue
                    en_reference = None
                    en_is_yellow = False
                    en_is_blue = False  # ✨ EN需要缩短
                    en_as_source = False  # ✨ EN作为主源文本
                    en_col_idx = col_mapping.get('EN')

                    if en_col_idx is not None:
                        # Check if EN cell is yellow or blue
                        en_cell_color = self._get_cell_color(df, row_idx, en_col_idx)
                        if en_cell_color and is_yellow_color(en_cell_color):
                            en_is_yellow = True
                            # EN is yellow → use as main source (not just reference)
                            en_value = df.iloc[row_idx, en_col_idx]
                            if pd.notna(en_value) and str(en_value).strip():
                                en_reference = str(en_value)

                                # ✅ If only EN is yellow (CH not yellow), EN becomes main source
                                if not source_is_yellow:
                                    en_as_source = True

                        elif en_cell_color and is_blue_color(en_cell_color):
                            # ✨ EN is blue → needs shortening, mark for blue task creation
                            en_is_blue = True
                            en_value = df.iloc[row_idx, en_col_idx]
                            if pd.notna(en_value) and str(en_value).strip():
                                en_reference = str(en_value)

                    # If source cell has blue color, create a blue task for shortening (only if blue rule enabled)
                    if source_is_blue and 'blue' in self.enabled_rules:
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

                    # ✨ Blue 规则：如果 EN 单元格是蓝色，无条件创建自我缩短任务（不受 target_langs 限制）
                    # ⚠️ 但如果 EN 已经是源语言，则跳过（避免重复创建）
                    if en_is_blue and en_reference and 'blue' in self.enabled_rules:
                        # Skip if EN is already the source language (already handled above)
                        if actual_source_lang != 'EN' or source_col_idx != en_col_idx:
                            task = self._create_task(
                                sheet_name,
                                row_idx,
                                en_col_idx,
                                en_col_idx,  # Target is the same as source (shorten itself)
                                en_reference,
                                'EN',
                                'EN',  # Target lang is same as source lang
                                start_counter + len(tasks),
                                'blue'
                            )
                            tasks.append(task)

                    # Check each target language
                    for target_lang in target_langs:
                        # ✨ Skip EN if it's yellow (already finalized) or blue (will be shortened)
                        if target_lang == 'EN' and (en_is_yellow or en_is_blue):
                            continue  # EN is yellow/blue = special handling, skip normal translation

                        if target_lang in col_mapping:
                            target_col = col_mapping[target_lang]

                            # Get target cell value
                            target_value = df.iloc[row_idx, target_col]

                            # Check target cell color
                            target_color = self._get_cell_color(df, row_idx, target_col)

                            # Determine if needs translation and task type
                            needs_translation = False
                            task_type = 'normal'

                            # ✅ Priority 1: Target cell is yellow → Skip (already modified, final version)
                            if target_color and is_yellow_color(target_color):
                                needs_translation = False
                                continue  # Yellow target = already finalized, skip translation

                            # ✅ Priority 2: Target cell is blue → Shortening task (only if blue rule enabled)
                            if target_color and is_blue_color(target_color) and 'blue' in self.enabled_rules:
                                needs_translation = True
                                task_type = 'blue'

                            # ✅ Priority 3: Source or EN is yellow → Force re-translate (only if yellow rule enabled)
                            elif (source_is_yellow or en_is_yellow) and 'yellow' in self.enabled_rules:
                                needs_translation = True
                                task_type = 'yellow'  # Force re-translate all right columns

                            # Priority 4: Empty target cell needs normal translation (only if empty rule enabled)
                            elif pd.isna(target_value) or str(target_value).strip() == '':
                                if source_text and source_text.strip() and 'empty' in self.enabled_rules:
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

            # ✅ CAPS task creation - OUTSIDE row loop, runs ONCE per sheet
            # CAPS任务：强制处理所有列（除了索引列），不受 target_langs 限制
            if 'CAPS' in sheet_name.upper() and 'caps' in self.enabled_rules:
                # 获取所有数据列（排除 color_* 和 comment_*）
                all_data_cols = self.excel_df.get_data_columns(sheet_name)

                # 处理每一列（除了第一列索引）
                for data_col_name in all_data_cols[1:]:  # 跳过第一列（索引列）
                    # 获取实际的 DataFrame 列索引
                    actual_col_idx = df.columns.get_loc(data_col_name)

                    # 检查这个列名是否是索引列（双重保护）
                    col_name_upper = str(data_col_name).upper()
                    if col_name_upper in ['KEY', 'INDEX', 'ID']:
                        continue  # 跳过索引列

                    # 扫描这一列的所有行
                    for caps_row_idx in range(len(df)):
                        cell_value = df.iloc[caps_row_idx, actual_col_idx]

                        # 如果单元格有内容（可能是源语言或目标语言），创建CAPS任务
                        if pd.notna(cell_value) and str(cell_value).strip():
                            task = self._create_task(
                                sheet_name,
                                caps_row_idx,
                                actual_col_idx,  # source = target (transform in place)
                                actual_col_idx,
                                str(cell_value),
                                data_col_name,  # 使用列名作为语言标识
                                data_col_name,  # 使用列名作为语言标识
                                start_counter + len(tasks),
                                'caps'  # CAPS transformation task
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

                # Check if source cell itself has blue color (needs shortening) - only if blue rule enabled
                source_cell_color = self._get_cell_color(df, row_idx, source_col)
                if source_cell_color and is_blue_color(source_cell_color) and 'blue' in self.enabled_rules:
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
                            df, row_idx, target_col, source_text
                        )

                        if needs_translation:
                            # Determine task type based on TARGET cell color (not source)
                            task_type = self._determine_task_type(df, row_idx, target_col)

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
        df: pd.DataFrame,
        row_idx: int,
        col_idx: int,
        source_text: str
    ) -> bool:
        """Check if a cell needs translation (respects enabled_rules)."""
        if df is None:
            return False

        # Get current value
        current_value = df.iloc[row_idx, col_idx] if col_idx < len(df.columns) else None

        # Check cell color
        color = self._get_cell_color(df, row_idx, col_idx)

        # Yellow cells need translation (only if yellow rule enabled)
        if color and is_yellow_color(color) and 'yellow' in self.enabled_rules:
            return True

        # Blue cells need translation (only if blue rule enabled)
        if color and is_blue_color(color) and 'blue' in self.enabled_rules:
            return True

        # Empty cells need translation if source has content (only if empty rule enabled)
        if pd.isna(current_value) or str(current_value).strip() == '':
            return bool(source_text and source_text.strip() and 'empty' in self.enabled_rules)

        # If already has content and no color marking, skip
        return False

    def _determine_task_type(
        self,
        df: pd.DataFrame,
        row_idx: int,
        col_idx: int
    ) -> str:
        """Determine task type based on cell color."""
        color = self._get_cell_color(df, row_idx, col_idx)

        if color and is_yellow_color(color):
            return 'yellow'  # Yellow re-translation task
        elif color and is_blue_color(color):
            return 'blue'    # Blue shortening task
        else:
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
        else:
            priority = 5

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

        # Get DataFrame for col_name extraction
        df = self.excel_df.get_sheet(sheet_name)
        col_name = df.columns[target_col] if target_col < len(df.columns) else str(target_col)

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
            'col_name': col_name,  # ✅ Add col_name for new architecture
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
        else:  # normal
            base_priority = 5  # Normal translation is standard priority

        # Additional priority adjustments based on content
        sheet_lower = sheet_name.lower()

        # UI text gets +1 priority within its type
        if 'ui' in sheet_lower:
            base_priority = min(10, base_priority + 1)

        # Short text (<=20 chars) gets slight boost within normal tasks
        elif task_type == 'normal' and len(source_text) <= 20:
            base_priority = min(10, base_priority + 1)

        return base_priority
