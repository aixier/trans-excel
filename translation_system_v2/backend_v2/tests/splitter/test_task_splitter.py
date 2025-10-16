"""Integration tests for TaskSplitter."""

import unittest
import pandas as pd
import time

from services.splitter import (
    TaskSplitter,
    EmptyCellRule,
    YellowCellRule,
    BlueCellRule,
    CapsSheetRule,
    InvalidDataStateError
)
from services.splitter.mock_data_state import MockDataState


class TestTaskSplitter(unittest.TestCase):
    """Test cases for TaskSplitter."""

    def setUp(self):
        """Set up test fixtures."""
        self.splitter = TaskSplitter()

    def test_split_with_test_data(self):
        """Test splitting with test data state."""
        # Create test data state
        data_state = MockDataState.create_test_state()

        # Create rules
        rules = [
            EmptyCellRule(),
            YellowCellRule(),
            BlueCellRule(),
        ]

        # Split
        task_df = self.splitter.split(data_state, rules)

        # Verify tasks were created
        self.assertIsNotNone(task_df)
        self.assertGreater(len(task_df), 0)

        # Verify all tasks have status 'pending'
        self.assertTrue(all(task_df['status'] == 'pending'))

        # Verify tasks are sorted by priority (descending)
        priorities = task_df['priority'].tolist()
        self.assertEqual(priorities, sorted(priorities, reverse=True))

    def test_split_empty_cells(self):
        """Test splitting identifies empty cells."""
        data_state = MockDataState.create_test_state()
        rules = [EmptyCellRule()]

        task_df = self.splitter.split(data_state, rules)

        # Verify empty cell tasks were created
        empty_tasks = task_df[task_df['task_id'].str.contains('EMPTY')]
        self.assertGreater(len(empty_tasks), 0)

        # Verify all empty tasks have operation='translate'
        self.assertTrue(all(empty_tasks['operation'] == 'translate'))

    def test_split_yellow_cells(self):
        """Test splitting identifies yellow cells."""
        data_state = MockDataState.create_test_state()
        rules = [YellowCellRule()]

        task_df = self.splitter.split(data_state, rules)

        # Verify yellow cell tasks were created
        yellow_tasks = task_df[task_df['task_id'].str.contains('YELLOW')]
        self.assertGreater(len(yellow_tasks), 0)

        # Verify all yellow tasks have priority 9
        self.assertTrue(all(yellow_tasks['priority'] == 9))

    def test_split_blue_cells(self):
        """Test splitting identifies blue cells."""
        data_state = MockDataState.create_test_state()
        rules = [BlueCellRule()]

        task_df = self.splitter.split(data_state, rules)

        # Verify blue cell tasks were created
        blue_tasks = task_df[task_df['task_id'].str.contains('BLUE')]
        self.assertGreater(len(blue_tasks), 0)

        # Verify all blue tasks have priority 7
        self.assertTrue(all(blue_tasks['priority'] == 7))

    def test_split_caps_sheet(self):
        """Test splitting identifies CAPS sheet cells."""
        data_state = MockDataState.create_test_state()
        rules = [CapsSheetRule()]

        task_df = self.splitter.split(data_state, rules)

        # Verify CAPS tasks were created
        caps_tasks = task_df[task_df['task_id'].str.contains('CAPS')]
        self.assertGreater(len(caps_tasks), 0)

        # Verify all CAPS tasks have operation='uppercase'
        self.assertTrue(all(caps_tasks['operation'] == 'uppercase'))

        # Verify all CAPS tasks have priority 3
        self.assertTrue(all(caps_tasks['priority'] == 3))

    def test_split_multiple_rules(self):
        """Test splitting with multiple rules."""
        data_state = MockDataState.create_test_state()
        rules = [
            YellowCellRule(),  # Priority 9
            BlueCellRule(),    # Priority 7
            EmptyCellRule(),   # Priority 5
            CapsSheetRule(),   # Priority 3
        ]

        task_df = self.splitter.split(data_state, rules)

        # Verify tasks were created
        self.assertGreater(len(task_df), 0)

        # Verify we have different types of tasks
        task_types = task_df['task_id'].str.extract(r'^([A-Z]+)_')[0].unique()
        self.assertGreater(len(task_types), 1)

    def test_rule_priority_order(self):
        """Test that higher priority rules take precedence."""
        # Create data with a cell that matches multiple rules
        data = pd.DataFrame({
            'CH': ['你好'],
            'TH': [''],  # Empty (EmptyCellRule) and could be yellow
        })

        data_state = MockDataState({'Sheet1': data})
        # Make the cell yellow
        data_state.set_cell_color('Sheet1', 0, 1, 'FFFF00')

        # Apply rules in priority order
        rules = [
            YellowCellRule(),  # Priority 9
            EmptyCellRule(),   # Priority 5
        ]

        task_df = self.splitter.split(data_state, rules)

        # The cell should only have ONE task (from YellowCellRule, higher priority)
        self.assertEqual(len(task_df), 1)
        self.assertIn('YELLOW', task_df.iloc[0]['task_id'])

    def test_no_duplicate_tasks(self):
        """Test that no duplicate tasks are created."""
        data_state = MockDataState.create_test_state()
        rules = [
            EmptyCellRule(),
            YellowCellRule(),
            BlueCellRule(),
        ]

        task_df = self.splitter.split(data_state, rules)

        # Check for duplicate cell positions
        cell_positions = list(zip(
            task_df['sheet_name'],
            task_df['row_idx'],
            task_df['col_idx']
        ))

        self.assertEqual(len(cell_positions), len(set(cell_positions)))

    def test_empty_rules_list(self):
        """Test splitting with empty rules list."""
        data_state = MockDataState.create_test_state()
        rules = []

        task_df = self.splitter.split(data_state, rules)

        # Should return empty DataFrame
        self.assertEqual(len(task_df), 0)

    def test_invalid_data_state(self):
        """Test splitting with invalid data state."""
        rules = [EmptyCellRule()]

        # None data state
        with self.assertRaises(InvalidDataStateError):
            self.splitter.split(None, rules)

        # Data state without sheets attribute
        class BadDataState:
            pass

        with self.assertRaises(InvalidDataStateError):
            self.splitter.split(BadDataState(), rules)

    def test_empty_data_state(self):
        """Test splitting with empty data state."""
        data_state = MockDataState.create_empty_state()
        rules = [EmptyCellRule()]

        # Should not raise error, but return empty tasks
        task_df = self.splitter.split(data_state, rules)
        self.assertEqual(len(task_df), 0)

    def test_large_data_performance(self):
        """Test splitting performance with large dataset."""
        # Create large data state (1000 rows)
        data_state = MockDataState.create_large_state(1000)
        rules = [
            EmptyCellRule(),
            YellowCellRule(),
        ]

        # Measure split time
        start_time = time.time()
        task_df = self.splitter.split(data_state, rules)
        elapsed_time = time.time() - start_time

        # Should complete in less than 5 seconds
        self.assertLess(elapsed_time, 5.0)

        # Should create tasks
        self.assertGreater(len(task_df), 0)

    def test_statistics(self):
        """Test getting statistics after split."""
        data_state = MockDataState.create_test_state()
        rules = [EmptyCellRule(), YellowCellRule()]

        task_df = self.splitter.split(data_state, rules)
        stats = self.splitter.get_statistics()

        # Verify statistics
        self.assertGreater(stats['total'], 0)
        self.assertIn('pending', stats['by_status'])
        self.assertGreater(stats['by_status']['pending'], 0)

    def test_task_fields(self):
        """Test that all required task fields are present."""
        data_state = MockDataState.create_test_state()
        rules = [EmptyCellRule()]

        task_df = self.splitter.split(data_state, rules)

        # Check required fields
        required_fields = [
            'task_id', 'operation', 'priority', 'sheet_name',
            'row_idx', 'col_idx', 'target_lang', 'status'
        ]

        for field in required_fields:
            self.assertIn(field, task_df.columns)

        # Check that all tasks have non-null required fields
        for field in required_fields:
            self.assertTrue(task_df[field].notna().all())


