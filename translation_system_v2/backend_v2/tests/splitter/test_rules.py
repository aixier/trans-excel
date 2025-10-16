"""Unit tests for split rules."""

import unittest
import pandas as pd

from services.splitter.rules.empty_cell import EmptyCellRule
from services.splitter.rules.yellow_cell import YellowCellRule
from services.splitter.rules.blue_cell import BlueCellRule
from services.splitter.rules.caps_sheet import CapsSheetRule


class TestEmptyCellRule(unittest.TestCase):
    """Test cases for EmptyCellRule."""

    def setUp(self):
        """Set up test fixtures."""
        self.rule = EmptyCellRule()

    def test_match_empty_cell_in_target_column(self):
        """Test matching empty cell in target language column."""
        cell = ''
        context = {
            'column_name': 'TH',
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': ''}),
            'sheet_name': 'Sheet1',
            'row_idx': 0,
            'col_idx': 2
        }

        self.assertTrue(self.rule.match(cell, context))

    def test_no_match_non_empty_cell(self):
        """Test no match for non-empty cell."""
        cell = 'สวัสดี'
        context = {
            'column_name': 'TH',
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': 'สวัสดี'}),
            'sheet_name': 'Sheet1',
            'row_idx': 0,
            'col_idx': 2
        }

        self.assertFalse(self.rule.match(cell, context))

    def test_no_match_empty_source(self):
        """Test no match when source text is empty."""
        cell = ''
        context = {
            'column_name': 'TH',
            'row_data': pd.Series({'CH': '', 'EN': '', 'TH': ''}),
            'sheet_name': 'Sheet1',
            'row_idx': 0,
            'col_idx': 2
        }

        self.assertFalse(self.rule.match(cell, context))

    def test_no_match_non_target_column(self):
        """Test no match for non-target column."""
        cell = ''
        context = {
            'column_name': 'CH',
            'row_data': pd.Series({'CH': '', 'EN': 'Hello', 'TH': ''}),
            'sheet_name': 'Sheet1',
            'row_idx': 0,
            'col_idx': 0
        }

        self.assertFalse(self.rule.match(cell, context))

    def test_create_task(self):
        """Test task creation for empty cell."""
        cell = ''
        context = {
            'column_name': 'TH',
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': ''}),
            'sheet_name': 'Sheet1',
            'row_idx': 0,
            'col_idx': 2
        }

        task = self.rule.create_task(cell, context)

        self.assertEqual(task['operation'], 'translate')
        self.assertEqual(task['priority'], 5)
        self.assertEqual(task['target_lang'], 'TH')
        self.assertEqual(task['source_text'], '你好')
        self.assertEqual(task['source_lang'], 'CH')
        self.assertEqual(task['status'], 'pending')
        self.assertIn('EMPTY_', task['task_id'])

    def test_priority(self):
        """Test priority value."""
        self.assertEqual(self.rule.get_priority(), 5)

    def test_operation_type(self):
        """Test operation type."""
        self.assertEqual(self.rule.get_operation_type(), 'translate')


class TestYellowCellRule(unittest.TestCase):
    """Test cases for YellowCellRule."""

    def setUp(self):
        """Set up test fixtures."""
        self.rule = YellowCellRule()

    def test_match_yellow_cell_in_target_column(self):
        """Test matching yellow cell in target language column."""
        cell = 'สวัสดี'
        context = {
            'column_name': 'TH',
            'color': 'FFFF00',
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': 'สวัสดี'}),
            'sheet_name': 'Sheet1',
            'row_idx': 0,
            'col_idx': 2
        }

        self.assertTrue(self.rule.match(cell, context))

    def test_no_match_non_yellow_cell(self):
        """Test no match for non-yellow cell."""
        cell = 'สวัสดี'
        context = {
            'column_name': 'TH',
            'color': None,
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': 'สวัสดี'}),
            'sheet_name': 'Sheet1',
            'row_idx': 0,
            'col_idx': 2
        }

        self.assertFalse(self.rule.match(cell, context))

    def test_no_match_yellow_source_column(self):
        """Test no match for yellow cell in source column."""
        cell = '你好'
        context = {
            'column_name': 'CH',
            'color': 'FFFF00',
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': ''}),
            'sheet_name': 'Sheet1',
            'row_idx': 0,
            'col_idx': 0
        }

        self.assertFalse(self.rule.match(cell, context))

    def test_create_task_with_reference_en(self):
        """Test task creation with EN reference."""
        cell = 'สวัสดี'
        context = {
            'column_name': 'TH',
            'color': 'FFFF00',
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': 'สวัสดี'}),
            'sheet_name': 'Sheet1',
            'row_idx': 0,
            'col_idx': 2
        }

        task = self.rule.create_task(cell, context)

        self.assertEqual(task['operation'], 'translate')
        self.assertEqual(task['priority'], 9)
        self.assertEqual(task['target_lang'], 'TH')
        self.assertEqual(task['source_text'], '你好')
        self.assertEqual(task['reference_en'], 'Hello')
        self.assertEqual(task['status'], 'pending')
        self.assertIn('YELLOW_', task['task_id'])
        self.assertTrue(task['metadata']['is_retranslation'])

    def test_priority(self):
        """Test priority value."""
        self.assertEqual(self.rule.get_priority(), 9)

    def test_operation_type(self):
        """Test operation type."""
        self.assertEqual(self.rule.get_operation_type(), 'translate')


