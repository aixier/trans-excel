"""Excel analyzer service."""

import pandas as pd
from typing import Dict, Any, List
from models.excel_dataframe import ExcelDataFrame
from models.game_info import GameInfo
from services.language_detector import LanguageDetector
from services.language_metadata import LanguageMetadata
from utils.color_detector import is_yellow_color, is_blue_color


class ExcelAnalyzer:
    """Analyze Excel files for translation tasks."""

    def __init__(self):
        self.language_detector = LanguageDetector()

    def _get_cell_color(self, excel_df: ExcelDataFrame, sheet_name: str, row_idx: int, col_idx: int):
        """Helper to get cell color from DataFrame."""
        df = excel_df.get_sheet(sheet_name)
        if df is None or col_idx >= len(df.columns):
            return None
        col_name = df.columns[col_idx]
        if col_name.startswith('color_') or col_name.startswith('comment_'):
            return None
        color_col = f'color_{col_name}'
        if color_col in df.columns:
            color = df.at[row_idx, color_col]
            return color if pd.notna(color) else None
        return None

    def _get_cell_comment(self, excel_df: ExcelDataFrame, sheet_name: str, row_idx: int, col_idx: int):
        """Helper to get cell comment from DataFrame."""
        df = excel_df.get_sheet(sheet_name)
        if df is None or col_idx >= len(df.columns):
            return None
        col_name = df.columns[col_idx]
        if col_name.startswith('color_') or col_name.startswith('comment_'):
            return None
        comment_col = f'comment_{col_name}'
        if comment_col in df.columns:
            comment = df.at[row_idx, comment_col]
            return comment if pd.notna(comment) else None
        return None

    def analyze(self, excel_df: ExcelDataFrame, game_info: GameInfo = None) -> Dict[str, Any]:
        """Analyze Excel file and return comprehensive analysis."""
        analysis = {
            'file_info': self._analyze_file_info(excel_df),
            'language_detection': self._analyze_languages(excel_df),
            'statistics': self._analyze_statistics(excel_df),
            'game_context': game_info.to_dict() if game_info else {}
        }

        return analysis

    def _analyze_file_info(self, excel_df: ExcelDataFrame) -> Dict[str, Any]:
        """Analyze basic file information."""
        # Calculate total rows and columns dynamically
        total_rows = 0
        total_cols = 0
        for sheet_name in excel_df.get_sheet_names():
            df = excel_df.get_sheet(sheet_name)
            if df is not None:
                total_rows += len(df)
                # Only count data columns (not color_* and comment_*)
                data_cols = excel_df.get_data_columns(sheet_name)
                total_cols = max(total_cols, len(data_cols))

        return {
            'filename': excel_df.filename,
            'excel_id': excel_df.excel_id,
            'sheets': excel_df.get_sheet_names(),
            'sheet_count': len(excel_df.sheets),
            'total_rows': total_rows,
            'total_cols': total_cols
        }

    def _analyze_languages(self, excel_df: ExcelDataFrame) -> Dict[str, Any]:
        """Analyze language distribution with complete metadata."""
        all_source_langs = set()
        all_target_langs = set()
        sheet_analyses = []

        for sheet_name in excel_df.get_sheet_names():
            df = excel_df.get_sheet(sheet_name)
            sheet_analysis = self.language_detector.analyze_sheet(df)

            all_source_langs.update(sheet_analysis['source_languages'])
            all_target_langs.update(sheet_analysis['target_languages'])

            sheet_analyses.append({
                'sheet_name': sheet_name,
                **sheet_analysis
            })

        # 丰富检测到的语言信息
        detected_source_langs = LanguageMetadata.enrich_language_list(list(all_source_langs))
        detected_target_langs = LanguageMetadata.enrich_language_list(list(all_target_langs))

        # 获取所有可用的语言选项
        available_source_langs = LanguageMetadata.get_available_source_languages()
        available_target_langs = LanguageMetadata.get_available_target_languages()

        # 智能推荐配置
        suggested_source = list(all_source_langs)[0] if all_source_langs else None
        suggested_targets = list(all_target_langs) if all_target_langs else []

        return {
            # 检测到的语言（带完整元数据）
            'detected': {
                'source_languages': detected_source_langs,
                'target_languages': detected_target_langs
            },

            # 系统支持的所有语言（用于选择器）
            'available': {
                'source_languages': [
                    {'code': 'auto', 'name': '自动检测', 'abbr': 'AUTO'},
                    *available_source_langs
                ],
                'target_languages': available_target_langs
            },

            # 智能推荐配置
            'suggested_config': {
                'source_lang': suggested_source,
                'target_langs': suggested_targets,
                'confidence': 0.95 if suggested_source and suggested_targets else 0.0
            },

            # 保留原始数据（兼容性）
            'source_langs': list(all_source_langs),
            'target_langs': list(all_target_langs),
            'sheet_details': sheet_analyses
        }

    def _analyze_statistics(self, excel_df: ExcelDataFrame) -> Dict[str, Any]:
        """Analyze statistics for task estimation."""
        stats = excel_df.get_statistics()

        # Three types of tasks to count
        normal_tasks = 0  # Normal translation tasks
        yellow_tasks = 0  # Yellow re-translation tasks
        blue_tasks = 0    # Blue shortening tasks
        caps_tasks = 0    # CAPS uppercase tasks

        char_distribution = {'min': float('inf'), 'max': 0, 'total': 0, 'count': 0}

        for sheet_name in excel_df.get_sheet_names():
            df = excel_df.get_sheet(sheet_name)
            columns = list(df.columns)

            # Identify source and target columns
            source_cols = []
            target_cols = []

            for idx, col in enumerate(columns):
                col_upper = str(col).upper()
                # Source columns
                if col_upper in ['CH', 'CN', '中文', 'EN', 'ENGLISH', '英文']:
                    source_cols.append(idx)
                # Target columns
                elif col_upper in ['TR', 'TH', 'PT', 'VN', 'VI', 'ES', 'IND', 'ID', 'TURKISH', '土耳其语']:
                    target_cols.append(idx)

            # CAPS sheets: each non-source column produces an uppercase task
            if 'caps' in sheet_name.lower():
                if source_cols:
                    primary_source = source_cols[0]
                else:
                    primary_source = None

                caps_cols = [idx for idx in range(len(columns)) if idx != primary_source]
                caps_tasks += len(caps_cols) * len(df)

            # Count all three types of tasks
            # Type 1: Normal translation tasks (all rows with source text and empty targets)
            for row_idx in range(len(df)):
                # Check if source columns have content
                has_source = False
                source_text = None
                for source_col_idx in source_cols:
                    if source_col_idx < len(columns):
                        source_value = df.iloc[row_idx, source_col_idx]
                        if pd.notna(source_value) and isinstance(source_value, str) and len(source_value.strip()) > 0:
                            has_source = True
                            source_text = str(source_value).strip()
                            break

                if has_source and source_text:
                    # Count empty target columns
                    for target_col_idx in target_cols:
                        if target_col_idx < len(columns):
                            target_value = df.iloc[row_idx, target_col_idx]
                            if pd.isna(target_value) or str(target_value).strip() == '':
                                normal_tasks += 1
                                char_len = len(source_text)
                                char_distribution['min'] = min(char_distribution['min'], char_len)
                                char_distribution['max'] = max(char_distribution['max'], char_len)
                                char_distribution['total'] += char_len
                                char_distribution['count'] += 1

            # Type 2 & 3: Yellow and Blue cells
            for row_idx in range(len(df)):
                for col_idx in range(len(columns)):
                    cell_value = df.iloc[row_idx, col_idx]
                    if pd.notna(cell_value) and isinstance(cell_value, str) and len(cell_value.strip()) > 0:
                        cell_color = self._get_cell_color(excel_df, sheet_name, row_idx, col_idx)

                        if cell_color and is_yellow_color(cell_color):
                            # Type 2: Yellow cells (re-translate to all following columns)
                            cols_after = len(columns) - col_idx - 1
                            if cols_after > 0:
                                yellow_tasks += cols_after
                                text = str(cell_value).strip()
                                char_len = len(text)
                                for _ in range(cols_after):
                                    char_distribution['min'] = min(char_distribution['min'], char_len)
                                    char_distribution['max'] = max(char_distribution['max'], char_len)
                                    char_distribution['total'] += char_len
                                    char_distribution['count'] += 1

                        elif cell_color and is_blue_color(cell_color):
                            # Type 3: Blue cells (shortening to self)
                            blue_tasks += 1
                            text = str(cell_value).strip()
                            char_len = len(text)
                            char_distribution['min'] = min(char_distribution['min'], char_len)
                            char_distribution['max'] = max(char_distribution['max'], char_len)
                            char_distribution['total'] += char_len
                            char_distribution['count'] += 1

        # Total estimated tasks
        estimated_tasks = normal_tasks + yellow_tasks + blue_tasks + caps_tasks

        # Calculate average
        if char_distribution['count'] > 0:
            char_distribution['avg'] = float(char_distribution['total'] / char_distribution['count'])
        else:
            char_distribution['min'] = 0
            char_distribution['avg'] = 0.0

        # Convert all numeric values to Python types (not numpy)
        return {
            **stats,
            'estimated_tasks': int(estimated_tasks),
            'task_breakdown': {
                'normal_tasks': int(normal_tasks),
                'yellow_tasks': int(yellow_tasks),
                'blue_tasks': int(blue_tasks),
                'caps_tasks': int(caps_tasks)
            },
            'char_distribution': {
                'min': int(char_distribution['min']) if char_distribution['min'] != float('inf') else 0,
                'max': int(char_distribution['max']),
                'total': int(char_distribution['total']),
                'count': int(char_distribution['count']),
                'avg': float(char_distribution['avg'])
            }
        }

    def identify_translation_cells(self, excel_df: ExcelDataFrame, sheet_name: str) -> List[Dict[str, Any]]:
        """Identify cells that need translation in a specific sheet."""
        cells = []
        df = excel_df.get_sheet(sheet_name)

        if df is None:
            return cells

        for row_idx in range(len(df)):
            for col_idx in range(len(df.columns)):
                value = df.iloc[row_idx, col_idx]

                if pd.notna(value) and isinstance(value, str) and len(value.strip()) > 0:
                    # Check color
                    color = self._get_cell_color(excel_df, sheet_name, row_idx, col_idx)

                    # Determine if needs translation
                    needs_translation = False
                    task_type = 'normal'

                    if is_yellow_color(color):
                        needs_translation = True
                        task_type = 'yellow'
                    elif is_blue_color(color):
                        needs_translation = True
                        task_type = 'blue'
                    elif pd.isna(value) or value == '':  # Empty but might need translation
                        # Check if corresponding source has content
                        pass  # Will be handled in task splitter

                    if needs_translation:
                        cells.append({
                            'row': row_idx,
                            'col': col_idx,
                            'value': value,
                            'color': color,
                            'type': task_type,
                            'comment': self._get_cell_comment(excel_df, sheet_name, row_idx, col_idx)
                        })

        return cells
