"""Empty cell rule for identifying cells that need translation."""

from typing import Dict, Any
import pandas as pd

from ..split_rule import SplitRule


class EmptyCellRule(SplitRule):
    """Rule for identifying empty cells in target language columns.

    This rule matches cells that:
    1. Are empty or contain only whitespace
    2. Are in target language columns (TH, TW, PT, EN, VN, etc.)
    3. Have corresponding source text in CH or EN columns
    """

    # Target language columns that should be translated
    TARGET_COLUMNS = ['TH', 'TW', 'PT', 'EN', 'VN', 'ID', 'ES', 'FR', 'DE', 'RU', 'AR', 'JA', 'KO']

    # Source language columns
    SOURCE_COLUMNS = ['CH', 'CN', 'EN']

    def match(self, cell: Any, context: Dict[str, Any]) -> bool:
        """Check if cell is empty and in a target language column.

        Args:
            cell: Cell value to check
            context: Context containing column_name, row_data, etc.

        Returns:
            bool: True if cell is empty and should be translated
        """
        # Check if cell is empty
        if not self._is_empty(cell):
            return False

        # Check if column is a target language column
        column_name = context.get('column_name', '').upper()
        if column_name not in self.TARGET_COLUMNS:
            return False

        # Check if there's source text available
        row_data = context.get('row_data')
        if row_data is None:
            return False

        # Look for source text in CH or EN columns
        source_text = self._find_source_text(row_data)
        if not source_text:
            return False

        return True

    def create_task(self, cell: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a translation task for an empty cell.

        Args:
            cell: Cell value (empty)
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
        task_id = f"EMPTY_{sheet_name}_{row_idx}_{col_idx}"

        # Generate cell reference (e.g., 'A1')
        cell_ref = self._generate_cell_ref(row_idx, col_idx)

        return {
            'task_id': task_id,
            'operation': 'translate',
            'priority': 5,  # Normal priority
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
                'rule': 'EmptyCellRule',
                'is_retranslation': False
            }
        }

    def get_priority(self) -> int:
        """Return priority for empty cell rule."""
        return 5  # Normal priority

    def get_operation_type(self) -> str:
        """Return operation type."""
        return 'translate'

    def _is_empty(self, cell: Any) -> bool:
        """Check if a cell is empty.

        Args:
            cell: Cell value to check

        Returns:
            bool: True if cell is empty or contains only whitespace
        """
        if cell is None:
            return True

        if pd.isna(cell):
            return True

        if isinstance(cell, str) and cell.strip() == '':
            return True

        return False

    def _find_source_text(self, row_data: pd.Series) -> str:
        """Find source text from row data.

        Args:
            row_data: Pandas Series containing row data

        Returns:
            str: Source text, or empty string if not found
        """
        # Try CH column first, then CN, then EN
        for col in self.SOURCE_COLUMNS:
            if col in row_data.index:
                value = row_data[col]
                if not self._is_empty(value):
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
                if not self._is_empty(value):
                    return (str(value).strip(), 'CH')

        # Try EN column
        if 'EN' in row_data.index:
            value = row_data['EN']
            if not self._is_empty(value):
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
        # Convert column index to letters (0=A, 1=B, ..., 25=Z, 26=AA, etc.)
        col_letter = ''
        col_num = col_idx + 1  # Excel columns are 1-based

        while col_num > 0:
            col_num, remainder = divmod(col_num - 1, 26)
            col_letter = chr(65 + remainder) + col_letter

        # Excel rows are 1-based
        return f"{col_letter}{row_idx + 1}"
