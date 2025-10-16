"""Language detection service."""

import re
import pandas as pd
from typing import List, Tuple, Dict, Any, Optional
from collections import Counter


class LanguageDetector:
    """Detect source and target languages in Excel sheets."""

    # Language patterns
    PATTERNS = {
        'CH': re.compile(r'[\u4e00-\u9fff]+'),  # Chinese characters (Simplified)
        'TW': re.compile(r'[\u4e00-\u9fff]+'),  # Traditional Chinese (same Unicode range)
        'EN': re.compile(r'[a-zA-Z]{2,}'),      # English words
        'JP': re.compile(r'[\u3040-\u309f\u30a0-\u30ff]+'),  # Japanese (Hiragana + Katakana)
        'KR': re.compile(r'[\uac00-\ud7af\u1100-\u11ff]+'),  # Korean (Hangul)
        'PT': re.compile(r'\b(de|da|do|na|em|com|para|por|que|não|são|está)\b', re.I),  # Portuguese
        'BR': re.compile(r'\b(de|da|do|na|em|com|para|por|que|não|são|está)\b', re.I),  # Brazilian Portuguese (same as PT)
        'ES': re.compile(r'\b(el|la|de|que|y|en|un|por|con|no|para|es|se|los|las)\b|[áéíóúñ¿¡]', re.I),  # Spanish
        'FR': re.compile(r'\b(le|la|de|et|est|un|pour|dans|que|ce|il|elle|on|ne|pas|plus)\b|[àâæçéèêëïîôùûü]', re.I),  # French
        'DE': re.compile(r'\b(der|die|das|und|ist|ein|für|in|zu|den|dem|mit|nicht|von|auf)\b|[äöüß]', re.I),  # German
        'IT': re.compile(r'\b(il|la|di|e|è|un|per|in|che|del|con|non|da|sono)\b|[àèéìòù]', re.I),  # Italian
        'RU': re.compile(r'[\u0400-\u04ff]+'),  # Russian (Cyrillic)
        'PL': re.compile(r'\b(i|w|z|na|do|się|jest|to|nie|za|o|by|co|jak|po)\b|[ąćęłńóśźż]', re.I),  # Polish
        'NL': re.compile(r'\b(de|het|een|in|van|is|op|te|dat|aan|met|voor|door|er|om)\b|[ëïöü]', re.I),  # Dutch
        'TH': re.compile(r'[\u0e00-\u0e7f]+'),  # Thai characters
        'VN': re.compile(r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]', re.I),  # Vietnamese
        'IND': re.compile(r'\b(dan|yang|di|ke|dari|untuk|dengan|ini|itu|adalah|pada|tidak|kami|saya)\b', re.I),  # Indonesian
        'MS': re.compile(r'\b(dan|yang|di|ke|untuk|dengan|ini|itu|adalah|pada|tidak|kami|saya|yang)\b', re.I),  # Malay (similar to Indonesian)
        'TR': re.compile(r'[çğıöşüÇĞİÖŞÜ]|(\b(ve|ile|için|bir|bu|şu|o|ben|sen|biz|siz|onlar)\b)', re.I),  # Turkish
        'AR': re.compile(r'[\u0600-\u06ff\u0750-\u077f]+'),  # Arabic
        'HI': re.compile(r'[\u0900-\u097f]+'),  # Hindi (Devanagari)
    }

    # Language column indicators (including variations with colons)
    COLUMN_INDICATORS = {
        'source': ['源文', 'source', 'original', '原文', 'chinese', ':ch:', 'ch', 'cn', ':cn:', 'english', ':en:', 'en'],
        'CH': ['chinese', ':ch:', 'ch', 'cn', ':cn:', '中文', '简体', '简中'],
        'TW': ['taiwan', 'tw', ':tw:', 'traditional', '繁体', '台湾', '繁體', '繁中'],
        'EN': ['english', ':en:', 'en', '英文', '英语'],
        'JP': ['japanese', ':jp:', 'jp', 'japan', '日语', '日文', '日本语'],
        'KR': ['korean', ':kr:', 'kr', 'korea', '韩语', '韩文', '韓語'],
        'PT': ['portuguese', ':pt:', 'pt', 'pt-br', 'brazil', 'br', ':br:', '葡萄牙', '巴西'],
        'ES': ['spanish', ':es:', 'es', 'spain', '西班牙', '西班牙语', '西语'],
        'FR': ['french', ':fr:', 'fr', 'france', '法语', '法文'],
        'DE': ['german', ':de:', 'de', 'germany', '德语', '德文'],
        'IT': ['italian', ':it:', 'it', 'italy', '意大利', '意大利语', '意语'],
        'RU': ['russian', ':ru:', 'ru', 'russia', '俄语', '俄文', '俄罗斯语'],
        'PL': ['polish', ':pl:', 'pl', 'poland', '波兰', '波兰语'],
        'NL': ['dutch', ':nl:', 'nl', 'netherlands', '荷兰', '荷兰语'],
        'TH': ['thai', ':th:', 'th', 'thailand', '泰', '泰语', '泰文'],
        'VN': ['vietnamese', ':vn:', 'vn', 'vietnam', '越南', '越南语', '越南文'],
        'IND': ['indonesian', ':ind:', 'ind', 'indonesia', ':id:', 'id', '印尼', '印尼语'],
        'MS': ['malay', ':ms:', 'ms', 'malaysia', '马来', '马来语', '马来文'],
        'TR': ['turkish', ':tr:', 'tr', 'turkey', '土耳其', '土耳其语', '土耳其文'],
        'AR': ['arabic', ':ar:', 'ar', '阿拉伯', '阿拉伯语', '阿语'],
        'HI': ['hindi', ':hi:', 'hi', 'india', '印地', '印地语']
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
            'CH_columns': [],
            'TW_columns': [],
            'EN_columns': [],
            'JP_columns': [],
            'KR_columns': [],
            'PT_columns': [],
            'ES_columns': [],
            'FR_columns': [],
            'DE_columns': [],
            'IT_columns': [],
            'RU_columns': [],
            'PL_columns': [],
            'NL_columns': [],
            'TH_columns': [],
            'VN_columns': [],
            'IND_columns': [],
            'MS_columns': [],
            'TR_columns': [],
            'AR_columns': [],
            'HI_columns': []
        }

        # First, check column names
        for col_idx, col_name in enumerate(df.columns):
            col_name_lower = str(col_name).lower()

            # Check source indicators
            if any(indicator in col_name_lower for indicator in cls.COLUMN_INDICATORS['source']):
                result['source_columns'].append(col_idx)

            # Check all language indicators
            for lang in ['CH', 'TW', 'EN', 'JP', 'KR', 'PT', 'ES', 'FR', 'DE', 'IT', 'RU', 'PL', 'NL',
                        'TH', 'VN', 'IND', 'MS', 'TR', 'AR', 'HI']:
                if lang in cls.COLUMN_INDICATORS:
                    if any(indicator in col_name_lower for indicator in cls.COLUMN_INDICATORS[lang]):
                        result[f'{lang}_columns'].append(col_idx)

        # If no columns identified by name, use content detection
        if not any(result.values()):
            column_langs = cls.detect_column_languages(df)

            for col_idx, lang in column_langs.items():
                # Source languages
                if lang in ['CH', 'EN', 'TW', 'JP', 'KR']:
                    result['source_columns'].append(col_idx)

                # Map detected language to result columns
                lang_key = f'{lang}_columns'
                if lang_key in result:
                    result[lang_key].append(col_idx)
                # Handle BR as PT
                elif lang in ['BR']:
                    result['PT_columns'].append(col_idx)

        return result

    @classmethod
    def analyze_sheet(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze a sheet for language information."""
        language_columns = cls.identify_language_columns(df)

        # Determine source languages
        source_langs = set()
        for col_idx in language_columns['source_columns']:
            if col_idx < len(df.columns):
                sample = df.iloc[:, col_idx].dropna().astype(str).head(20)
                for text in sample:
                    lang = cls.detect_language(text)
                    if lang in ['CH', 'EN', 'TW', 'JP', 'KR']:
                        source_langs.add(lang)

        # Also check specifically labeled language columns for source
        # ✅ FIX: Only add if column has content (not empty)
        for potential_source in ['CH', 'EN', 'TW', 'JP', 'KR']:
            lang_key = f'{potential_source}_columns'
            if language_columns.get(lang_key):
                for col_idx in language_columns[lang_key]:
                    if col_idx < len(df.columns):
                        non_empty = df.iloc[:, col_idx].dropna().astype(str).str.strip().str.len().sum()
                        if non_empty > 0:
                            source_langs.add(potential_source)
                            break

        # Determine available target languages
        target_langs = []
        # Check all supported languages
        for lang in ['EN', 'CH', 'TW', 'JP', 'KR', 'PT', 'ES', 'FR', 'DE', 'IT', 'RU', 'PL', 'NL',
                     'TH', 'VN', 'IND', 'MS', 'TR', 'AR', 'HI']:
            lang_key = f'{lang}_columns'
            # Add as target if column exists and not a source language
            if language_columns.get(lang_key) and lang not in source_langs:
                target_langs.append(lang)

        return {
            'source_languages': list(source_langs),
            'target_languages': target_langs,
            'language_columns': language_columns,
            'has_translation_pairs': len(source_langs) > 0 and len(target_langs) > 0
        }