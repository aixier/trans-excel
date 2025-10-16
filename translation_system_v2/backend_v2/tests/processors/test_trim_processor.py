"""Unit tests for TrimProcessor."""

import pytest
from services.processors.trim_processor import TrimProcessor


class TestTrimProcessor:
    """Test suite for TrimProcessor."""

    def test_init(self):
        """Test processor initialization."""
        processor = TrimProcessor()
        assert processor is not None

    def test_get_operation_type(self):
        """Test operation type."""
        processor = TrimProcessor()
        assert processor.get_operation_type() == 'trim'

    def test_process_leading_whitespace(self):
        """Test trimming leading whitespace."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': '   hello world'
        }
        result = processor.process(task)
        assert result == 'hello world'

    def test_process_trailing_whitespace(self):
        """Test trimming trailing whitespace."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': 'hello world   '
        }
        result = processor.process(task)
        assert result == 'hello world'

    def test_process_both_ends(self):
        """Test trimming both leading and trailing whitespace."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': '   hello world   '
        }
        result = processor.process(task)
        assert result == 'hello world'

    def test_process_no_whitespace(self):
        """Test text with no whitespace to trim."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': 'hello world'
        }
        result = processor.process(task)
        assert result == 'hello world'

    def test_process_internal_whitespace_preserved(self):
        """Test that internal whitespace is preserved."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': '  hello   world  '
        }
        result = processor.process(task)
        assert result == 'hello   world'

    def test_process_newlines(self):
        """Test trimming newlines."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': '\nhello world\n'
        }
        result = processor.process(task)
        assert result == 'hello world'

    def test_process_tabs(self):
        """Test trimming tabs."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': '\thello world\t'
        }
        result = processor.process(task)
        assert result == 'hello world'

    def test_process_mixed_whitespace(self):
        """Test trimming mixed whitespace characters."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': ' \t\n hello world \n\t '
        }
        result = processor.process(task)
        assert result == 'hello world'

    def test_process_unicode_whitespace(self):
        """Test trimming Unicode whitespace."""
        processor = TrimProcessor()
        # Full-width space (U+3000)
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': '\u3000你好世界\u3000'
        }
        result = processor.process(task)
        assert result == '你好世界'

    def test_process_empty_string(self):
        """Test trimming empty string."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': ''
        }
        result = processor.process(task)
        assert result == ''

    def test_process_only_whitespace(self):
        """Test text that is only whitespace."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': '    '
        }
        result = processor.process(task)
        assert result == ''

    def test_process_none_source_text(self):
        """Test handling None source text."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': None
        }
        result = processor.process(task)
        assert result == ''

    def test_process_with_context(self):
        """Test trimming with context dependency."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': 'original',
            'depends_on': 'TRANS_001'
        }
        context = {
            'previous_tasks': {
                'TRANS_001': {
                    'task_id': 'TRANS_001',
                    'result': '  translated text  '
                }
            }
        }
        result = processor.process(task, context)
        assert result == 'translated text'

    def test_validate_task_valid(self):
        """Test task validation with valid task."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': 'test'
        }
        assert processor.validate_task(task) is True

    def test_validate_task_invalid(self):
        """Test task validation with invalid task."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'wrong',
            'source_text': 'test'
        }
        assert processor.validate_task(task) is False

    def test_process_invalid_task_raises(self):
        """Test that invalid task raises ValueError."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'wrong_operation',
            'source_text': 'test'
        }
        with pytest.raises(ValueError):
            processor.process(task)

    def test_process_batch(self):
        """Test batch processing."""
        processor = TrimProcessor()
        tasks = [
            {'task_id': 'TRIM_001', 'operation': 'trim', 'source_text': '  text one  '},
            {'task_id': 'TRIM_002', 'operation': 'trim', 'source_text': '\ttext two\n'},
            {'task_id': 'TRIM_003', 'operation': 'trim', 'source_text': 'text three'},
        ]
        results = processor.process_batch(tasks)
        assert len(results) == 3
        assert results[0] == 'text one'
        assert results[1] == 'text two'
        assert results[2] == 'text three'

    def test_process_multiline_text(self):
        """Test trimming multiline text."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': '\nLine 1\nLine 2\nLine 3\n'
        }
        result = processor.process(task)
        assert result == 'Line 1\nLine 2\nLine 3'
        # Internal newlines are preserved

    def test_process_unicode_text(self):
        """Test trimming Unicode text."""
        processor = TrimProcessor()
        task = {
            'task_id': 'TRIM_001',
            'operation': 'trim',
            'source_text': '  สวัสดี你好world  '
        }
        result = processor.process(task)
        assert result == 'สวัสดี你好world'
