"""Unit tests for NormalizeProcessor."""

import pytest
from services.processors.normalize_processor import NormalizeProcessor


class TestNormalizeProcessor:
    """Test suite for NormalizeProcessor."""

    def test_init(self):
        """Test processor initialization."""
        processor = NormalizeProcessor()
        assert processor is not None

    def test_get_operation_type(self):
        """Test operation type."""
        processor = NormalizeProcessor()
        assert processor.get_operation_type() == 'normalize'

    def test_process_chinese_comma(self):
        """Test converting Chinese comma to English comma."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '你好,世界'
        }
        result = processor.process(task)
        assert result == '你好,世界'

    def test_process_chinese_period(self):
        """Test converting Chinese period to English period."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '这是测试。'
        }
        result = processor.process(task)
        assert result == '这是测试.'

    def test_process_chinese_question_mark(self):
        """Test converting Chinese question mark."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '你好吗?'
        }
        result = processor.process(task)
        assert result == '你好吗?'

    def test_process_chinese_exclamation(self):
        """Test converting Chinese exclamation mark."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '太好了!'
        }
        result = processor.process(task)
        assert result == '太好了!'

    def test_process_chinese_parentheses(self):
        """Test converting Chinese parentheses."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '这是(测试)内容'
        }
        result = processor.process(task)
        assert result == '这是(测试)内容'

    def test_process_chinese_quotes(self):
        """Test converting Chinese quotes."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '"这是测试"内容'
        }
        result = processor.process(task)
        assert result == '"这是测试"内容'

    def test_process_chinese_single_quotes(self):
        """Test converting Chinese single quotes."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '\u2018测试\u2019'  # Chinese single quotes as unicode
        }
        result = processor.process(task)
        assert result == "'测试'"

    def test_process_angle_brackets(self):
        """Test converting Chinese angle brackets."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '《书名》'
        }
        result = processor.process(task)
        assert result == '<书名>'

    def test_process_ellipsis(self):
        """Test converting Chinese ellipsis."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '测试…继续'
        }
        result = processor.process(task)
        assert result == '测试...继续'

    def test_process_em_dash(self):
        """Test converting em dash."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '测试—继续'
        }
        result = processor.process(task)
        assert result == '测试-继续'

    def test_process_full_width_space(self):
        """Test converting full-width space."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '测试\u3000内容'
        }
        result = processor.process(task)
        assert result == '测试 内容'

    def test_process_multiple_punctuation(self):
        """Test converting multiple punctuation types."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '"你好,"他说。"这是测试!"'
        }
        result = processor.process(task)
        assert result == '"你好,"他说."这是测试!"'

    def test_process_mixed_content(self):
        """Test normalizing text with mixed Chinese and English."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': 'Hello,世界!这是测试。'
        }
        result = processor.process(task)
        assert result == 'Hello,世界!这是测试.'

    def test_process_no_chinese_punctuation(self):
        """Test text with no Chinese punctuation."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': 'Hello, world!'
        }
        result = processor.process(task)
        assert result == 'Hello, world!'

    def test_process_empty_string(self):
        """Test normalizing empty string."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': ''
        }
        result = processor.process(task)
        assert result == ''

    def test_process_colon_semicolon(self):
        """Test converting Chinese colon and semicolon."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '标题:内容;备注'
        }
        result = processor.process(task)
        assert result == '标题:内容;备注'

    def test_process_brackets(self):
        """Test converting Chinese brackets."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '[测试]内容{数据}'
        }
        result = processor.process(task)
        assert result == '[测试]内容{数据}'

    def test_process_middle_dot(self):
        """Test converting middle dot."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '名字·姓氏'
        }
        result = processor.process(task)
        assert result == '名字.姓氏'

    def test_process_with_context(self):
        """Test normalizing with context dependency."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': 'original',
            'depends_on': 'TRANS_001'
        }
        context = {
            'previous_tasks': {
                'TRANS_001': {
                    'task_id': 'TRANS_001',
                    'result': '你好,世界。'
                }
            }
        }
        result = processor.process(task, context)
        assert result == '你好,世界.'

    def test_validate_task_valid(self):
        """Test task validation with valid task."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': 'test'
        }
        assert processor.validate_task(task) is True

    def test_validate_task_invalid(self):
        """Test task validation with invalid task."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'wrong',
            'source_text': 'test'
        }
        assert processor.validate_task(task) is False

    def test_process_invalid_task_raises(self):
        """Test that invalid task raises ValueError."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'wrong_operation',
            'source_text': 'test'
        }
        with pytest.raises(ValueError):
            processor.process(task)

    def test_process_batch(self):
        """Test batch processing."""
        processor = NormalizeProcessor()
        tasks = [
            {'task_id': 'NORM_001', 'operation': 'normalize', 'source_text': '你好,世界。'},
            {'task_id': 'NORM_002', 'operation': 'normalize', 'source_text': '"测试"内容!'},
            {'task_id': 'NORM_003', 'operation': 'normalize', 'source_text': 'English text.'},
        ]
        results = processor.process_batch(tasks)
        assert len(results) == 3
        assert results[0] == '你好,世界.'
        assert results[1] == '"测试"内容!'
        assert results[2] == 'English text.'

    def test_process_complex_text(self):
        """Test normalizing complex text with multiple types of punctuation."""
        processor = NormalizeProcessor()
        task = {
            'task_id': 'NORM_001',
            'operation': 'normalize',
            'source_text': '他说:"你好,《世界》!"她回答:"好的…"(完成)'
        }
        result = processor.process(task)
        # All Chinese punctuation should be converted
        assert '\u201c' not in result  # Left double quote converted
        assert '\u201d' not in result  # Right double quote converted
        assert '《' not in result  # Left angle quote converted
        assert '》' not in result  # Right angle quote converted
        assert '…' not in result  # Ellipsis converted to three dots
        # Check expected conversions happened correctly
        assert '"' in result  # Converted to ASCII English quotes
        assert '<' in result and '>' in result  # Angle brackets converted
        assert '...' in result  # Ellipsis converted to three dots
        # Note: The source already contains standard ASCII parentheses, not full-width
        assert '(' in result and ')' in result  # Parentheses present

    def test_normalize_punctuation_map(self):
        """Test that PUNCTUATION_MAP contains expected mappings."""
        processor = NormalizeProcessor()
        # Check some key mappings
        assert ',' in processor.PUNCTUATION_MAP
        assert '。' in processor.PUNCTUATION_MAP
        assert '"' in processor.PUNCTUATION_MAP
        assert '"' in processor.PUNCTUATION_MAP
        assert '…' in processor.PUNCTUATION_MAP
        assert '\u3000' in processor.PUNCTUATION_MAP
