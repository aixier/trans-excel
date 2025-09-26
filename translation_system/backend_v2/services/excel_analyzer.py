"""Excel analyzer service."""

import pandas as pd
from typing import Dict, Any, List
from models.excel_dataframe import ExcelDataFrame
from models.game_info import GameInfo
from services.language_detector import LanguageDetector


class ExcelAnalyzer:
    """Analyze Excel files for translation tasks."""

    def __init__(self):
        self.language_detector = LanguageDetector()

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
        return {
            'filename': excel_df.filename,
            'excel_id': excel_df.excel_id,
            'sheets': excel_df.get_sheet_names(),
            'sheet_count': len(excel_df.sheets),
            'total_rows': excel_df.total_rows,
            'total_cols': excel_df.total_cols
        }

    def _analyze_languages(self, excel_df: ExcelDataFrame) -> Dict[str, Any]:
        """Analyze language distribution."""
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

        return {
            'source_langs': list(all_source_langs),
            'target_langs': list(all_target_langs),
            'sheet_details': sheet_analyses
        }

    def _analyze_statistics(self, excel_df: ExcelDataFrame) -> Dict[str, Any]:
        """Analyze statistics for task estimation."""
        stats = excel_df.get_statistics()

        # Estimate translation tasks
        estimated_tasks = 0
        char_distribution = {'min': float('inf'), 'max': 0, 'total': 0, 'count': 0}

        for sheet_name in excel_df.get_sheet_names():
            df = excel_df.get_sheet(sheet_name)

            # Count non-empty cells that might need translation
            for row_idx in range(len(df)):
                for col_idx in range(len(df.columns)):
                    value = df.iloc[row_idx, col_idx]

                    if pd.notna(value) and isinstance(value, str) and len(value.strip()) > 0:
                        # Check if cell has color (potential translation task)
                        color = excel_df.get_cell_color(sheet_name, row_idx, col_idx)

                        # Yellow (#FFFF00) or Blue (#0000FF) indicates translation need
                        if color in ['#FFFF00', '#FFFFFF00', '#0000FF', '#FF0000FF']:
                            estimated_tasks += 1
                            char_len = len(value)
                            char_distribution['min'] = min(char_distribution['min'], char_len)
                            char_distribution['max'] = max(char_distribution['max'], char_len)
                            char_distribution['total'] += char_len
                            char_distribution['count'] += 1
                        # Or if no color info, estimate based on content
                        elif not color:
                            lang = self.language_detector.detect_language(value)
                            if lang in ['CH', 'EN']:
                                estimated_tasks += 1
                                char_len = len(value)
                                char_distribution['min'] = min(char_distribution['min'], char_len)
                                char_distribution['max'] = max(char_distribution['max'], char_len)
                                char_distribution['total'] += char_len
                                char_distribution['count'] += 1

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
                    color = excel_df.get_cell_color(sheet_name, row_idx, col_idx)

                    # Determine if needs translation
                    needs_translation = False
                    task_type = 'normal'

                    if color == '#FFFF00' or color == '#FFFFFF00':  # Yellow
                        needs_translation = True
                        task_type = 'yellow'
                    elif color == '#0000FF' or color == '#FF0000FF':  # Blue
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
                            'comment': excel_df.get_cell_comment(sheet_name, row_idx, col_idx)
                        })

        return cells