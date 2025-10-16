"""CAPS sheet rule for identifying cells that need uppercase conversion."""

from typing import Dict, Any
import pandas as pd

from ..split_rule import SplitRule


class CapsSheetRule(SplitRule):
    """Rule for identifying cells in CAPS sheets that need uppercase conversion.

    This rule matches cells that:
    1. Are in sheets with 'CAPS' in their name
    2. Are in target language columns (not source columns)
    3. Need to be converted to uppercase after translation

    IMPORTANT: This rule creates tasks with operation='uppercase', NOT 'translate'.
    The uppercase conversion should happen AFTER translation is complete.
    """

    # Target language columns that can be uppercase
    TARGET_COLUMNS = ['TH', 'TW', 'PT', 'EN', 'VN', 'ID', 'ES', 'FR', 'DE', 'RU', 'AR', 'JA', 'KO']

    # Columns to exclude from uppercase (source columns)
    EXCLUDE_COLUMNS = ['KEY', 'CH', 'CN']

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

        # Check if column is a target language column
        column_name = context.get('column_name', '').upper()

        # Exclude source columns
        if column_name in self.EXCLUDE_COLUMNS:
            return False

        # Include only target language columns
        if column_name not in self.TARGET_COLUMNS:
            return False

        # For CAPS tasks, we match all cells (empty or not)
        # because they will be uppercased after translation
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
        column_name = context.get('column_name', '').upper()

        # Generate task ID
        task_id = f"CAPS_{sheet_name}_{row_idx}_{col_idx}"

        # Generate cell reference
        cell_ref = self._generate_cell_ref(row_idx, col_idx)

        # For CAPS tasks, source_text is initially empty
        # It will be filled by the transformer from the translation result
        current_value = str(cell) if not pd.isna(cell) and cell else ''

        return {
            'task_id': task_id,
            'operation': 'uppercase',  # IMPORTANT: operation is 'uppercase', NOT 'translate'
            'priority': 3,  # Lower priority (execute after translation)
            'sheet_name': sheet_name,
            'row_idx': row_idx,
            'col_idx': col_idx,
            'cell_ref': cell_ref,
            'source_text': current_value,  # Current value (may be empty or translated)
            'source_lang': '',  # Not applicable for uppercase
            'target_lang': column_name,
            'status': 'pending',
            'result': '',
            'metadata': {
                'rule': 'CapsSheetRule',
                'requires_translation_first': current_value == '',
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
