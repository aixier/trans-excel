"""Language detection service."""

import re
import pandas as pd
from typing import List, Tuple, Dict, Any, Optional
from collections import Counter


class LanguageDetector:
    """Detect source and target languages in Excel sheets."""

    # Language patterns
    PATTERNS = {
        'CH': re.compile(r'[\u4e00-\u9fff]+'),  # Chinese characters
        'EN': re.compile(r'[a-zA-Z]{2,}'),      # English words
        'PT': re.compile(r'\b(de|da|do|na|em|com|para|por|que|não|são|está)\b', re.I),  # Portuguese
        'TH': re.compile(r'[\u0e00-\u0e7f]+'),  # Thai characters
        'VN': re.compile(r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]', re.I),  # Vietnamese
        'BR': re.compile(r'\b(de|da|do|na|em|com|para|por|que|não|são|está)\b', re.I),  # Brazilian Portuguese (same as PT)
    }

    # Language column indicators
    COLUMN_INDICATORS = {
        'source': ['源文', 'source', 'original', '原文', 'chinese', 'ch', 'cn', 'english', 'en'],
        'PT': ['portuguese', 'pt', 'pt-br', 'brazil', 'br', '葡萄牙', '巴西'],
        'TH': ['thai', 'th', 'thailand', '泰', '泰语', '泰文'],
        'VN': ['vietnamese', 'vn', 'vietnam', '越南', '越南语']
    }

    @classmethod
    def detect_language(cls, text: str) -> str:
        """Detect the primary language of a text."""
        if not text or not isinstance(text, str):
            return 'UNKNOWN'

        # Count characters by language
        counts = {}
        for lang, pattern in cls.PATTERNS.items():
            matches = pattern.findall(text)
            counts[lang] = sum(len(match) for match in matches)

        # Return the language with most characters
        if counts:
            return max(counts.items(), key=lambda x: x[1])[0] if max(counts.values()) > 0 else 'UNKNOWN'
        return 'UNKNOWN'

    @classmethod
    def detect_column_languages(cls, df: pd.DataFrame) -> Dict[int, str]:
        """Detect language for each column based on content."""
        column_langs = {}

        for col_idx, col in enumerate(df.columns):
            # Sample non-empty values from column
            sample = df.iloc[:, col_idx].dropna().astype(str).head(20)

            if len(sample) == 0:
                column_langs[col_idx] = 'EMPTY'
                continue

            # Detect language for each sample
            lang_counts = Counter()
            for text in sample:
                lang = cls.detect_language(text)
                if lang != 'UNKNOWN':
                    lang_counts[lang] += 1

            # Get most common language
            if lang_counts:
                column_langs[col_idx] = lang_counts.most_common(1)[0][0]
            else:
                column_langs[col_idx] = 'UNKNOWN'

        return column_langs

    @classmethod
    def identify_language_columns(cls, df: pd.DataFrame) -> Dict[str, List[int]]:
        """Identify source and target language columns."""
        result = {
            'source_columns': [],
            'PT_columns': [],
            'TH_columns': [],
            'VN_columns': []
        }

        # First, check column names
        for col_idx, col_name in enumerate(df.columns):
            col_name_lower = str(col_name).lower()

            # Check source indicators
            if any(indicator in col_name_lower for indicator in cls.COLUMN_INDICATORS['source']):
                result['source_columns'].append(col_idx)

            # Check target language indicators
            for lang in ['PT', 'TH', 'VN']:
                if any(indicator in col_name_lower for indicator in cls.COLUMN_INDICATORS[lang]):
                    result[f'{lang}_columns'].append(col_idx)

        # If no columns identified by name, use content detection
        if not any(result.values()):
            column_langs = cls.detect_column_languages(df)

            for col_idx, lang in column_langs.items():
                if lang in ['CH', 'EN']:
                    result['source_columns'].append(col_idx)
                elif lang in ['PT', 'BR']:
                    result['PT_columns'].append(col_idx)
                elif lang == 'TH':
                    result['TH_columns'].append(col_idx)
                elif lang == 'VN':
                    result['VN_columns'].append(col_idx)

        return result

    @classmethod
    def analyze_sheet(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze a sheet for language information."""
        language_columns = cls.identify_language_columns(df)

        # Determine source languages
        source_langs = set()
        for col_idx in language_columns['source_columns']:
            sample = df.iloc[:, col_idx].dropna().astype(str).head(20)
            for text in sample:
                lang = cls.detect_language(text)
                if lang in ['CH', 'EN']:
                    source_langs.add(lang)

        # Determine available target languages
        target_langs = []
        if language_columns['PT_columns']:
            target_langs.append('PT')
        if language_columns['TH_columns']:
            target_langs.append('TH')
        if language_columns['VN_columns']:
            target_langs.append('VN')

        return {
            'source_languages': list(source_langs),
            'target_languages': target_langs,
            'language_columns': language_columns,
            'has_translation_pairs': len(source_langs) > 0 and len(target_langs) > 0
        }