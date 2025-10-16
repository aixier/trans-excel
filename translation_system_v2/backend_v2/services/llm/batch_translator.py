"""Batch translator for optimized LLM calls."""

import json
import logging
from typing import List, Dict, Any, Optional
import asyncio
from dataclasses import dataclass

from .base_provider import BaseLLMProvider, TranslationRequest, TranslationResponse

logger = logging.getLogger(__name__)


@dataclass
class BatchTranslationRequest:
    """Batch translation request containing multiple tasks."""
    tasks: List[Dict[str, Any]]
    batch_id: str
    target_lang: str
    game_context: Dict[str, Any]


class BatchTranslator:
    """Optimized batch translator that processes multiple tasks in one LLM call."""

    def __init__(self, provider: BaseLLMProvider, batch_size: int = 5):
        """
        Initialize batch translator.

        Args:
            provider: LLM provider instance
            batch_size: Number of tasks to process in one request
        """
        self.provider = provider
        self.batch_size = batch_size
        self.logger = logging.getLogger(self.__class__.__name__)

    async def translate_batch_optimized(
        self,
        tasks: List[Dict[str, Any]],
        glossary_config: Dict[str, Any] = None  # ✨ Glossary configuration
    ) -> List[Dict[str, Any]]:
        """
        Optimized batch translation that processes multiple tasks in fewer LLM calls.

        Args:
            tasks: List of translation tasks
            glossary_config: Glossary configuration

        Returns:
            List of tasks with translation results
        """
        if not tasks:
            return []

        # Group tasks by target language
        grouped_tasks = self._group_by_language(tasks)

        # Process each language group
        all_results = []
        for target_lang, lang_tasks in grouped_tasks.items():
            # Split into smaller batches
            batches = self._split_into_batches(lang_tasks, self.batch_size)

            # Process batches concurrently
            batch_results = await asyncio.gather(
                *[self._process_single_batch(batch, target_lang, glossary_config) for batch in batches],
                return_exceptions=True
            )

            # Flatten results
            for batch_result in batch_results:
                if isinstance(batch_result, Exception):
                    self.logger.error(f"Batch processing failed: {batch_result}")
                    # Mark tasks as failed
                    for task in lang_tasks:
                        task['status'] = 'failed'
                        task['error_message'] = str(batch_result)
                    all_results.extend(lang_tasks)
                else:
                    all_results.extend(batch_result)

        return all_results

    def _group_by_language(self, tasks: List[Dict]) -> Dict[str, List[Dict]]:
        """Group tasks by target language."""
        grouped = {}
        for task in tasks:
            lang = task.get('target_lang', 'PT')
            if lang not in grouped:
                grouped[lang] = []
            grouped[lang].append(task)
        return grouped

    def _split_into_batches(self, tasks: List[Dict], batch_size: int) -> List[List[Dict]]:
        """Split tasks into smaller batches."""
        batches = []
        for i in range(0, len(tasks), batch_size):
            batches.append(tasks[i:i + batch_size])
        return batches

    async def _process_single_batch(
        self,
        batch_tasks: List[Dict],
        target_lang: str,
        glossary_config: Dict[str, Any] = None  # ✨ Glossary configuration
    ) -> List[Dict]:
        """
        Process a single batch of tasks with one LLM call.

        Args:
            batch_tasks: Tasks to process together
            target_lang: Target language

        Returns:
            Tasks with translation results
        """
        try:
            # Build combined prompt
            combined_prompt = self._build_batch_prompt(batch_tasks, target_lang)

            # Create a single translation request
            # 注意：批量翻译时使用统一的task_type，优先级：blue > yellow > normal
            batch_task_type = self._determine_batch_task_type(batch_tasks)
            translation_request = TranslationRequest(
                source_text=combined_prompt,
                source_lang=batch_tasks[0].get('source_lang', 'CH'),
                target_lang=target_lang,
                context=self._extract_context(batch_tasks),
                game_info=batch_tasks[0].get('game_context', {}),
                task_type=batch_task_type,
                glossary_config=glossary_config  # ✨ Pass glossary config
            )

            # Call LLM once for all tasks
            start_time = asyncio.get_event_loop().time()
            response = await self.provider.translate_single(translation_request)
            duration_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)

            # Parse batch response
            translated_texts = self._parse_batch_response(response.translated_text, len(batch_tasks))

            # Update each task with results
            for i, task in enumerate(batch_tasks):
                if i < len(translated_texts):
                    task['result'] = translated_texts[i]
                    task['status'] = 'completed'
                    task['confidence'] = response.confidence
                    task['duration_ms'] = duration_ms // len(batch_tasks)  # Average duration
                    task['token_count'] = response.token_usage.get('total_tokens', 0) // len(batch_tasks)
                    task['llm_model'] = response.model
                else:
                    task['status'] = 'failed'
                    task['error_message'] = 'Failed to parse translation result'

            return batch_tasks

        except Exception as e:
            self.logger.error(f"Batch translation failed: {str(e)}")
            # Mark all tasks as failed
            for task in batch_tasks:
                task['status'] = 'failed'
                task['error_message'] = str(e)
            return batch_tasks

    def _build_batch_prompt(self, tasks: List[Dict], target_lang: str) -> str:
        """
        Build a combined prompt for multiple tasks.

        Format:
        Translate the following texts to {target_lang}:
        1. [Text 1]
        2. [Text 2]
        ...

        Return format: JSON array of translations
        """
        prompt_lines = [
            f"Translate the following {len(tasks)} game texts to {target_lang}.",
            "Maintain consistency and game terminology.",
            "Return ONLY a JSON array with translations in the same order.",
            "",
            "Texts to translate:"
        ]

        for i, task in enumerate(tasks, 1):
            source_text = task.get('source_text', '')
            prompt_lines.append(f"{i}. {source_text}")

        prompt_lines.extend([
            "",
            "Expected format: [\"translation1\", \"translation2\", ...]"
        ])

        return '\n'.join(prompt_lines)

    def _determine_batch_task_type(self, tasks: List[Dict]) -> str:
        """
        Determine the task type for a batch.
        Priority: blue > yellow > normal (最严格的任务类型优先)
        """
        task_types = [task.get('task_type', 'normal') for task in tasks]

        if 'blue' in task_types:
            return 'blue'    # 有缩短任务，使用蓝色模式
        elif 'yellow' in task_types:
            return 'yellow'  # 有重译任务，使用黄色模式
        else:
            return 'normal'  # 全部为普通任务

    def _parse_batch_response(self, response_text: str, expected_count: int) -> List[str]:
        """
        Parse batch response to extract individual translations.

        Args:
            response_text: LLM response containing multiple translations
            expected_count: Expected number of translations

        Returns:
            List of translated texts
        """
        try:
            # Try to parse as JSON array
            if response_text.strip().startswith('['):
                translations = json.loads(response_text)
                if isinstance(translations, list):
                    return translations[:expected_count]

            # Fallback: Split by newlines and numbers
            lines = response_text.strip().split('\n')
            translations = []
            for line in lines:
                # Remove numbering like "1. ", "2. ", etc.
                import re
                cleaned = re.sub(r'^\d+\.\s*', '', line.strip())
                if cleaned and not cleaned.startswith('['):
                    translations.append(cleaned)

            return translations[:expected_count]

        except Exception as e:
            self.logger.warning(f"Failed to parse batch response: {e}")
            # Return original text split by lines as fallback
            return response_text.strip().split('\n')[:expected_count]

    def _extract_context(self, tasks: List[Dict]) -> str:
        """Extract combined context from tasks."""
        contexts = []
        for task in tasks:
            if task.get('source_context'):
                contexts.append(task['source_context'])
        return ' | '.join(contexts[:3])  # Limit context size

    async def get_optimal_batch_size(self) -> int:
        """
        Determine optimal batch size based on provider capabilities.

        Returns:
            Optimal batch size
        """
        # Could be enhanced with dynamic adjustment based on response times
        return self.batch_size