"""CAPS sheet rule for identifying cells that need uppercase conversion."""

from typing import Dict, Any
import pandas as pd

from ..split_rule import SplitRule


class CapsSheetRule(SplitRule):
    """Rule for identifying cells in CAPS sheets that need uppercase conversion.

    This rule matches cells that:
    1. Are in sheets with 'CAPS' in their name
    2. Are in ANY language columns (source AND target languages)
    3. Excludes only the first index column (KEY)
    4. Need to be converted to uppercase

    IMPORTANT: This rule creates tasks with operation='uppercase', NOT 'translate'.
    The uppercase conversion processes both source and target language columns.
    """

    # Columns to exclude from uppercase (only index columns)
    EXCLUDE_COLUMNS = ['KEY', 'key', 'Key', 'INDEX', 'index', 'Index', 'ID', 'id', 'Id']

    def match(self, cell: Any, context: Dict[str, Any]) -> bool:
        """Check if cell is in a CAPS sheet and should be uppercased.

        Args:
            cell: Cell value
            context: Context containing sheet_name, column_name, etc.

        Returns:
            bool: True if cell should be uppercased
        """
        # Check if sheet name contains 'CAPS'
        sheet_name = context.get('sheet_name', '').upper()
        if 'CAPS' not in sheet_name:
            return False

        # Get column information
        column_name = context.get('column_name', '')
        col_idx = context.get('col_idx', 0)

        # Exclude index columns (first column or columns in EXCLUDE_COLUMNS)
        if col_idx == 0:  # First column is always the index
            return False

        if column_name.upper() in [c.upper() for c in self.EXCLUDE_COLUMNS]:
            return False

        # Match all other columns (source and target languages)
        # For CAPS tasks, we match all cells (empty or not)
        # because they will be uppercased
        return True

    def create_task(self, cell: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create an uppercase conversion task for a cell in CAPS sheet.

        Args:
            cell: Cell value
            context: Context information

        Returns:
            Dict containing task information with operation='uppercase'
        """
        sheet_name = context['sheet_name']
        row_idx = context['row_idx']
        col_idx = context['col_idx']
        column_name = context.get('column_name', '')

        # Generate task ID
        task_id = f"CAPS_{sheet_name}_{row_idx}_{col_idx}"

        # Generate cell reference
        cell_ref = self._generate_cell_ref(row_idx, col_idx)

        # For CAPS tasks, source_text is the current value (may be source or target language)
        # It will be converted to uppercase
        current_value = str(cell) if not pd.isna(cell) and cell else ''

        return {
            'task_id': task_id,
            'operation': 'uppercase',  # IMPORTANT: operation is 'uppercase', NOT 'translate'
            'priority': 3,  # Lower priority (execute after translation)
            'sheet_name': sheet_name,
            'row_idx': row_idx,
            'col_idx': col_idx,
            'cell_ref': cell_ref,
            'source_text': current_value,  # Current value (source or target language)
            'source_lang': '',  # Not applicable for uppercase
            'target_lang': column_name,  # Column name (can be any language)
            'status': 'pending',
            'result': '',
            'metadata': {
                'rule': 'CapsSheetRule',
                'column_type': 'all_languages',  # Process all language columns
                'original_value': current_value
            }
        }

    def get_priority(self) -> int:
        """Return priority for CAPS sheet rule.

        CAPS tasks have lower priority because they should be executed
        AFTER translation tasks are complete.
        """
        return 3  # Low priority (after translation)

    def get_operation_type(self) -> str:
        """Return operation type.

        IMPORTANT: Returns 'uppercase', NOT 'translate'.
        """
        return 'uppercase'

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