class TestTaskSplitterEdgeCases(unittest.TestCase):
    """Test edge cases for TaskSplitter."""

    def test_special_characters_in_sheet_name(self):
        """Test handling sheets with special characters in name."""
        data = pd.DataFrame({
            'CH': ['你好'],
            'TH': [''],
        })

        sheets = {
            'Sheet-1 (Test)': data,
            'CAPS_Sheet!': data,
        }

        data_state = MockDataState(sheets)
        splitter = TaskSplitter()

        # Should handle special characters
        rules = [EmptyCellRule(), CapsSheetRule()]
        task_df = splitter.split(data_state, rules)

        self.assertGreater(len(task_df), 0)

    def test_unicode_content(self):
        """Test handling unicode content."""
        data = pd.DataFrame({
            'CH': ['你好世界', '🎮游戏', 'Test测试'],
            'EN': ['Hello World', 'Game🎲', 'Test测试'],
            'TH': ['', '', ''],
        })

        data_state = MockDataState({'Sheet1': data})
        splitter = TaskSplitter()

        rules = [EmptyCellRule()]
        task_df = splitter.split(data_state, rules)

        # Should handle unicode properly
        self.assertEqual(len(task_df), 3)
        self.assertIn('🎮游戏', task_df['source_text'].tolist())

    def test_very_long_text(self):
        """Test handling very long text."""
        long_text = 'A' * 10000
        data = pd.DataFrame({
            'CH': [long_text],
            'TH': [''],
        })

        data_state = MockDataState({'Sheet1': data})
        splitter = TaskSplitter()

        rules = [EmptyCellRule()]
        task_df = splitter.split(data_state, rules)

        self.assertEqual(len(task_df), 1)
        self.assertEqual(task_df.iloc[0]['source_text'], long_text)


if __name__ == '__main__':
    unittest.main()
