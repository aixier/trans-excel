"""Unit tests for UppercaseProcessor."""

import pytest
from services.processors.uppercase_processor import UppercaseProcessor


class TestUppercaseProcessor:
    """Test suite for UppercaseProcessor."""

    def test_init(self):
        """Test processor initialization."""
        processor = UppercaseProcessor()
        assert processor is not None

    def test_get_operation_type(self):
        """Test operation type."""
        processor = UppercaseProcessor()
        assert processor.get_operation_type() == 'uppercase'

    def test_process_simple(self):
        """Test basic uppercase processing."""
        processor = UppercaseProcessor()
        task = {
            'task_id': 'CAPS_001',
            'operation': 'uppercase',
            'source_text': 'hello world'
        }
        result = processor.process(task)
        assert result == 'HELLO WORLD'

    def test_process_mixed_case(self):
        """Test uppercase with mixed case input."""
        processor = UppercaseProcessor()
        task = {
            'task_id': 'CAPS_001',
            'operation': 'uppercase',
            'source_text': 'HeLLo WoRLd'
        }
        result = processor.process(task)
        assert result == 'HELLO WORLD'

    def test_process_already_uppercase(self):
        """Test uppercase with already uppercase text."""
        processor = UppercaseProcessor()
        task = {
            'task_id': 'CAPS_001',
            'operation': 'uppercase',
            'source_text': 'ALREADY UPPERCASE'
        }
        result = processor.process(task)
        assert result == 'ALREADY UPPERCASE'

    def test_process_with_numbers_and_symbols(self):
        """Test uppercase with numbers and symbols."""
        processor = UppercaseProcessor()
        task = {
            'task_id': 'CAPS_001',
            'operation': 'uppercase',
            'source_text': 'test123!@#'
        }
        result = processor.process(task)
        assert result == 'TEST123!@#'

    def test_process_unicode_text(self):
        """Test uppercase with Unicode text."""
        processor = UppercaseProcessor()

        # Thai text (no case conversion)
        task = {
            'task_id': 'CAPS_001',
            'operation': 'uppercase',
            'source_text': 'สวัสดี'
        }
        result = processor.process(task)
        assert result == 'สวัสดี'  # Thai has no uppercase

        # Chinese text (no case conversion)
        task = {
            'task_id': 'CAPS_002',
            'operation': 'uppercase',
            'source_text': '你好世界'
        }
        result = processor.process(task)
        assert result == '你好世界'  # Chinese has no uppercase

    def test_process_mixed_language(self):
        """Test uppercase with mixed English and non-English text."""
        processor = UppercaseProcessor()
        task = {
            'task_id': 'CAPS_001',
            'operation': 'uppercase',
            'source_text': 'hello 你好 world'
        }
        result = processor.process(task)
        assert result == 'HELLO 你好 WORLD'

    def test_process_empty_string(self):
        """Test uppercase with empty string."""
        processor = UppercaseProcessor()
        task = {
            'task_id': 'CAPS_001',
            'operation': 'uppercase',
            'source_text': ''
        }
        result = processor.process(task)
        assert result == ''

    def test_process_with_context_dependency(self):
        """Test uppercase using result from previous task."""
        processor = UppercaseProcessor()
        task = {
            'task_id': 'CAPS_001',
            'operation': 'uppercase',
            'source_text': 'original chinese',
            'depends_on': 'TRANS_001'
        }
        context = {
            'previous_tasks': {
                'TRANS_001': {
                    'task_id': 'TRANS_001',
                    'result': 'translated text'
                }
            }
        }
        result = processor.process(task, context)
        assert result == 'TRANSLATED TEXT'

    def test_process_context_missing_dependency(self):
        """Test uppercase when dependency is not in context."""
        processor = UppercaseProcessor()
        task = {
            'task_id': 'CAPS_001',
            'operation': 'uppercase',
            'source_text': 'fallback text',
            'depends_on': 'TRANS_001'
        }
        context = {
            'previous_tasks': {
                'TRANS_002': {'result': 'other task'}
            }
        }
        result = processor.process(task, context)
        assert result == 'FALLBACK TEXT'

    def test_process_no_context(self):
        """Test uppercase without context."""
        processor = UppercaseProcessor()
        task = {
            'task_id': 'CAPS_001',
            'operation': 'uppercase',
            'source_text': 'no context',
            'depends_on': 'TRANS_001'
        }
        result = processor.process(task, None)
        assert result == 'NO CONTEXT'

    def test_validate_task_valid(self):
        """Test task validation with valid task."""
        processor = UppercaseProcessor()
        task = {
            'task_id': 'CAPS_001',
            'operation': 'uppercase',
            'source_text': 'test'
        }
        assert processor.validate_task(task) is True

    def test_validate_task_invalid(self):
        """Test task validation with invalid task."""
        processor = UppercaseProcessor()

        # Wrong operation
        task = {
            'task_id': 'CAPS_001',
            'operation': 'translate',
            'source_text': 'test'
        }
        assert processor.validate_task(task) is False

    def test_process_invalid_task_raises(self):
        """Test that invalid task raises ValueError."""
        processor = UppercaseProcessor()
        task = {
            'task_id': 'CAPS_001',
            'operation': 'wrong_operation',
            'source_text': 'test'
        }
        with pytest.raises(ValueError):
            processor.process(task)

    def test_process_batch(self):
        """Test batch processing."""
        processor = UppercaseProcessor()
        tasks = [
            {'task_id': 'CAPS_001', 'operation': 'uppercase', 'source_text': 'text one'},
            {'task_id': 'CAPS_002', 'operation': 'uppercase', 'source_text': 'text two'},
            {'task_id': 'CAPS_003', 'operation': 'uppercase', 'source_text': 'text three'},
        ]
        results = processor.process_batch(tasks)
        assert len(results) == 3
        assert results[0] == 'TEXT ONE'
        assert results[1] == 'TEXT TWO'
        assert results[2] == 'TEXT THREE'

    def test_process_batch_with_context(self):
        """Test batch processing with context dependencies."""
        processor = UppercaseProcessor()
        tasks = [
            {'task_id': 'CAPS_001', 'operation': 'uppercase', 'source_text': 'original1', 'depends_on': 'TRANS_001'},
            {'task_id': 'CAPS_002', 'operation': 'uppercase', 'source_text': 'original2', 'depends_on': 'TRANS_002'},
            {'task_id': 'CAPS_003', 'operation': 'uppercase', 'source_text': 'original3'},
        ]
        context = {
            'previous_tasks': {
                'TRANS_001': {'result': 'translated one'},
                'TRANS_002': {'result': 'translated two'}
            }
        }
        results = processor.process_batch(tasks, context)
        assert len(results) == 3
        assert results[0] == 'TRANSLATED ONE'
        assert results[1] == 'TRANSLATED TWO'
        assert results[2] == 'ORIGINAL3'

    def test_process_whitespace(self):
        """Test uppercase preserves whitespace."""
        processor = UppercaseProcessor()
        task = {
            'task_id': 'CAPS_001',
            'operation': 'uppercase',
            'source_text': '  hello   world  '
        }
        result = processor.process(task)
        assert result == '  HELLO   WORLD  '
