"""Excel analyzer service - analyzes Excel structure, language, and format."""

import pandas as pd
import re
import logging
from typing import Dict, Any, List
from collections import Counter

from models.excel_dataframe import ExcelDataFrame
from models.analysis_result import AnalysisResult
from utils.color_detector import is_yellow_color, is_blue_color

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Detect source and target languages in Excel sheets."""

    # Language patterns
    PATTERNS = {
        'CH': re.compile(r'[\u4e00-\u9fff]+'),  # Chinese characters
        'EN': re.compile(r'[a-zA-Z]{2,}'),      # English words
        'PT': re.compile(r'\b(de|da|do|na|em|com|para|por|que|não|são|está)\b', re.I),
        'TH': re.compile(r'[\u0e00-\u0e7f]+'),  # Thai characters
        'VN': re.compile(r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]', re.I),
        'TR': re.compile(r'[çğıöşüÇĞİÖŞÜ]|(\b(ve|ile|için|bir|bu)\b)', re.I),
        'IND': re.compile(r'\b(dan|yang|di|ke|dari|untuk|dengan)\b', re.I),
        'ES': re.compile(r'\b(el|la|de|que|y|en|un|por)\b|[áéíóúñ¿¡]', re.I),
    }

    # Language column indicators
    COLUMN_INDICATORS = {
        'source': ['源文', 'source', 'original', 'chinese', 'ch', 'cn', 'english', 'en'],
        'CH': ['chinese', 'ch', 'cn', '中文'],
        'EN': ['english', 'en', '英文'],
        'PT': ['portuguese', 'pt', 'brazil', 'br'],
        'TH': ['thai', 'th', '泰'],
        'VN': ['vietnamese', 'vn', 'vietnam'],
        'TR': ['turkish', 'tr', '土耳其'],
        'IND': ['indonesian', 'ind', 'id', '印尼'],
        'ES': ['spanish', 'es', '西班牙']
    }

    @classmethod
    def detect_language(cls, text: str) -> str:
        """Detect the primary language of a text."""
        if not text or not isinstance(text, str):
            return 'UNKNOWN'

        counts = {}
        for lang, pattern in cls.PATTERNS.items():
            matches = pattern.findall(text)
            counts[lang] = sum(len(match) if isinstance(match, str) else len(match[0]) for match in matches)

        if counts:
            return max(counts.items(), key=lambda x: x[1])[0] if max(counts.values()) > 0 else 'UNKNOWN'
        return 'UNKNOWN'

    @classmethod
    def identify_language_columns(cls, df: pd.DataFrame) -> Dict[str, List[int]]:
        """Identify source and target language columns."""
        result = {
            'source_columns': [],
            'CH_columns': [], 'EN_columns': [],
            'PT_columns': [], 'TH_columns': [],
            'VN_columns': [], 'TR_columns': [],
            'IND_columns': [], 'ES_columns': []
        }

        for col_idx, col_name in enumerate(df.columns):
            col_name_lower = str(col_name).lower()

            # Check source indicators
            if any(indicator in col_name_lower for indicator in cls.COLUMN_INDICATORS['source']):
                result['source_columns'].append(col_idx)

            # Check all language indicators
            for lang in ['CH', 'EN', 'PT', 'TH', 'VN', 'TR', 'IND', 'ES']:
                if any(indicator in col_name_lower for indicator in cls.COLUMN_INDICATORS[lang]):
                    result[f'{lang}_columns'].append(col_idx)

        return result

    @classmethod
    def analyze_sheet(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze a sheet for language information."""
        language_columns = cls.identify_language_columns(df)

        source_langs = set()
        if language_columns['CH_columns']:
            source_langs.add('CH')
        if language_columns['EN_columns']:
            source_langs.add('EN')

        target_langs = []
        for lang in ['PT', 'TH', 'VN', 'TR', 'IND', 'ES']:
            if language_columns[f'{lang}_columns']:
                target_langs.append(lang)

        return {
            'source_languages': list(source_langs),
            'target_languages': target_langs,
            'language_columns': language_columns,
            'has_translation_pairs': len(source_langs) > 0 and len(target_langs) > 0,
            'confidence': 0.95 if source_langs and target_langs else 0.5
        }