class TestBlueCellRule(unittest.TestCase):
    """Test cases for BlueCellRule."""

    def setUp(self):
        """Set up test fixtures."""
        self.rule = BlueCellRule()

    def test_match_blue_cell_in_target_column(self):
        """Test matching blue cell in target language column."""
        cell = 'สวัสดี'
        context = {
            'column_name': 'TH',
            'color': '4472C4',
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': 'สวัสดี'}),
            'sheet_name': 'Sheet1',
            'row_idx': 0,
            'col_idx': 2
        }

        self.assertTrue(self.rule.match(cell, context))

    def test_no_match_non_blue_cell(self):
        """Test no match for non-blue cell."""
        cell = 'สวัสดี'
        context = {
            'column_name': 'TH',
            'color': None,
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': 'สวัสดี'}),
            'sheet_name': 'Sheet1',
            'row_idx': 0,
            'col_idx': 2
        }

        self.assertFalse(self.rule.match(cell, context))

    def test_create_task(self):
        """Test task creation for blue cell."""
        cell = 'สวัสดี'
        context = {
            'column_name': 'TH',
            'color': '4472C4',
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': 'สวัสดี'}),
            'sheet_name': 'Sheet1',
            'row_idx': 0,
            'col_idx': 2
        }

        task = self.rule.create_task(cell, context)

        self.assertEqual(task['operation'], 'translate')
        self.assertEqual(task['priority'], 7)
        self.assertEqual(task['target_lang'], 'TH')
        self.assertEqual(task['status'], 'pending')
        self.assertIn('BLUE_', task['task_id'])
        self.assertTrue(task['metadata']['is_retranslation'])
        self.assertTrue(task['metadata']['requires_context'])

    def test_priority(self):
        """Test priority value."""
        self.assertEqual(self.rule.get_priority(), 7)

    def test_operation_type(self):
        """Test operation type."""
        self.assertEqual(self.rule.get_operation_type(), 'translate')


class TestCapsSheetRule(unittest.TestCase):
    """Test cases for CapsSheetRule."""

    def setUp(self):
        """Set up test fixtures."""
        self.rule = CapsSheetRule()

    def test_match_caps_sheet_target_column(self):
        """Test matching cell in CAPS sheet target column."""
        cell = 'hello'
        context = {
            'sheet_name': 'CAPS_Sheet',
            'column_name': 'TH',
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': 'hello'}),
            'row_idx': 0,
            'col_idx': 2
        }

        self.assertTrue(self.rule.match(cell, context))

    def test_no_match_non_caps_sheet(self):
        """Test no match for non-CAPS sheet."""
        cell = 'hello'
        context = {
            'sheet_name': 'Sheet1',
            'column_name': 'TH',
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': 'hello'}),
            'row_idx': 0,
            'col_idx': 2
        }

        self.assertFalse(self.rule.match(cell, context))

    def test_no_match_source_column(self):
        """Test no match for source columns in CAPS sheet."""
        cell = '你好'
        context = {
            'sheet_name': 'CAPS_Sheet',
            'column_name': 'CH',
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': ''}),
            'row_idx': 0,
            'col_idx': 0
        }

        self.assertFalse(self.rule.match(cell, context))

    def test_match_empty_cell_in_caps_sheet(self):
        """Test matching empty cell in CAPS sheet."""
        cell = ''
        context = {
            'sheet_name': 'CAPS_Sheet',
            'column_name': 'TH',
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': ''}),
            'row_idx': 0,
            'col_idx': 2
        }

        self.assertTrue(self.rule.match(cell, context))

    def test_create_task(self):
        """Test task creation for CAPS cell."""
        cell = 'hello'
        context = {
            'sheet_name': 'CAPS_Sheet',
            'column_name': 'TH',
            'row_data': pd.Series({'CH': '你好', 'EN': 'Hello', 'TH': 'hello'}),
            'row_idx': 0,
            'col_idx': 2
        }

        task = self.rule.create_task(cell, context)

        # IMPORTANT: operation should be 'uppercase', NOT 'translate'
        self.assertEqual(task['operation'], 'uppercase')
        self.assertEqual(task['priority'], 3)
        self.assertEqual(task['target_lang'], 'TH')
        self.assertEqual(task['status'], 'pending')
        self.assertIn('CAPS_', task['task_id'])
        self.assertEqual(task['source_text'], 'hello')

    def test_priority(self):
        """Test priority value."""
        self.assertEqual(self.rule.get_priority(), 3)

    def test_operation_type(self):
        """Test operation type is uppercase."""
        self.assertEqual(self.rule.get_operation_type(), 'uppercase')


if __name__ == '__main__':
    unittest.main()
