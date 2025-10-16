"""LLM processor for translation tasks.

This processor wraps existing LLM providers for translation operations.
It serves as an adapter between the processor interface and LLM providers.
"""

from typing import Dict, Any, Optional, List
import asyncio
from .processor import Processor
from ..llm.base_provider import BaseLLMProvider, TranslationRequest, TranslationResponse


class LLMProcessor(Processor):
    """Processor that performs LLM-based translation.

    This is a wrapper around existing LLM providers (QwenProvider, OpenAIProvider, etc.)
    It adapts the processor interface to work with LLM translation providers.

    Architecture:
    - Does NOT modify existing LLM provider code
    - Acts as an adapter between Processor and BaseLLMProvider
    - Handles async/sync conversion
    - Manages translation request/response conversion

    Use cases:
    - Normal translation tasks
    - Yellow cell retranslation
    - Blue cell shortened translation
    - Context-aware translation

    Example:
        >>> from services.llm.qwen_provider import QwenProvider
        >>> from services.llm.base_provider import LLMConfig
        >>>
        >>> config = LLMConfig(
        ...     provider='qwen',
        ...     api_key='your-key',
        ...     model='qwen-plus'
        ... )
        >>> llm_provider = QwenProvider(config)
        >>> processor = LLMProcessor(llm_provider)
        >>>
        >>> task = {
        ...     'task_id': 'TRANS_001',
        ...     'operation': 'translate',
        ...     'source_text': '你好世界',
        ...     'source_lang': 'zh',
        ...     'target_lang': 'en',
        ...     'task_type': 'normal'
        ... }
        >>> result = processor.process(task)
        >>> print(result)
        'Hello World'
    """

    def __init__(self, llm_provider: BaseLLMProvider):
        """Initialize LLM processor.

        Args:
            llm_provider: An instance of BaseLLMProvider (QwenProvider, OpenAIProvider, etc.)
        """
        super().__init__()
        self.llm_provider = llm_provider

    def get_operation_type(self) -> str:
        """Return the operation type.

        Returns:
            str: 'translate'
        """
        return 'translate'

    def process(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Translate text using LLM provider.

        Args:
            task: Task dictionary containing:
                - task_id: Task identifier
                - operation: Must be 'translate'
                - source_text: Text to translate
                - source_lang: Source language code (e.g., 'zh', 'en')
                - target_lang: Target language code
                - task_type: Task type ('normal', 'yellow', 'blue')
                - context_text: Optional context for translation
                - game_info: Optional game information
                - glossary_config: Optional glossary configuration

            context: Optional context containing:
                - previous_tasks: Results from previous stages
                - data_state: Current data state
                - Other context data

        Returns:
            str: Translated text

        Raises:
            ValueError: If task validation fails
            RuntimeError: If translation fails

        Processing logic:
            1. Validate task data
            2. Build TranslationRequest from task
            3. Call LLM provider's translate_single method
            4. Extract and return translated text

        Note:
            - Handles async LLM calls via asyncio.run()
            - Preserves error information in logs
            - Returns empty string on failure (caller handles retry)
        """
        # Validate task
        if not self.validate_task(task):
            raise ValueError(f"Invalid task data for translation: {task.get('task_id')}")

        # Get source text
        source_text = self.get_source_text(task, context)
        if not source_text:
            self.logger.warning(
                f"Task {task.get('task_id')} has empty source text, skipping translation"
            )
            return ""

        # Build translation request
        request = self._build_translation_request(task, context)

        # Perform translation (handle async)
        try:
            # Handle async call properly in both sync and async contexts
            response = self._run_async_translation(request)

            if response.error:
                self.logger.error(
                    f"Translation failed for task {task.get('task_id')}: {response.error}"
                )
                raise RuntimeError(f"Translation error: {response.error}")

            self.logger.debug(
                f"Translated task {task.get('task_id')}: "
                f"'{source_text[:50]}...' -> '{response.translated_text[:50]}...' "
                f"(tokens: {response.token_usage}, duration: {response.duration_ms}ms)"
            )

            return response.translated_text

        except Exception as e:
            self.logger.error(
                f"Failed to translate task {task.get('task_id')}: {e}",
                exc_info=True
            )
            raise RuntimeError(f"Translation failed: {e}") from e

    def _run_async_translation(self, request):
        """Run async translation, handling both sync and async contexts.

        Args:
            request: TranslationRequest object

        Returns:
            TranslationResponse object
        """
        try:
            # Try to get running event loop
            loop = asyncio.get_running_loop()
            # If we're in a running loop (e.g., FastAPI async endpoint),
            # we need to run the async function in a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    self.llm_provider.translate_single(request)
                )
                return future.result()
        except RuntimeError:
            # No running loop, we can use asyncio.run() directly
            return asyncio.run(self.llm_provider.translate_single(request))

    def _build_translation_request(
        self,
        task: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> TranslationRequest:
        """Build TranslationRequest from task data.

        Args:
            task: Task dictionary
            context: Optional context

        Returns:
            TranslationRequest: Request object for LLM provider
        """
        # Get source text
        source_text = self.get_source_text(task, context)

        # Build request
        request = TranslationRequest(
            source_text=source_text,
            source_lang=task.get('source_lang', 'zh'),
            target_lang=task.get('target_lang', 'en'),
            context=task.get('context_text', ''),
            game_info=task.get('game_info', {}),
            task_type=task.get('task_type', 'normal'),
            task_id=task.get('task_id'),
            batch_id=task.get('batch_id'),
            group_id=task.get('group_id'),
            glossary_config=task.get('glossary_config'),
        )

        return request

    def process_batch(
        self,
        tasks: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Process multiple translation tasks in batch.

        This method leverages the LLM provider's batch translation capability
        for improved performance.

        Args:
            tasks: List of translation tasks
            context: Optional context

        Returns:
            List[str]: List of translated texts

        Note:
            - Uses LLM provider's translate_batch for efficiency
            - Maintains order of results
            - Handles errors per task
        """
        if not tasks:
            return []

        # Build batch requests
        requests = []
        for task in tasks:
            try:
                # Validate task before building request
                if not self.validate_task(task):
                    self.logger.warning(
                        f"Skipping invalid task {task.get('task_id')} in batch"
                    )
                    requests.append(None)
                    continue

                request = self._build_translation_request(task, context)
                requests.append(request)
            except Exception as e:
                self.logger.error(
                    f"Failed to build request for task {task.get('task_id')}: {e}"
                )
                # Add placeholder request to maintain order
                requests.append(None)

        # Perform batch translation
        try:
            # Filter out None requests
            valid_requests = [r for r in requests if r is not None]
            valid_indices = [i for i, r in enumerate(requests) if r is not None]

            if not valid_requests:
                return [""] * len(tasks)

            # Call batch translation (handle async properly)
            try:
                loop = asyncio.get_running_loop()
                # In running loop, use thread pool
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.llm_provider.translate_batch(valid_requests)
                    )
                    responses = future.result()
            except RuntimeError:
                # No running loop
                responses = asyncio.run(self.llm_provider.translate_batch(valid_requests))

            # Build result list
            results = [""] * len(tasks)
            for idx, response in zip(valid_indices, responses):
                if response.error:
                    self.logger.error(
                        f"Batch translation failed for task {tasks[idx].get('task_id')}: "
                        f"{response.error}"
                    )
                    results[idx] = ""
                else:
                    results[idx] = response.translated_text

            self.logger.info(
                f"Batch translated {len(valid_requests)} tasks, "
                f"{sum(1 for r in results if r)} successful"
            )

            return results

        except Exception as e:
            self.logger.error(f"Batch translation failed: {e}", exc_info=True)
            # Fall back to individual processing
            self.logger.warning("Falling back to individual translation")
            return super().process_batch(tasks, context)

    def validate_task(self, task: Dict[str, Any]) -> bool:
        """Validate translation task data.

        Args:
            task: Task dictionary to validate

        Returns:
            bool: True if valid, False otherwise
        """
        # Call parent validation
        if not super().validate_task(task):
            return False

        # Check translation-specific fields
        required_fields = ['source_lang', 'target_lang']

        for field in required_fields:
            if field not in task:
                self.logger.warning(
                    f"Translation task {task.get('task_id')} missing required field: {field}"
                )
                return False

        return True
