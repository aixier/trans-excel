"""Unit tests for LLMProcessor."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.processors.llm_processor import LLMProcessor
from services.llm.base_provider import (
    BaseLLMProvider,
    TranslationRequest,
    TranslationResponse,
    LLMConfig
)


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, config=None):
        if config is None:
            config = LLMConfig(provider='mock', api_key='test-key', model='mock-model')
        super().__init__(config)
        self.translate_single_called = False
        self.translate_batch_called = False

    async def translate_single(self, request: TranslationRequest) -> TranslationResponse:
        """Mock single translation."""
        self.translate_single_called = True
        return TranslationResponse(
            translated_text=f"Translated: {request.source_text}",
            confidence=0.9,
            token_usage={'prompt_tokens': 10, 'completion_tokens': 5},
            model='mock-model',
            duration_ms=100,
            task_id=request.task_id
        )

    async def translate_batch(self, requests):
        """Mock batch translation."""
        self.translate_batch_called = True
        responses = []
        for req in requests:
            responses.append(TranslationResponse(
                translated_text=f"Translated: {req.source_text}",
                confidence=0.9,
                token_usage={'prompt_tokens': 10, 'completion_tokens': 5},
                model='mock-model',
                duration_ms=100,
                task_id=req.task_id
            ))
        return responses

    async def health_check(self):
        """Mock health check."""
        return True


class TestLLMProcessor:
    """Test suite for LLMProcessor."""

    def test_init(self):
        """Test processor initialization."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)
        assert processor is not None
        assert processor.llm_provider is provider

    def test_get_operation_type(self):
        """Test operation type."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)
        assert processor.get_operation_type() == 'translate'

    def test_process_simple(self):
        """Test basic translation processing."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)

        task = {
            'task_id': 'TRANS_001',
            'operation': 'translate',
            'source_text': '你好世界',
            'source_lang': 'zh',
            'target_lang': 'en',
            'task_type': 'normal'
        }

        result = processor.process(task)
        assert result == 'Translated: 你好世界'
        assert provider.translate_single_called

    def test_process_with_context_text(self):
        """Test translation with context text."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)

        task = {
            'task_id': 'TRANS_001',
            'operation': 'translate',
            'source_text': '攻击',
            'source_lang': 'zh',
            'target_lang': 'en',
            'task_type': 'normal',
            'context_text': 'This is a game skill',
            'game_info': {'game_name': 'RPG Game'}
        }

        result = processor.process(task)
        assert 'Translated:' in result

    def test_process_empty_source_text(self):
        """Test translation with empty source text."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)

        task = {
            'task_id': 'TRANS_001',
            'operation': 'translate',
            'source_text': '',
            'source_lang': 'zh',
            'target_lang': 'en',
            'task_type': 'normal'
        }

        result = processor.process(task)
        assert result == ''

    def test_process_with_glossary(self):
        """Test translation with glossary configuration."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)

        task = {
            'task_id': 'TRANS_001',
            'operation': 'translate',
            'source_text': '技能',
            'source_lang': 'zh',
            'target_lang': 'en',
            'task_type': 'normal',
            'glossary_config': {
                'enabled': True,
                'terms': {'技能': 'Skill'}
            }
        }

        result = processor.process(task)
        assert result == 'Translated: 技能'

    def test_process_different_task_types(self):
        """Test translation with different task types."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)

        for task_type in ['normal', 'yellow', 'blue']:
            task = {
                'task_id': f'TRANS_{task_type}',
                'operation': 'translate',
                'source_text': '测试',
                'source_lang': 'zh',
                'target_lang': 'en',
                'task_type': task_type
            }

            result = processor.process(task)
            assert result == 'Translated: 测试'

    def test_process_with_context_dependency(self):
        """Test translation can use context dependencies."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)

        task = {
            'task_id': 'TRANS_002',
            'operation': 'translate',
            'source_text': 'original text',
            'source_lang': 'zh',
            'target_lang': 'en',
            'task_type': 'normal',
            'depends_on': 'TRANS_001'
        }

        context = {
            'previous_tasks': {
                'TRANS_001': {
                    'result': 'dependency result'
                }
            }
        }

        # Should translate the dependency result, not original text
        result = processor.process(task, context)
        assert result == 'Translated: dependency result'

    def test_validate_task_valid(self):
        """Test task validation with valid task."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)

        task = {
            'task_id': 'TRANS_001',
            'operation': 'translate',
            'source_text': 'test',
            'source_lang': 'zh',
            'target_lang': 'en'
        }

        assert processor.validate_task(task) is True

    def test_validate_task_missing_source_lang(self):
        """Test validation fails without source_lang."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)

        task = {
            'task_id': 'TRANS_001',
            'operation': 'translate',
            'source_text': 'test',
            'target_lang': 'en'
        }

        assert processor.validate_task(task) is False

    def test_validate_task_missing_target_lang(self):
        """Test validation fails without target_lang."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)

        task = {
            'task_id': 'TRANS_001',
            'operation': 'translate',
            'source_text': 'test',
            'source_lang': 'zh'
        }

        assert processor.validate_task(task) is False

    def test_process_invalid_task_raises(self):
        """Test that invalid task raises ValueError."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)

        task = {
            'task_id': 'TRANS_001',
            'operation': 'translate',
            'source_text': 'test'
            # Missing source_lang and target_lang
        }

        with pytest.raises(ValueError):
            processor.process(task)

    def test_process_batch(self):
        """Test batch translation processing."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)

        tasks = [
            {
                'task_id': 'TRANS_001',
                'operation': 'translate',
                'source_text': '你好',
                'source_lang': 'zh',
                'target_lang': 'en',
                'task_type': 'normal'
            },
            {
                'task_id': 'TRANS_002',
                'operation': 'translate',
                'source_text': '世界',
                'source_lang': 'zh',
                'target_lang': 'en',
                'task_type': 'normal'
            },
            {
                'task_id': 'TRANS_003',
                'operation': 'translate',
                'source_text': '测试',
                'source_lang': 'zh',
                'target_lang': 'en',
                'task_type': 'normal'
            }
        ]

        results = processor.process_batch(tasks)
        assert len(results) == 3
        assert results[0] == 'Translated: 你好'
        assert results[1] == 'Translated: 世界'
        assert results[2] == 'Translated: 测试'
        assert provider.translate_batch_called

    def test_process_batch_empty(self):
        """Test batch processing with empty task list."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)

        results = processor.process_batch([])
        assert results == []

    def test_process_batch_with_errors(self):
        """Test batch processing handles errors gracefully."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)

        tasks = [
            {
                'task_id': 'TRANS_001',
                'operation': 'translate',
                'source_text': '你好',
                'source_lang': 'zh',
                'target_lang': 'en',
                'task_type': 'normal'
            },
            {
                'task_id': 'TRANS_002',
                'operation': 'translate',
                'source_text': '世界',
                # Missing source_lang and target_lang - will fail validation
            },
            {
                'task_id': 'TRANS_003',
                'operation': 'translate',
                'source_text': '测试',
                'source_lang': 'zh',
                'target_lang': 'en',
                'task_type': 'normal'
            }
        ]

        results = processor.process_batch(tasks)
        assert len(results) == 3
        assert results[0] == 'Translated: 你好'
        assert results[1] == ''  # Error case
        assert results[2] == 'Translated: 测试'

    def test_build_translation_request(self):
        """Test building TranslationRequest from task."""
        provider = MockLLMProvider()
        processor = LLMProcessor(provider)

        task = {
            'task_id': 'TRANS_001',
            'operation': 'translate',
            'source_text': '你好',
            'source_lang': 'zh',
            'target_lang': 'en',
            'task_type': 'normal',
            'context_text': 'game context',
            'game_info': {'name': 'Test Game'},
            'batch_id': 'BATCH_01',
            'group_id': 'GROUP_01',
            'glossary_config': {'enabled': True}
        }

        request = processor._build_translation_request(task)

        assert isinstance(request, TranslationRequest)
        assert request.source_text == '你好'
        assert request.source_lang == 'zh'
        assert request.target_lang == 'en'
        assert request.task_type == 'normal'
        assert request.context == 'game context'
        assert request.game_info == {'name': 'Test Game'}
        assert request.task_id == 'TRANS_001'
        assert request.batch_id == 'BATCH_01'
        assert request.group_id == 'GROUP_01'
        assert request.glossary_config == {'enabled': True}

    def test_process_translation_error(self):
        """Test handling translation errors."""

        class ErrorLLMProvider(BaseLLMProvider):
            async def translate_single(self, request):
                return TranslationResponse(
                    translated_text='',
                    error='Translation failed',
                    task_id=request.task_id
                )

            async def translate_batch(self, requests):
                return []

            async def health_check(self):
                return False

        provider = ErrorLLMProvider(LLMConfig(provider='error', api_key='test'))
        processor = LLMProcessor(provider)

        task = {
            'task_id': 'TRANS_001',
            'operation': 'translate',
            'source_text': '你好',
            'source_lang': 'zh',
            'target_lang': 'en',
            'task_type': 'normal'
        }

        with pytest.raises(RuntimeError) as exc_info:
            processor.process(task)

        assert 'Translation error' in str(exc_info.value)

    def test_process_exception_handling(self):
        """Test exception handling during translation."""

        class ExceptionLLMProvider(BaseLLMProvider):
            async def translate_single(self, request):
                raise Exception("Network error")

            async def translate_batch(self, requests):
                raise Exception("Network error")

            async def health_check(self):
                return False

        provider = ExceptionLLMProvider(LLMConfig(provider='error', api_key='test'))
        processor = LLMProcessor(provider)

        task = {
            'task_id': 'TRANS_001',
            'operation': 'translate',
            'source_text': '你好',
            'source_lang': 'zh',
            'target_lang': 'en',
            'task_type': 'normal'
        }

        with pytest.raises(RuntimeError):
            processor.process(task)
