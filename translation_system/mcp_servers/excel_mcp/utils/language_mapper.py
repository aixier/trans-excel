"""Language column name mapper for Excel headers.

Supports multiple formats:
- Standard: CH, EN, PT, TH, VN, TR, TW, IND
- Colon format: :CH:, :EN:, :PT:, :ES:, :id:
- Chinese names: 中文, 英文
"""

from typing import Dict, List, Optional


class LanguageMapper:
    """Map various column name formats to standard language codes."""

    # Standard language code mappings
    LANGUAGE_MAPPINGS = {
        'CH': ['CH', ':CH:', 'CN', '中文', 'CHINESE', 'ZH', 'ZH-CN'],
        'EN': ['EN', ':EN:', '英文', 'ENGLISH'],
        'PT': ['PT', ':PT:', 'PORTUGUESE', 'BR'],
        'TH': ['TH', ':TH:', 'THAI'],
        'VN': ['VN', ':VN:', 'VIETNAMESE', 'VI'],
        'TR': ['TR', ':TR:', 'TURKISH'],
        'TW': ['TW', ':TW:', 'ZH-TW', '繁体', '繁體'],
        'ID': ['ID', 'IND', ':id:', ':ID:', 'INDONESIAN'],
        'ES': ['ES', ':ES:', 'SPANISH'],
        'JP': ['JP', ':JP:', 'JA', 'JAPANESE', '日文'],
        'KR': ['KR', ':KR:', 'KO', 'KOREAN', '韩文'],
        'FR': ['FR', ':FR:', 'FRENCH', '法文'],
        'DE': ['DE', ':DE:', 'GERMAN', '德文'],
        'IT': ['IT', ':IT:', 'ITALIAN', '意文'],
        'RU': ['RU', ':RU:', 'RUSSIAN', '俄文'],
        'AR': ['AR', ':AR:', 'ARABIC', '阿拉伯文']
    }

    # Reverse mapping: variant -> standard code
    _reverse_map: Dict[str, str] = None

    @classmethod
    def _build_reverse_map(cls):
        """Build reverse mapping from variants to standard codes."""
        if cls._reverse_map is None:
            cls._reverse_map = {}
            for standard_code, variants in cls.LANGUAGE_MAPPINGS.items():
                for variant in variants:
                    cls._reverse_map[variant.upper()] = standard_code

    @classmethod
    def normalize_language_code(cls, column_name: str) -> Optional[str]:
        """
        Normalize a column name to standard language code.

        Args:
            column_name: Column name from Excel header (e.g., 'CH', ':EN:', '中文')

        Returns:
            Standard language code (e.g., 'CH', 'EN') or None if not recognized

        Examples:
            >>> LanguageMapper.normalize_language_code('CH')
            'CH'
            >>> LanguageMapper.normalize_language_code(':EN:')
            'EN'
            >>> LanguageMapper.normalize_language_code('中文')
            'CH'
            >>> LanguageMapper.normalize_language_code(':id:')
            'ID'
        """
        cls._build_reverse_map()
        return cls._reverse_map.get(column_name.upper())

    @classmethod
    def get_all_variants(cls, standard_code: str) -> List[str]:
        """
        Get all variants for a standard language code.

        Args:
            standard_code: Standard language code (e.g., 'CH', 'EN')

        Returns:
            List of all variants
        """
        return cls.LANGUAGE_MAPPINGS.get(standard_code.upper(), [])

    @classmethod
    def is_language_column(cls, column_name: str) -> bool:
        """
        Check if a column name is a language column.

        Args:
            column_name: Column name from Excel header

        Returns:
            True if it's a language column, False otherwise
        """
        return cls.normalize_language_code(column_name) is not None

    @classmethod
    def detect_languages_in_columns(cls, columns: List[str]) -> Dict[str, str]:
        """
        Detect all language columns in a list of column names.

        Args:
            columns: List of column names from Excel

        Returns:
            Dict mapping original column name to standard language code

        Example:
            >>> LanguageMapper.detect_languages_in_columns(['key', 'CH', ':EN:', 'PT'])
            {'CH': 'CH', ':EN:': 'EN', 'PT': 'PT'}
        """
        result = {}
        for col in columns:
            standard_code = cls.normalize_language_code(col)
            if standard_code:
                result[col] = standard_code
        return result

    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """Get list of all supported standard language codes."""
        return list(cls.LANGUAGE_MAPPINGS.keys())


# Convenience functions
def normalize_language(col_name: str) -> Optional[str]:
    """Normalize language column name to standard code."""
    return LanguageMapper.normalize_language_code(col_name)


def is_language_column(col_name: str) -> bool:
    """Check if column name is a language column."""
    return LanguageMapper.is_language_column(col_name)


def detect_languages(columns: List[str]) -> Dict[str, str]:
    """Detect all language columns."""
    return LanguageMapper.detect_languages_in_columns(columns)
