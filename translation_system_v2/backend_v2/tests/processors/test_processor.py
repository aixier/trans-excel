"""Unit tests for base Processor class."""

import pytest
from services.processors.processor import Processor


class ConcreteProcessor(Processor):
    """Concrete implementation for testing."""

    def get_operation_type(self) -> str:
        return 'test_operation'

    def process(self, task, context=None):
        source = self.get_source_text(task, context)
        return f"processed_{source}"


class TestProcessor:
    """Test suite for Processor base class."""

    def test_init(self):
        """Test processor initialization."""
        processor = ConcreteProcessor()
        assert processor is not None
        assert processor.logger is not None

    def test_get_operation_type(self):
        """Test get_operation_type method."""
        processor = ConcreteProcessor()
        assert processor.get_operation_type() == 'test_operation'

    def test_validate_task_valid(self):
        """Test validate_task with valid task."""
        processor = ConcreteProcessor()
        task = {
            'task_id': 'T001',
            'operation': 'test_operation',
            'source_text': 'test'
        }
        assert processor.validate_task(task) is True

    def test_validate_task_missing_fields(self):
        """Test validate_task with missing required fields."""
        processor = ConcreteProcessor()

        # Missing task_id
        task = {
            'operation': 'test_operation',
            'source_text': 'test'
        }
        assert processor.validate_task(task) is False

        # Missing operation
        task = {
            'task_id': 'T001',
            'source_text': 'test'
        }
        assert processor.validate_task(task) is False

        # Missing source_text
        task = {
            'task_id': 'T001',
            'operation': 'test_operation'
        }
        assert processor.validate_task(task) is False

    def test_validate_task_wrong_operation(self):
        """Test validate_task with wrong operation type."""
        processor = ConcreteProcessor()
        task = {
            'task_id': 'T001',
            'operation': 'wrong_operation',
            'source_text': 'test'
        }
        assert processor.validate_task(task) is False

    def test_get_source_text_from_task(self):
        """Test get_source_text from task itself."""
        processor = ConcreteProcessor()
        task = {
            'task_id': 'T001',
            'source_text': 'hello world'
        }
        result = processor.get_source_text(task)
        assert result == 'hello world'

    def test_get_source_text_from_context(self):
        """Test get_source_text from context dependency."""
        processor = ConcreteProcessor()
        task = {
            'task_id': 'T002',
            'source_text': 'original',
            'depends_on': 'T001'
        }
        context = {
            'previous_tasks': {
                'T001': {
                    'task_id': 'T001',
                    'result': 'dependency result'
                }
            }
        }
        result = processor.get_source_text(task, context)
        assert result == 'dependency result'

    def test_get_source_text_dependency_not_found(self):
        """Test get_source_text when dependency is not in context."""
        processor = ConcreteProcessor()
        task = {
            'task_id': 'T002',
            'source_text': 'fallback',
            'depends_on': 'T001'
        }
        context = {
            'previous_tasks': {
                'T003': {'result': 'other task'}
            }
        }
        result = processor.get_source_text(task, context)
        assert result == 'fallback'

    def test_get_source_text_no_context(self):
        """Test get_source_text with dependency but no context."""
        processor = ConcreteProcessor()
        task = {
            'task_id': 'T002',
            'source_text': 'fallback',
            'depends_on': 'T001'
        }
        result = processor.get_source_text(task, None)
        assert result == 'fallback'

    def test_get_source_text_empty_result(self):
        """Test get_source_text when dependency has empty result."""
        processor = ConcreteProcessor()
        task = {
            'task_id': 'T002',
            'source_text': 'fallback',
            'depends_on': 'T001'
        }
        context = {
            'previous_tasks': {
                'T001': {'result': ''}
            }
        }
        result = processor.get_source_text(task, context)
        assert result == 'fallback'

    def test_process_batch_default(self):
        """Test default process_batch implementation."""
        processor = ConcreteProcessor()
        tasks = [
            {'task_id': 'T001', 'operation': 'test_operation', 'source_text': 'text1'},
            {'task_id': 'T002', 'operation': 'test_operation', 'source_text': 'text2'},
            {'task_id': 'T003', 'operation': 'test_operation', 'source_text': 'text3'},
        ]
        results = processor.process_batch(tasks)
        assert len(results) == 3
        assert results[0] == 'processed_text1'
        assert results[1] == 'processed_text2'
        assert results[2] == 'processed_text3'

    def test_process_batch_with_context(self):
        """Test process_batch with context."""
        processor = ConcreteProcessor()
        tasks = [
            {'task_id': 'T002', 'operation': 'test_operation', 'source_text': 'text1', 'depends_on': 'T001'},
            {'task_id': 'T003', 'operation': 'test_operation', 'source_text': 'text2', 'depends_on': 'T001'},
        ]
        context = {
            'previous_tasks': {
                'T001': {'result': 'dependency'}
            }
        }
        results = processor.process_batch(tasks, context)
        assert len(results) == 2
        assert results[0] == 'processed_dependency'
        assert results[1] == 'processed_dependency'

    def test_process_batch_error_handling(self):
        """Test process_batch handles errors gracefully."""
        class ErrorProcessor(Processor):
            def get_operation_type(self):
                return 'error'

            def process(self, task, context=None):
                if task['task_id'] == 'T002':
                    raise RuntimeError("Processing error")
                return "success"

        processor = ErrorProcessor()
        tasks = [
            {'task_id': 'T001', 'operation': 'error', 'source_text': 'text1'},
            {'task_id': 'T002', 'operation': 'error', 'source_text': 'text2'},
            {'task_id': 'T003', 'operation': 'error', 'source_text': 'text3'},
        ]
        results = processor.process_batch(tasks)
        assert len(results) == 3
        assert results[0] == 'success'
        assert results[1] == ''  # Error returns empty string
        assert results[2] == 'success'

    def test_repr(self):
        """Test string representation."""
        processor = ConcreteProcessor()
        repr_str = repr(processor)
        assert 'ConcreteProcessor' in repr_str
        assert 'test_operation' in repr_str
