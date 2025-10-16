"""Yellow cell rule for identifying cells that need retranslation."""

from typing import Dict, Any
import pandas as pd

from ..split_rule import SplitRule


class YellowCellRule(SplitRule):
    """Rule for identifying yellow-highlighted cells that need retranslation.

    This rule matches cells that:
    1. Have yellow background color
    2. Are in target language columns
    3. Need to be retranslated with higher priority
    """

    # Yellow color codes (various shades)
    YELLOW_COLORS = ['FFFF00', 'FFFFFF00', 'FFFF99', 'FFFFCC', 'FFF9C4', 'FFEB3B']

    # Target language columns
    TARGET_COLUMNS = ['TH', 'TW', 'PT', 'EN', 'VN', 'ID', 'ES', 'FR', 'DE', 'RU', 'AR', 'JA', 'KO']

    # Source language columns
    SOURCE_COLUMNS = ['CH', 'CN', 'EN']

    def match(self, cell: Any, context: Dict[str, Any]) -> bool:
        """Check if cell is yellow and in a target language column.

        Args:
            cell: Cell value
            context: Context containing color, column_name, etc.

        Returns:
            bool: True if cell is yellow and should be retranslated
        """
        # Check if cell has yellow color
        color = context.get('color')
        if not self._is_yellow(color):
            return False

        # Check if column is a target language column
        column_name = context.get('column_name', '').upper()
        if column_name not in self.TARGET_COLUMNS:
            return False

        # Check if there's source text available
        row_data = context.get('row_data')
        if row_data is None:
            return False

        source_text = self._find_source_text(row_data)
        if not source_text:
            return False

        return True

    def create_task(self, cell: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a retranslation task for a yellow cell.

        Args:
            cell: Cell value
            context: Context information

        Returns:
            Dict containing task information
        """
        sheet_name = context['sheet_name']
        row_idx = context['row_idx']
        col_idx = context['col_idx']
        column_name = context.get('column_name', '').upper()
        row_data = context.get('row_data')

        # Find source text and language
        source_text, source_lang = self._find_source_text_and_lang(row_data)

        # Get reference EN text if available (for yellow retranslation context)
        reference_en = self._get_reference_en(row_data, column_name)

        # Generate task ID
        task_id = f"YELLOW_{sheet_name}_{row_idx}_{col_idx}"

        # Generate cell reference
        cell_ref = self._generate_cell_ref(row_idx, col_idx)

        return {
            'task_id': task_id,
            'operation': 'translate',
            'priority': 9,  # High priority for yellow cells
            'sheet_name': sheet_name,
            'row_idx': row_idx,
            'col_idx': col_idx,
            'cell_ref': cell_ref,
            'source_text': source_text,
            'source_lang': source_lang,
            'target_lang': column_name,
            'reference_en': reference_en,  # EN reference for context
            'status': 'pending',
            'result': '',
            'metadata': {
                'rule': 'YellowCellRule',
                'is_retranslation': True,
                'original_value': str(cell) if not pd.isna(cell) else '',
                'color': context.get('color')
            }
        }

    def get_priority(self) -> int:
        """Return priority for yellow cell rule."""
        return 9  # High priority

    def get_operation_type(self) -> str:
        """Return operation type."""
        return 'translate'

    def _is_yellow(self, color: Any) -> bool:
        """Check if color is yellow.

        Args:
            color: Color code (hex string)

        Returns:
            bool: True if color is yellow
        """
        if color is None:
            return False

        # Normalize color string
        color_str = str(color).upper().replace('#', '')

        # Check against yellow color codes
        return color_str in self.YELLOW_COLORS

    def _find_source_text(self, row_data: pd.Series) -> str:
        """Find source text from row data.

        Args:
            row_data: Pandas Series containing row data

        Returns:
            str: Source text, or empty string if not found
        """
        for col in self.SOURCE_COLUMNS:
            if col in row_data.index:
                value = row_data[col]
                if not pd.isna(value) and str(value).strip():
                    return str(value).strip()

        return ''

    def _find_source_text_and_lang(self, row_data: pd.Series) -> tuple[str, str]:
        """Find source text and determine source language.

        Args:
            row_data: Pandas Series containing row data

        Returns:
            tuple: (source_text, source_lang)
        """
        # Try CH/CN column first
        for col in ['CH', 'CN']:
            if col in row_data.index:
                value = row_data[col]
                if not pd.isna(value) and str(value).strip():
                    return (str(value).strip(), 'CH')

        # Try EN column
        if 'EN' in row_data.index:
            value = row_data['EN']
            if not pd.isna(value) and str(value).strip():
                return (str(value).strip(), 'EN')

        return ('', 'CH')

    def _get_reference_en(self, row_data: pd.Series, target_lang: str) -> str:
        """Get reference EN text for yellow cell translation.

        When a non-EN column is yellow, use EN as reference.
        When EN itself is yellow, return empty string.

        Args:
            row_data: Pandas Series containing row data
            target_lang: Target language

        Returns:
            str: Reference EN text, or empty string
        """
        # If target is EN, no reference needed
        if target_lang == 'EN':
            return ''

        # Get EN column value
        if 'EN' in row_data.index:
            value = row_data['EN']
            if not pd.isna(value) and str(value).strip():
                return str(value).strip()

        return ''

    def _generate_cell_ref(self, row_idx: int, col_idx: int) -> str:
        """Generate Excel-style cell reference.

        Args:
            row_idx: Row index (0-based)
            col_idx: Column index (0-based)

        Returns:
            str: Cell reference like 'A1', 'B2', etc.
        """
        col_letter = ''
        col_num = col_idx + 1

        while col_num > 0:
            col_num, remainder = divmod(col_num - 1, 26)
            col_letter = chr(65 + remainder) + col_letter

        return f"{col_letter}{row_idx + 1}"
