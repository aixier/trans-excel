"""LLM batch executor with pipeline integration."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from services.llm.base_provider import BaseLLMProvider, TranslationRequest, TranslationResponse
from services.llm.batch_translator import BatchTranslator
from models.task_dataframe import TaskDataFrameManager, TaskStatus
from services.executor.pipeline import TaskPipelineConfig, task_pipeline_registry
from services.executor.post_processing import PostProcessor
from services.executor.progress_tracker import progress_tracker

logger = logging.getLogger(__name__)


class BatchExecutor:
    """Execute translation batches controlled by pipeline configurations."""

    def __init__(self, llm_provider: BaseLLMProvider, use_batch_optimization: bool = True):
        self.llm_provider = llm_provider
        self.use_batch_optimization = use_batch_optimization
        if use_batch_optimization:
            self.batch_translator = BatchTranslator(llm_provider, batch_size=5)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def execute_batch(
        self,
        batch_id: str,
        tasks: List[Dict],
        task_manager: TaskDataFrameManager,
        session_id: str | None = None,
        game_info: Optional[Dict] = None,
        glossary_config: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        start_time = time.time()
        self.logger.info("Starting batch %s with %s tasks", batch_id, len(tasks))

        pipeline_pairs = [
            (task, task_pipeline_registry.get(task.get('task_type')))
            for task in tasks
        ]

        # Mark all tasks as processing upfront
        for task, _ in pipeline_pairs:
            task_manager.update_task(
                task['task_id'],
                {'status': TaskStatus.PROCESSING, 'start_time': datetime.now()}
            )

            if session_id:
                await progress_tracker.update_task_progress(
                    session_id,
                    task['task_id'],
                    TaskStatus.PROCESSING
                )

        llm_pairs = [(task, cfg) for task, cfg in pipeline_pairs if cfg.requires_llm]
        direct_pairs = [(task, cfg) for task, cfg in pipeline_pairs if not cfg.requires_llm]

        results = {
            'batch_id': batch_id,
            'total_tasks': len(tasks),
            'successful': 0,
            'failed': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
        }

        if llm_pairs:
            llm_tasks = [task for task, _ in llm_pairs]
            pipeline_map = {task['task_id']: cfg for task, cfg in llm_pairs}

            try:
                requests = self._prepare_requests(llm_tasks, game_info, glossary_config)

                if self.use_batch_optimization:
                    translated = await self.batch_translator.translate_batch_optimized(
                        llm_tasks,
                        glossary_config=glossary_config,
                    )

                    for task in translated:
                        cfg = pipeline_map.get(task['task_id'])
                        await self._handle_llm_task(task, cfg, task_manager, results, session_id)
                else:
                    responses = await self.llm_provider.translate_batch(requests)
                    for task, response in zip(llm_tasks, responses):
                        cfg = pipeline_map.get(task['task_id'])
                        await self._process_response(task, cfg, response, task_manager, results)

            except Exception as exc:
                self.logger.exception("Batch %s LLM execution failed", batch_id)
                for task, _ in llm_pairs:
                    task_manager.update_task(
                        task['task_id'],
                        {
                            'status': TaskStatus.FAILED,
                            'error_message': str(exc),
                            'end_time': datetime.now(),
                        },
                    )
                results['failed'] += len(llm_pairs)

                if session_id:
                    for task, _ in llm_pairs:
                        await progress_tracker.update_task_progress(
                            session_id,
                            task['task_id'],
                            TaskStatus.FAILED,
                            error_message=str(exc),
                        )

        # Direct pipelines run after LLMs so they can consume the latest results
        for task, cfg in direct_pairs:
            try:
                raw = cfg.direct_processor(task, task_manager) if cfg.direct_processor else task.get('source_text', '')
                final = cfg.post_processor(task, raw) if cfg.post_processor else raw

                task_manager.update_task(
                    task['task_id'],
                    {
                        'status': TaskStatus.COMPLETED,
                        'result': final,
                        'confidence': 1.0,
                        'end_time': datetime.now(),
                        'duration_ms': 0,
                        'token_count': 0,
                        'llm_model': '',
                    }
                )
                results['successful'] += 1

                if session_id:
                    await progress_tracker.update_task_progress(
                        session_id,
                        task['task_id'],
                        TaskStatus.COMPLETED,
                        result=final,
                        confidence=1.0,
                        duration_ms=0,
                    )
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.exception("Direct pipeline failed for %s", task['task_id'])
                task_manager.update_task(
                    task['task_id'],
                    {
                        'status': TaskStatus.FAILED,
                        'error_message': str(exc),
                        'end_time': datetime.now(),
                    }
                )
                results['failed'] += 1

                if session_id:
                    await progress_tracker.update_task_progress(
                        session_id,
                        task['task_id'],
                        TaskStatus.FAILED,
                        error_message=str(exc),
                    )

        results['duration_seconds'] = time.time() - start_time
        self.logger.info(
            "Batch %s completed: %s successful, %s failed, duration %.2fs",
            batch_id,
            results['successful'],
            results['failed'],
            results['duration_seconds'],
        )
        return results

    def _prepare_requests(
        self,
        tasks: List[Dict[str, Any]],
        game_info: Optional[Dict[str, Any]],
        glossary_config: Optional[Dict[str, Any]] = None,
    ) -> List[TranslationRequest]:
        requests: List[TranslationRequest] = []

        for task in tasks:
            task_game_info = (game_info or {}).copy()
            if task.get('reference_en'):
                task_game_info['reference_en'] = task['reference_en']

            requests.append(
                TranslationRequest(
                    source_text=task['source_text'],
                    source_lang=task['source_lang'],
                    target_lang=task['target_lang'],
                    context=task.get('source_context', ''),
                    game_info=task_game_info,
                    task_type=task.get('task_type', 'normal'),
                    task_id=task['task_id'],
                    batch_id=task.get('batch_id'),
                    group_id=task.get('group_id'),
                    glossary_config=glossary_config,
                )
            )

        return requests

    async def _process_response(
        self,
        task: Dict[str, Any],
        pipeline_config: TaskPipelineConfig,
        response: TranslationResponse,
        task_manager: TaskDataFrameManager,
        results: Dict[str, Any],
    ) -> None:
        try:
            if response.error:
                task_manager.update_task(
                    task['task_id'],
                    {
                        'status': TaskStatus.FAILED,
                        'error_message': response.error,
                        'end_time': datetime.now(),
                        'duration_ms': response.duration_ms,
                    }
                )
                results['failed'] += 1
                return

            post_processor = pipeline_config.post_processor if pipeline_config and pipeline_config.post_processor else PostProcessor.apply_post_processing
            final_result = post_processor(task, response.translated_text)

            task_manager.update_task(
                task['task_id'],
                {
                    'status': TaskStatus.COMPLETED,
                    'result': final_result,
                    'confidence': response.confidence,
                    'end_time': datetime.now(),
                    'duration_ms': response.duration_ms,
                    'llm_model': response.model,
                    'token_count': response.token_usage.get('total_tokens', 0),
                    'is_final': True,
                }
            )
            results['successful'] += 1
            results['total_tokens'] += response.token_usage.get('total_tokens', 0)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.exception("Error processing response for task %s", task['task_id'])
            task_manager.update_task(
                task['task_id'],
                {
                    'status': TaskStatus.FAILED,
                    'error_message': str(exc),
                    'end_time': datetime.now(),
                }
            )
            results['failed'] += 1

    async def _handle_llm_task(
        self,
        task: Dict[str, Any],
        pipeline_config: TaskPipelineConfig,
        task_manager: TaskDataFrameManager,
        results: Dict[str, Any],
        session_id: Optional[str],
    ) -> None:
        if task.get('status') == 'completed':
            await self._process_response(
                task,
                pipeline_config,
                TranslationResponse(
                    translated_text=task.get('result', ''),
                    confidence=task.get('confidence', 0.7),
                    token_usage={'total_tokens': task.get('token_count', 0)},
                    model=task.get('llm_model', ''),
                    duration_ms=task.get('duration_ms', 0),
                ),
                task_manager,
                results,
            )
            if session_id:
                await progress_tracker.update_task_progress(
                    session_id,
                    task['task_id'],
                    TaskStatus.COMPLETED,
                    result=task.get('result'),
                    confidence=task.get('confidence', 0.7),
                    duration_ms=task.get('duration_ms', 0),
                )
        else:
            task_manager.update_task(
                task['task_id'],
                {
                    'status': TaskStatus.FAILED,
                    'error_message': task.get('error_message', 'Translation failed'),
                    'end_time': datetime.now(),
                }
            )
            results['failed'] += 1
            if session_id:
                await progress_tracker.update_task_progress(
                    session_id,
                    task['task_id'],
                    TaskStatus.FAILED,
                    error_message=task.get('error_message', 'Translation failed'),
                )


class RetryableBatchExecutor(BatchExecutor):
    """Batch executor that retries failed tasks up to ``max_retries`` times."""

    def __init__(self, llm_provider: BaseLLMProvider, max_retries: int = 3):
        super().__init__(llm_provider)
        self.max_retries = max_retries

    async def execute_batch(
        self,
        batch_id: str,
        tasks: List[Dict[str, Any]],
        task_manager: TaskDataFrameManager,
        session_id: str | None = None,
        game_info: Optional[Dict[str, Any]] = None,
        glossary_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        results = await super().execute_batch(
            batch_id,
            tasks,
            task_manager,
            session_id,
            game_info,
            glossary_config,
        )

        failed_tasks: List[Dict[str, Any]] = []
        for task in tasks:
            task_data = task_manager.get_task(task['task_id'])
            if task_data is None or task_data['status'] != TaskStatus.FAILED:
                continue
            retry_count = task_data.get('retry_count', 0)
            if retry_count < self.max_retries:
                failed_tasks.append(task)

        if not failed_tasks:
            return results

        self.logger.info("Retrying %s failed tasks in batch %s", len(failed_tasks), batch_id)
        for task in failed_tasks:
            task_manager.update_task(
                task['task_id'],
                {'retry_count': task.get('retry_count', 0) + 1}
            )

        await asyncio.sleep(5)

        retry_results = await super().execute_batch(
            f"{batch_id}_retry",
            failed_tasks,
            task_manager,
            session_id,
            game_info,
            glossary_config,
        )

        results['successful'] += retry_results.get('successful', 0)
        results['failed'] = retry_results.get('failed', results['failed'])
        results['total_tokens'] += retry_results.get('total_tokens', 0)
        results['total_cost'] += retry_results.get('total_cost', 0.0)

        return results
