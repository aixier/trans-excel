"""Blue cell rule for identifying cells with special handling requirements."""

from typing import Dict, Any
import pandas as pd

from ..split_rule import SplitRule


class BlueCellRule(SplitRule):
    """Rule for identifying blue-highlighted cells.

    Blue cells typically indicate special handling requirements such as:
    1. Context-aware translation
    2. Terminology consistency checks
    3. Format preservation
    """

    # Blue color codes (various shades)
    BLUE_COLORS = ['0000FF', 'FF0000FF', '4472C4', '5B9BD5', '4BACC6', '00B0F0', 'ADD8E6']

    # Target language columns
    TARGET_COLUMNS = ['TH', 'TW', 'PT', 'EN', 'VN', 'ID', 'ES', 'FR', 'DE', 'RU', 'AR', 'JA', 'KO']

    # Source language columns
    SOURCE_COLUMNS = ['CH', 'CN', 'EN']

    def match(self, cell: Any, context: Dict[str, Any]) -> bool:
        """Check if cell is blue and in a target language column.

        Args:
            cell: Cell value
            context: Context containing color, column_name, etc.

        Returns:
            bool: True if cell is blue and should be processed
        """
        # Check if cell has blue color
        color = context.get('color')
        if not self._is_blue(color):
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
        """Create a translation task for a blue cell.

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

        # Generate task ID
        task_id = f"BLUE_{sheet_name}_{row_idx}_{col_idx}"

        # Generate cell reference
        cell_ref = self._generate_cell_ref(row_idx, col_idx)

        return {
            'task_id': task_id,
            'operation': 'translate',
            'priority': 7,  # Higher than normal, lower than yellow
            'sheet_name': sheet_name,
            'row_idx': row_idx,
            'col_idx': col_idx,
            'cell_ref': cell_ref,
            'source_text': source_text,
            'source_lang': source_lang,
            'target_lang': column_name,
            'status': 'pending',
            'result': '',
            'metadata': {
                'rule': 'BlueCellRule',
                'is_retranslation': True,
                'requires_context': True,
                'original_value': str(cell) if not pd.isna(cell) else '',
                'color': context.get('color')
            }
        }

    def get_priority(self) -> int:
        """Return priority for blue cell rule."""
        return 7  # Higher than normal, lower than yellow

    def get_operation_type(self) -> str:
        """Return operation type."""
        return 'translate'

    def _is_blue(self, color: Any) -> bool:
        """Check if color is blue.

        Args:
            color: Color code (hex string)

        Returns:
            bool: True if color is blue
        """
        if color is None:
            return False

        # Normalize color string
        color_str = str(color).upper().replace('#', '')

        # Check against blue color codes
        return color_str in self.BLUE_COLORS

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
