"""
Comprehensive tests for Transformer module.

Test Coverage:
1. Basic execution with MockProcessor
2. Data state immutability (copy semantics)
3. Task status updates
4. Error handling (single task failure)
5. Context passing to processor
6. Empty task list handling
7. Integration with real processors (UppercaseProcessor)
8. Validation logic
9. Performance (optional)

Target: >= 85% code coverage
"""

import pytest
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional

from services.transformer import Transformer, BaseTransformer
from services.transformer.transformer import (
    TransformerError,
    InvalidTaskError,
    ProcessorError
)
from services.processors import Processor, UppercaseProcessor
from services.data_state import DataState, ExcelState
from models.excel_dataframe import ExcelDataFrame


# ============================================================================
# Mock Processor for Testing
# ============================================================================

class MockProcessor(Processor):
    """Mock processor that returns predictable results for testing."""

    def __init__(self, return_value: str = "MOCK_RESULT", should_fail: bool = False):
        """
        Initialize mock processor.

        Args:
            return_value: Value to return from process()
            should_fail: If True, process() will raise an exception
        """
        super().__init__()
        self.return_value = return_value
        self.should_fail = should_fail
        self.process_calls = []  # Track calls for verification
        self.context_received = None  # Store context for verification

    def get_operation_type(self) -> str:
        """Return mock operation type."""
        return 'mock'

    def process(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Mock process implementation."""
        # Record call
        self.process_calls.append(task.get('task_id'))
        self.context_received = context

        # Simulate failure if requested
        if self.should_fail:
            raise RuntimeError("Mock processor failure")

        # Return mock result
        return self.return_value


class ConditionalFailProcessor(Processor):
    """Processor that fails on specific task IDs."""

    def __init__(self, fail_on_ids: list):
        """
        Initialize processor that fails on specific IDs.

        Args:
            fail_on_ids: List of task IDs that should fail
        """
        super().__init__()
        self.fail_on_ids = fail_on_ids

    def get_operation_type(self) -> str:
        return 'conditional_fail'

    def process(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        task_id = task.get('task_id')
        if task_id in self.fail_on_ids:
            raise RuntimeError(f"Intentional failure for {task_id}")
        return f"SUCCESS_{task_id}"


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_data_state():
    """Create a sample data state for testing."""
    # Create ExcelDataFrame with test data
    excel_df = ExcelDataFrame()
    excel_df.filename = "test.xlsx"
    excel_df.excel_id = "test_001"

    # Create test sheet
    test_data = pd.DataFrame({
        'CH': ['你好', '世界', '测试'],
        'EN': ['', '', ''],
        'PT': ['', '', '']
    })
    excel_df.sheets = {'Sheet1': test_data}
    excel_df.total_rows = len(test_data)
    excel_df.total_cols = len(test_data.columns)
    excel_df.color_map = {}
    excel_df.comment_map = {}

    return ExcelState(excel_df)


@pytest.fixture
def sample_tasks():
    """Create a sample task DataFrame for testing."""
    tasks = pd.DataFrame({
        'task_id': ['T001', 'T002', 'T003'],
        'batch_id': ['B001', 'B001', 'B001'],
        'group_id': ['G001', 'G001', 'G001'],
        'operation': ['mock', 'mock', 'mock'],
        'sheet_name': ['Sheet1', 'Sheet1', 'Sheet1'],
        'row_idx': [0, 1, 2],
        'col_idx': [1, 1, 1],  # EN column
        'source_text': ['你好', '世界', '测试'],
        'target_lang': ['EN', 'EN', 'EN'],
        'status': ['pending', 'pending', 'pending'],
        'result': ['', '', ''],
        'error_message': ['', '', ''],
        'updated_at': [datetime.now(), datetime.now(), datetime.now()]
    })
    return tasks


# ============================================================================
# Test Cases
# ============================================================================

class TestBasicExecution:
    """Test basic transformer execution functionality."""

    def test_basic_execution_with_mock_processor(self, sample_data_state, sample_tasks):
        """Test 1: Basic execution with MockProcessor."""
        # Arrange
        processor = MockProcessor(return_value="TRANSLATED")
        transformer = BaseTransformer(processor)

        # Act
        new_state = transformer.execute(sample_data_state, sample_tasks)

        # Assert
        assert new_state is not None
        assert isinstance(new_state, DataState)
        assert len(processor.process_calls) == 3  # All tasks processed
        assert all(sample_tasks['status'] == 'completed')
        assert all(sample_tasks['result'] == 'TRANSLATED')

    def test_empty_task_list(self, sample_data_state):
        """Test 6: Empty task list handling."""
        # Arrange
        empty_tasks = pd.DataFrame(columns=[
            'task_id', 'operation', 'sheet_name', 'row_idx',
            'col_idx', 'source_text', 'status', 'result'
        ])
        processor = MockProcessor()
        transformer = BaseTransformer(processor)

        # Act
        new_state = transformer.execute(sample_data_state, empty_tasks)

        # Assert
        assert new_state is not None
        assert len(processor.process_calls) == 0  # No tasks processed
        assert len(empty_tasks) == 0


class TestDataStateImmutability:
    """Test that transformers preserve input state immutability."""

    def test_returns_new_data_state(self, sample_data_state, sample_tasks):
        """Test 2: Data state immutability - returns new object."""
        # Arrange
        processor = MockProcessor(return_value="MODIFIED")
        transformer = BaseTransformer(processor)
        original_id = id(sample_data_state)

        # Act
        new_state = transformer.execute(sample_data_state, sample_tasks)

        # Assert
        assert new_state is not sample_data_state  # Different object
        assert id(new_state) != original_id

    def test_original_state_unchanged(self, sample_data_state, sample_tasks):
        """Test 2b: Original data state remains unchanged."""
        # Arrange
        processor = MockProcessor(return_value="MODIFIED")
        transformer = BaseTransformer(processor)

        # Store original values
        original_values = []
        for _, task in sample_tasks.iterrows():
            val = sample_data_state.get_cell_value(
                task['sheet_name'],
                task['row_idx'],
                task['col_idx']
            )
            original_values.append(val)

        # Act
        new_state = transformer.execute(sample_data_state, sample_tasks)

        # Assert - original state unchanged
        for idx, task in sample_tasks.iterrows():
            current_val = sample_data_state.get_cell_value(
                task['sheet_name'],
                task['row_idx'],
                task['col_idx']
            )
            assert current_val == original_values[idx]

    def test_new_state_has_results(self, sample_data_state, sample_tasks):
        """Test 2c: New state contains transformation results."""
        # Arrange
        processor = MockProcessor(return_value="NEW_VALUE")
        transformer = BaseTransformer(processor)

        # Act
        new_state = transformer.execute(sample_data_state, sample_tasks)

        # Assert - new state has updated values
        for _, task in sample_tasks.iterrows():
            new_val = new_state.get_cell_value(
                task['sheet_name'],
                task['row_idx'],
                task['col_idx']
            )
            assert new_val == "NEW_VALUE"


class TestTaskStatusUpdates:
    """Test task status and result updates."""

    def test_task_status_updated_to_completed(self, sample_data_state, sample_tasks):
        """Test 3: Task status updated to 'completed'."""
        # Arrange
        processor = MockProcessor(return_value="RESULT")
        transformer = BaseTransformer(processor)

        # Act
        transformer.execute(sample_data_state, sample_tasks)

        # Assert
        assert all(sample_tasks['status'] == 'completed')

    def test_task_result_filled(self, sample_data_state, sample_tasks):
        """Test 3b: Task result column filled with processor output."""
        # Arrange
        expected_result = "EXPECTED_OUTPUT"
        processor = MockProcessor(return_value=expected_result)
        transformer = BaseTransformer(processor)

        # Act
        transformer.execute(sample_data_state, sample_tasks)

        # Assert
        assert all(sample_tasks['result'] == expected_result)

    def test_updated_at_timestamp_changed(self, sample_data_state, sample_tasks):
        """Test 3c: updated_at timestamp is updated."""
        # Arrange
        original_timestamps = sample_tasks['updated_at'].copy()
        processor = MockProcessor()
        transformer = BaseTransformer(processor)

        # Act (add small delay to ensure timestamp difference)
        import time
        time.sleep(0.01)
        transformer.execute(sample_data_state, sample_tasks)

        # Assert
        # At least one timestamp should be different
        # (comparing all might be flaky due to timing)
        assert any(sample_tasks['updated_at'] != original_timestamps)


class TestErrorHandling:
    """Test error handling and recovery."""

    def test_single_task_failure_doesnt_stop_others(self, sample_data_state, sample_tasks):
        """Test 4: Single task failure doesn't affect other tasks."""
        # Arrange - processor fails on T002 only
        processor = ConditionalFailProcessor(fail_on_ids=['T002'])
        transformer = BaseTransformer(processor)

        # Act
        new_state = transformer.execute(sample_data_state, sample_tasks)

        # Assert
        assert sample_tasks.loc[0, 'status'] == 'completed'  # T001 succeeded
        assert sample_tasks.loc[1, 'status'] == 'failed'     # T002 failed
        assert sample_tasks.loc[2, 'status'] == 'completed'  # T003 succeeded

    def test_failed_task_has_error_message(self, sample_data_state, sample_tasks):
        """Test 4b: Failed task has error message."""
        # Arrange
        processor = ConditionalFailProcessor(fail_on_ids=['T001'])
        transformer = BaseTransformer(processor)

        # Act
        transformer.execute(sample_data_state, sample_tasks)

        # Assert
        error_msg = sample_tasks.loc[0, 'error_message']
        assert error_msg != ''
        assert 'Intentional failure' in error_msg

    def test_failed_task_has_empty_result(self, sample_data_state, sample_tasks):
        """Test 4c: Failed task has empty result."""
        # Arrange
        processor = ConditionalFailProcessor(fail_on_ids=['T002'])
        transformer = BaseTransformer(processor)

        # Act
        transformer.execute(sample_data_state, sample_tasks)

        # Assert
        assert sample_tasks.loc[1, 'result'] == ''  # Failed task has empty result
        assert sample_tasks.loc[0, 'result'] != ''  # Successful task has result


class TestContextPassing:
    """Test context passing to processors."""

    def test_context_passed_to_processor(self, sample_data_state, sample_tasks):
        """Test 5: Context is passed to processor."""
        # Arrange
        processor = MockProcessor()
        transformer = BaseTransformer(processor)
        test_context = {
            'previous_tasks': {'T000': {'result': 'prev_result'}},
            'session_id': 'test_session',
            'config': {'key': 'value'}
        }

        # Act
        transformer.execute(sample_data_state, sample_tasks, context=test_context)

        # Assert
        assert processor.context_received is not None
        assert processor.context_received == test_context
        assert 'previous_tasks' in processor.context_received
        assert 'session_id' in processor.context_received

    def test_none_context_handled(self, sample_data_state, sample_tasks):
        """Test 5b: None context is handled gracefully."""
        # Arrange
        processor = MockProcessor()
        transformer = BaseTransformer(processor)

        # Act
        transformer.execute(sample_data_state, sample_tasks, context=None)

        # Assert - should not raise error
        assert processor.context_received is None


class TestRealProcessorIntegration:
    """Test integration with real processors."""

    def test_uppercase_processor_integration(self, sample_data_state):
        """Test 7: Integration with UppercaseProcessor."""
        # Arrange
        processor = UppercaseProcessor()
        transformer = BaseTransformer(processor)

        tasks = pd.DataFrame({
            'task_id': ['U001', 'U002'],
            'operation': ['uppercase', 'uppercase'],
            'sheet_name': ['Sheet1', 'Sheet1'],
            'row_idx': [0, 1],
            'col_idx': [1, 1],
            'source_text': ['hello world', 'test data'],
            'status': ['pending', 'pending'],
            'result': ['', ''],
            'error_message': ['', ''],
            'updated_at': [datetime.now(), datetime.now()]
        })

        # Act
        new_state = transformer.execute(sample_data_state, tasks)

        # Assert
        assert all(tasks['status'] == 'completed')
        assert tasks.loc[0, 'result'] == 'HELLO WORLD'
        assert tasks.loc[1, 'result'] == 'TEST DATA'

        # Verify data state updated
        assert new_state.get_cell_value('Sheet1', 0, 1) == 'HELLO WORLD'
        assert new_state.get_cell_value('Sheet1', 1, 1) == 'TEST DATA'

    def test_uppercase_with_dependency_context(self, sample_data_state):
        """Test 7b: UppercaseProcessor with dependency context."""
        # Arrange
        processor = UppercaseProcessor()
        transformer = BaseTransformer(processor)

        # Create tasks with dependencies
        tasks = pd.DataFrame({
            'task_id': ['U001'],
            'operation': ['uppercase'],
            'sheet_name': ['Sheet1'],
            'row_idx': [0],
            'col_idx': [1],
            'source_text': ['original'],
            'depends_on': ['TRANS_001'],  # Depends on a translation task
            'status': ['pending'],
            'result': [''],
            'error_message': [''],
            'updated_at': [datetime.now()]
        })

        # Context with previous translation result
        context = {
            'previous_tasks': {
                'TRANS_001': {'result': 'translated text'}
            }
        }

        # Act
        new_state = transformer.execute(sample_data_state, tasks, context=context)

        # Assert
        # Should uppercase the translated result, not the original
        assert tasks.loc[0, 'result'] == 'TRANSLATED TEXT'
        assert new_state.get_cell_value('Sheet1', 0, 1) == 'TRANSLATED TEXT'


class TestValidation:
    """Test validation logic."""

    def test_validate_tasks_with_valid_data(self, sample_tasks):
        """Test 8: validate_tasks returns True for valid data."""
        # Arrange
        processor = MockProcessor()
        transformer = BaseTransformer(processor)

        # Act
        result = transformer.validate_tasks(sample_tasks)

        # Assert
        assert result is True

    def test_validate_tasks_with_none(self):
        """Test 8b: validate_tasks handles None."""
        # Arrange
        processor = MockProcessor()
        transformer = BaseTransformer(processor)

        # Act
        result = transformer.validate_tasks(None)

        # Assert
        assert result is False

    def test_validate_tasks_with_missing_columns(self):
        """Test 8c: validate_tasks detects missing columns."""
        # Arrange
        processor = MockProcessor()
        transformer = BaseTransformer(processor)

        # Create tasks missing required column
        incomplete_tasks = pd.DataFrame({
            'task_id': ['T001'],
            'operation': ['mock'],
            # Missing: sheet_name, row_idx, col_idx, source_text, status
        })

        # Act
        result = transformer.validate_tasks(incomplete_tasks)

        # Assert
        assert result is False

    def test_execute_raises_on_invalid_tasks(self, sample_data_state):
        """Test 8d: execute raises InvalidTaskError on invalid tasks."""
        # Arrange
        processor = MockProcessor()
        transformer = BaseTransformer(processor)
        invalid_tasks = None

        # Act & Assert
        with pytest.raises(InvalidTaskError):
            transformer.execute(sample_data_state, invalid_tasks)


class TestTransformerInterface:
    """Test Transformer abstract interface."""

    def test_get_processor_type(self):
        """Test get_processor_type returns correct type."""
        # Arrange
        processor = UppercaseProcessor()
        transformer = BaseTransformer(processor)

        # Act
        result = transformer.get_processor_type()

        # Assert
        assert result == 'uppercase'

    def test_repr_string(self):
        """Test __repr__ returns meaningful string."""
        # Arrange
        processor = MockProcessor()
        transformer = BaseTransformer(processor)

        # Act
        result = repr(transformer)

        # Assert
        assert 'BaseTransformer' in result
        assert 'MockProcessor' in result


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_source_text_handled(self, sample_data_state):
        """Test handling of empty source text."""
        # Arrange
        processor = UppercaseProcessor()
        transformer = BaseTransformer(processor)

        tasks = pd.DataFrame({
            'task_id': ['E001'],
            'operation': ['uppercase'],
            'sheet_name': ['Sheet1'],
            'row_idx': [0],
            'col_idx': [1],
            'source_text': [''],  # Empty source
            'status': ['pending'],
            'result': [''],
            'error_message': [''],
            'updated_at': [datetime.now()]
        })

        # Act
        new_state = transformer.execute(sample_data_state, tasks)

        # Assert
        assert tasks.loc[0, 'status'] == 'completed'
        assert tasks.loc[0, 'result'] == ''

    def test_large_result_text(self, sample_data_state):
        """Test handling of large result text."""
        # Arrange
        large_text = "X" * 10000  # 10k characters
        processor = MockProcessor(return_value=large_text)
        transformer = BaseTransformer(processor)

        tasks = pd.DataFrame({
            'task_id': ['L001'],
            'operation': ['mock'],
            'sheet_name': ['Sheet1'],
            'row_idx': [0],
            'col_idx': [1],
            'source_text': ['test'],
            'status': ['pending'],
            'result': [''],
            'error_message': [''],
            'updated_at': [datetime.now()]
        })

        # Act
        new_state = transformer.execute(sample_data_state, tasks)

        # Assert
        assert tasks.loc[0, 'status'] == 'completed'
        assert len(tasks.loc[0, 'result']) == 10000


# ============================================================================
# Performance Tests (Optional)
# ============================================================================

@pytest.mark.performance
class TestPerformance:
    """Optional performance tests."""

    def test_process_1000_tasks(self, sample_data_state):
        """Test 9: Process 1000 tasks performance."""
        # Arrange
        processor = MockProcessor(return_value="RESULT")
        transformer = BaseTransformer(processor)

        # Create 1000 tasks
        task_count = 1000
        tasks = pd.DataFrame({
            'task_id': [f'T{i:04d}' for i in range(task_count)],
            'operation': ['mock'] * task_count,
            'sheet_name': ['Sheet1'] * task_count,
            'row_idx': [i % 3 for i in range(task_count)],  # Cycle through 3 rows
            'col_idx': [1] * task_count,
            'source_text': [f'text_{i}' for i in range(task_count)],
            'status': ['pending'] * task_count,
            'result': [''] * task_count,
            'error_message': [''] * task_count,
            'updated_at': [datetime.now()] * task_count
        })

        # Act
        import time
        start = time.time()
        new_state = transformer.execute(sample_data_state, tasks)
        duration = time.time() - start

        # Assert
        assert all(tasks['status'] == 'completed')
        assert duration < 10.0  # Should complete in under 10 seconds
        print(f"\nProcessed {task_count} tasks in {duration:.2f}s "
              f"({task_count/duration:.0f} tasks/sec)")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