class ExcelAnalyzer:
    """Analyze Excel files for structure, language, and format."""

    def __init__(self):
        self.language_detector = LanguageDetector()

    def analyze(self, excel_df: ExcelDataFrame, options: Dict[str, Any] = None) -> AnalysisResult:
        """
        Perform comprehensive Excel analysis.

        Args:
            excel_df: ExcelDataFrame to analyze
            options: Analysis options (detect_language, detect_formats, analyze_colors)

        Returns:
            AnalysisResult containing all analysis data
        """
        options = options or {}
        detect_language = options.get('detect_language', True)
        detect_formats = options.get('detect_formats', True)
        analyze_colors = options.get('analyze_colors', True)

        logger.info(f"Starting Excel analysis: {excel_df.filename}")

        analysis = AnalysisResult()

        # File info
        analysis.file_info = self._analyze_file_info(excel_df)

        # Language detection
        if detect_language:
            analysis.language_detection = self._analyze_languages(excel_df)

        # Statistics
        analysis.statistics = self._analyze_statistics(excel_df, analyze_colors)

        # Format analysis
        if detect_formats:
            analysis.format_analysis = self._analyze_formats(excel_df, analyze_colors)

        logger.info(f"Analysis complete: {analysis.statistics.get('estimated_tasks', 0)} tasks estimated")
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

    def _analyze_statistics(self, excel_df: ExcelDataFrame, analyze_colors: bool = True) -> Dict[str, Any]:
        """Analyze statistics for task estimation."""
        stats = excel_df.get_statistics()

        # Three types of tasks to count
        normal_tasks = 0
        yellow_tasks = 0
        blue_tasks = 0

        char_distribution = {'min': float('inf'), 'max': 0, 'total': 0, 'count': 0}

        for sheet_name in excel_df.get_sheet_names():
            df = excel_df.get_sheet(sheet_name)
            columns = list(df.columns)

            # Identify source and target columns
            source_cols = []
            target_cols = []

            for idx, col in enumerate(columns):
                col_upper = str(col).upper()
                if col_upper in ['CH', 'CN', '中文', 'EN', 'ENGLISH', '英文']:
                    source_cols.append(idx)
                elif col_upper in ['TR', 'TH', 'PT', 'VN', 'VI', 'ES', 'IND', 'ID']:
                    target_cols.append(idx)

            # Count normal translation tasks
            for row_idx in range(len(df)):
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

            # Count yellow and blue tasks if color analysis is enabled
            if analyze_colors:
                for row_idx in range(len(df)):
                    for col_idx in range(len(columns)):
                        cell_value = df.iloc[row_idx, col_idx]
                        if pd.notna(cell_value) and isinstance(cell_value, str) and len(cell_value.strip()) > 0:
                            cell_color = excel_df.get_cell_color(sheet_name, row_idx, col_idx)

                            if cell_color and is_yellow_color(cell_color):
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
                                blue_tasks += 1
                                text = str(cell_value).strip()
                                char_len = len(text)
                                char_distribution['min'] = min(char_distribution['min'], char_len)
                                char_distribution['max'] = max(char_distribution['max'], char_len)
                                char_distribution['total'] += char_len
                                char_distribution['count'] += 1

        estimated_tasks = normal_tasks + yellow_tasks + blue_tasks

        if char_distribution['count'] > 0:
            char_distribution['avg'] = float(char_distribution['total'] / char_distribution['count'])
        else:
            char_distribution['min'] = 0
            char_distribution['avg'] = 0.0

        return {
            **stats,
            'estimated_tasks': int(estimated_tasks),
            'task_breakdown': {
                'normal_tasks': int(normal_tasks),
                'yellow_tasks': int(yellow_tasks),
                'blue_tasks': int(blue_tasks)
            },
            'char_distribution': {
                'min': int(char_distribution['min']) if char_distribution['min'] != float('inf') else 0,
                'max': int(char_distribution['max']),
                'total': int(char_distribution['total']),
                'count': int(char_distribution['count']),
                'avg': float(char_distribution['avg'])
            }
        }

    def _analyze_formats(self, excel_df: ExcelDataFrame, analyze_colors: bool = True) -> Dict[str, Any]:
        """Analyze format information (colors, comments, etc.)."""
        colored_cells = 0
        color_distribution = Counter()
        cells_with_comments = 0

        if analyze_colors:
            for sheet_name in excel_df.get_sheet_names():
                for (row, col), color in excel_df.color_map.get(sheet_name, {}).items():
                    colored_cells += 1
                    color_type = 'other'
                    if is_yellow_color(color):
                        color_type = 'yellow'
                    elif is_blue_color(color):
                        color_type = 'blue'
                    color_distribution[color_type] += 1

                cells_with_comments += len(excel_df.comment_map.get(sheet_name, {}))

        return {
            'colored_cells': colored_cells,
            'color_distribution': dict(color_distribution),
            'cells_with_comments': cells_with_comments
        }


# Global analyzer instance
excel_analyzer = ExcelAnalyzer()
