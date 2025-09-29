"""Batch executor for translation tasks."""

import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from services.llm.base_provider import (
    BaseLLMProvider,
    TranslationRequest,
    TranslationResponse
)
from services.llm.batch_translator import BatchTranslator
from models.task_dataframe import TaskDataFrameManager, TaskStatus

logger = logging.getLogger(__name__)


class BatchExecutor:
    """Execute translation tasks in batches."""

    def __init__(self, llm_provider: BaseLLMProvider, use_batch_optimization: bool = True):
        """
        Initialize batch executor.

        Args:
            llm_provider: LLM provider instance
            use_batch_optimization: Whether to use batch translation optimization
        """
        self.llm_provider = llm_provider
        self.use_batch_optimization = use_batch_optimization
        if use_batch_optimization:
            self.batch_translator = BatchTranslator(llm_provider, batch_size=5)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def execute_batch(
        self,
        batch_id: str,
        tasks: List[Dict[str, Any]],
        task_manager: TaskDataFrameManager,
        game_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a batch of translation tasks.

        Args:
            batch_id: Batch identifier
            tasks: List of task dictionaries
            task_manager: Task DataFrame manager
            game_info: Game information

        Returns:
            Batch execution result
        """
        start_time = time.time()
        self.logger.info(f"Starting batch {batch_id} with {len(tasks)} tasks")

        # Update tasks to processing status
        for task in tasks:
            task_manager.update_task(
                task['task_id'],
                {
                    'status': TaskStatus.PROCESSING,
                    'start_time': datetime.now()
                }
            )

        # Prepare translation requests
        requests = self._prepare_requests(tasks, game_info)

        # Execute translations
        results = {
            'batch_id': batch_id,
            'total_tasks': len(tasks),
            'successful': 0,
            'failed': 0,
            'total_tokens': 0,
            'total_cost': 0.0
        }

        try:
            if self.use_batch_optimization:
                # Use optimized batch translator
                translated_tasks = await self.batch_translator.translate_batch_optimized(tasks)

                # Process translated tasks
                for task in translated_tasks:
                    if task.get('status') == 'completed':
                        task_manager.update_task(
                            task['task_id'],
                            {
                                'status': TaskStatus.COMPLETED,
                                'result': task.get('result'),
                                'confidence': task.get('confidence', 0.7),
                                'end_time': datetime.now(),
                                'duration_ms': task.get('duration_ms', 0),
                                'token_count': task.get('token_count', 0),
                                'llm_model': task.get('llm_model', '')
                            }
                        )
                        results['successful'] += 1
                        results['total_tokens'] += task.get('token_count', 0)
                    else:
                        task_manager.update_task(
                            task['task_id'],
                            {
                                'status': TaskStatus.FAILED,
                                'error_message': task.get('error_message', 'Translation failed'),
                                'end_time': datetime.now()
                            }
                        )
                        results['failed'] += 1
            else:
                # Use original method
                responses = await self.llm_provider.translate_batch(requests)

                # Process responses
                for task, response in zip(tasks, responses):
                    await self._process_response(task, response, task_manager, results)

        except Exception as e:
            self.logger.error(f"Batch {batch_id} execution failed: {str(e)}")
            # Mark all tasks as failed
            for task in tasks:
                task_manager.update_task(
                    task['task_id'],
                    {
                        'status': TaskStatus.FAILED,
                        'error_message': str(e),
                        'end_time': datetime.now()
                    }
                )
            results['failed'] = len(tasks)

        # Calculate execution time
        results['duration_seconds'] = time.time() - start_time

        self.logger.info(
            f"Batch {batch_id} completed: "
            f"{results['successful']} successful, "
            f"{results['failed']} failed, "
            f"duration={results['duration_seconds']:.2f}s"
        )

        return results

    def _prepare_requests(
        self,
        tasks: List[Dict[str, Any]],
        game_info: Optional[Dict[str, Any]]
    ) -> List[TranslationRequest]:
        """Prepare translation requests from tasks."""
        requests = []

        for task in tasks:
            request = TranslationRequest(
                source_text=task['source_text'],
                source_lang=task['source_lang'],
                target_lang=task['target_lang'],
                context=task.get('source_context', ''),
                game_info=game_info or {},
                task_type=task.get('task_type', 'normal'),  # 传递任务类型
                task_id=task['task_id'],
                batch_id=task.get('batch_id'),
                group_id=task.get('group_id')
            )
            requests.append(request)

        return requests

    async def _process_response(
        self,
        task: Dict[str, Any],
        response: TranslationResponse,
        task_manager: TaskDataFrameManager,
        results: Dict[str, Any]
    ) -> None:
        """Process a single translation response."""
        try:
            if response.error:
                # Translation failed
                task_manager.update_task(
                    task['task_id'],
                    {
                        'status': TaskStatus.FAILED,
                        'error_message': response.error,
                        'end_time': datetime.now(),
                        'duration_ms': response.duration_ms
                    }
                )
                results['failed'] += 1
                self.logger.warning(f"Task {task['task_id']} failed: {response.error}")

            else:
                # Translation successful
                task_manager.update_task(
                    task['task_id'],
                    {
                        'status': TaskStatus.COMPLETED,
                        'result': response.translated_text,
                        'confidence': response.confidence,
                        'end_time': datetime.now(),
                        'duration_ms': response.duration_ms,
                        'llm_model': response.model,
                        'token_count': response.token_usage.get('total_tokens', 0),
                        'is_final': True
                    }
                )
                results['successful'] += 1

                # Update token usage
                results['total_tokens'] += response.token_usage.get('total_tokens', 0)

                # Estimate cost (rough estimate, adjust based on actual pricing)
                cost = self._estimate_cost(response.token_usage, response.model)
                results['total_cost'] += cost

                self.logger.debug(
                    f"Task {task['task_id']} completed: "
                    f"confidence={response.confidence:.2f}, "
                    f"tokens={response.token_usage.get('total_tokens', 0)}"
                )

        except Exception as e:
            self.logger.error(f"Error processing response for task {task['task_id']}: {str(e)}")
            task_manager.update_task(
                task['task_id'],
                {
                    'status': TaskStatus.FAILED,
                    'error_message': f"Response processing error: {str(e)}",
                    'end_time': datetime.now()
                }
            )
            results['failed'] += 1

    def _estimate_cost(self, token_usage: Dict[str, int], model: str) -> float:
        """
        Estimate cost based on token usage.

        This is a rough estimate. Actual costs depend on the model and provider.
        """
        total_tokens = token_usage.get('total_tokens', 0)

        # Rough cost estimates per 1000 tokens
        cost_per_1k = {
            'gpt-4': 0.03,
            'gpt-4-turbo': 0.01,
            'gpt-4-turbo-preview': 0.01,
            'gpt-3.5-turbo': 0.002,
            'qwen-max': 0.008,
            'qwen-plus': 0.004,
            'qwen-turbo': 0.002
        }

        # Find matching model
        model_cost = 0.01  # Default
        for model_name, cost in cost_per_1k.items():
            if model_name in model.lower():
                model_cost = cost
                break

        return (total_tokens / 1000) * model_cost


class RetryableBatchExecutor(BatchExecutor):
    """Batch executor with retry capability."""

    def __init__(self, llm_provider: BaseLLMProvider, max_retries: int = 3):
        """
        Initialize retryable batch executor.

        Args:
            llm_provider: LLM provider instance
            max_retries: Maximum retry attempts
        """
        super().__init__(llm_provider)
        self.max_retries = max_retries

    async def execute_batch(
        self,
        batch_id: str,
        tasks: List[Dict[str, Any]],
        task_manager: TaskDataFrameManager,
        game_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute batch with retry logic for failed tasks."""
        results = await super().execute_batch(batch_id, tasks, task_manager, game_info)

        # Collect failed tasks for retry
        failed_tasks = []
        for task in tasks:
            task_data = task_manager.get_task(task['task_id'])
            if task_data is not None and task_data['status'] == TaskStatus.FAILED:
                retry_count = task_data.get('retry_count', 0)
                if retry_count < self.max_retries:
                    failed_tasks.append(task)

        # Retry failed tasks
        if failed_tasks:
            self.logger.info(f"Retrying {len(failed_tasks)} failed tasks in batch {batch_id}")

            for task in failed_tasks:
                # Update retry count
                task_manager.update_task(
                    task['task_id'],
                    {'retry_count': task.get('retry_count', 0) + 1}
                )

            # Wait before retry
            await asyncio.sleep(5)

            # Execute retry
            retry_results = await super().execute_batch(
                f"{batch_id}_retry",
                failed_tasks,
                task_manager,
                game_info
            )

            # Update results
            results['successful'] += retry_results['successful']
            results['failed'] = retry_results['failed']  # Update with final failed count
            results['total_tokens'] += retry_results['total_tokens']
            results['total_cost'] += retry_results['total_cost']

        return results