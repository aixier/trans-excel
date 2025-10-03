"""
Translation Executor Service for LLM MCP Server
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from utils.session_manager import session_manager
from utils.config_loader import config_loader
from models.session_data import SessionStatus, TranslationSession

logger = logging.getLogger(__name__)


class TranslationExecutor:
    """Executes translation tasks asynchronously."""

    def __init__(self):
        self.active_executions = {}
        self._lock = asyncio.Lock()

    async def execute_translation(self, session_id: str):
        """Execute translation for a session."""
        try:
            session = session_manager.get_session(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return

            # Mark as translating
            session.status = SessionStatus.TRANSLATING
            start_time = time.time()

            # Initialize LLM provider
            provider = await self._get_provider(session)
            if not provider:
                session.status = SessionStatus.FAILED
                session.update_stats({'error': 'Failed to initialize provider'})
                return

            # Group tasks by batch
            batches = self._group_tasks_by_batch(session.tasks)
            total_batches = len(batches)
            completed_tasks = 0
            failed_tasks = 0

            # Process batches
            for batch_idx, (batch_id, batch_tasks) in enumerate(batches.items()):
                # Check if should stop
                if session.should_stop:
                    session.status = SessionStatus.STOPPED
                    break

                # Check if paused
                while session.is_paused:
                    await asyncio.sleep(1)
                    if session.should_stop:
                        session.status = SessionStatus.STOPPED
                        break

                # Process batch
                logger.info(f"Processing batch {batch_id} ({batch_idx + 1}/{total_batches})")

                # Create workers for concurrent translation
                max_workers = session.config.get('max_workers', 5)
                semaphore = asyncio.Semaphore(max_workers)

                async def translate_task(task):
                    async with semaphore:
                        return await self._translate_single_task(task, provider, session)

                # Execute tasks concurrently
                results = await asyncio.gather(
                    *[translate_task(task) for task in batch_tasks],
                    return_exceptions=True
                )

                # Update task statuses
                for task, result in zip(batch_tasks, results):
                    if isinstance(result, Exception):
                        task['status'] = 'failed'
                        task['error'] = str(result)
                        failed_tasks += 1
                    else:
                        task.update(result)
                        if task['status'] == 'completed':
                            completed_tasks += 1
                        else:
                            failed_tasks += 1

                # Update progress
                progress = ((batch_idx + 1) / total_batches) * 100
                session.update_progress(completed_tasks, len(session.tasks))

                # Calculate statistics
                elapsed_time = time.time() - start_time
                tasks_per_second = completed_tasks / elapsed_time if elapsed_time > 0 else 0
                remaining_tasks = len(session.tasks) - completed_tasks - failed_tasks
                estimated_remaining = remaining_tasks / tasks_per_second if tasks_per_second > 0 else 0

                # Update session stats
                stats = {
                    'completed_tasks': completed_tasks,
                    'failed_tasks': failed_tasks,
                    'total_tasks': len(session.tasks),
                    'current_batch': batch_idx + 1,
                    'total_batches': total_batches,
                    'elapsed_time': int(elapsed_time),
                    'estimated_remaining': int(estimated_remaining),
                    'tasks_per_second': round(tasks_per_second, 2)
                }

                # Calculate cost if available
                if hasattr(provider, 'get_total_cost'):
                    stats['current_cost'] = provider.get_total_cost()
                if hasattr(provider, 'get_total_tokens'):
                    stats['tokens_used'] = provider.get_total_tokens()

                session.update_stats(stats)

                logger.info(f"Batch {batch_id} completed: {completed_tasks}/{len(session.tasks)} tasks")

            # Mark session as completed
            if session.status == SessionStatus.TRANSLATING:
                session.status = SessionStatus.COMPLETED
                logger.info(f"Translation completed for session {session_id}")

        except Exception as e:
            logger.error(f"Translation execution failed: {e}", exc_info=True)
            session = session_manager.get_session(session_id)
            if session:
                session.status = SessionStatus.FAILED
                session.update_stats({'error': str(e)})

    async def resume_translation(self, session_id: str):
        """Resume paused translation."""
        session = session_manager.get_session(session_id)
        if session:
            session.is_paused = False
            # If not already executing, start execution
            if session_id not in self.active_executions:
                await self.execute_translation(session_id)

    async def retry_tasks(self, session_id: str, tasks: List[Dict], max_retries: int = 3):
        """Retry failed tasks."""
        session = session_manager.get_session(session_id)
        if not session:
            return

        session.status = SessionStatus.TRANSLATING

        # Initialize provider
        provider = await self._get_provider(session)
        if not provider:
            return

        # Retry each task
        for task in tasks:
            if task['retry_count'] >= max_retries:
                continue

            task['retry_count'] += 1

            try:
                result = await self._translate_single_task(task, provider, session)
                task.update(result)
            except Exception as e:
                logger.error(f"Retry failed for task {task['task_id']}: {e}")
                task['error'] = str(e)

        # Update session status
        all_completed = all(t['status'] == 'completed' for t in session.tasks)
        if all_completed:
            session.status = SessionStatus.COMPLETED
        else:
            session.status = SessionStatus.PAUSED

    async def _get_provider(self, session: TranslationSession):
        """Get LLM provider for session."""
        try:
            # Use provider from session or default from config
            provider_name = session.provider or config_loader.get_default_provider()

            # Get provider configuration
            provider_config = config_loader.get_provider_config(provider_name)

            # Override model if specified in session
            if session.model:
                provider_config['model'] = session.model

            # Initialize provider based on name
            if provider_name in ['openai', 'gpt-4', 'gpt4']:
                from services.llm.openai_provider import OpenAIProvider
                return OpenAIProvider(
                    api_key=provider_config.get('api_key'),
                    base_url=provider_config.get('base_url'),
                    model=provider_config.get('model', 'gpt-4-turbo-preview'),
                    temperature=provider_config.get('temperature', 0.3),
                    max_tokens=provider_config.get('max_tokens', 8000),
                    timeout=provider_config.get('timeout', 90)
                )
            elif provider_name in ['qwen', 'qwen-plus', 'tongyi']:
                from services.llm.qwen_provider import QwenProvider
                return QwenProvider(
                    api_key=provider_config.get('api_key'),
                    base_url=provider_config.get('base_url'),
                    model=provider_config.get('model', 'qwen-plus'),
                    temperature=provider_config.get('temperature', 0.3),
                    max_tokens=provider_config.get('max_tokens', 8000),
                    timeout=provider_config.get('timeout', 90)
                )
            else:
                logger.error(f"Unsupported provider: {provider_name}")
                return None

        except Exception as e:
            logger.error(f"Failed to initialize provider: {e}")
            return None

    async def _translate_single_task(self, task: Dict, provider: Any, session: TranslationSession) -> Dict:
        """Translate a single task."""
        try:
            # Skip if already completed
            if task.get('status') == 'completed' and task.get('target_text'):
                return task

            # Prepare context
            context = task.get('context', {})
            temperature = session.config.get('temperature', 0.3)

            # Call provider
            result = await provider.translate(
                text=task['source_text'],
                source_lang=task['source_lang'],
                target_lang=task['target_lang'],
                task_type=task.get('task_type', 'normal'),
                context=context,
                temperature=temperature
            )

            # Update task with result
            task['target_text'] = result.text
            task['status'] = 'completed'
            task['tokens_used'] = result.tokens_used
            task['cost'] = result.cost
            task['translated_at'] = datetime.now().isoformat()

            return task

        except Exception as e:
            logger.error(f"Translation failed for task {task.get('task_id')}: {e}")
            task['status'] = 'failed'
            task['error'] = str(e)
            return task

    def _group_tasks_by_batch(self, tasks: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group tasks by batch ID and sort by priority within each batch.

        Priority order (matching backend_v2):
        1. Yellow tasks (re-translation) - Priority 9-10
        2. Blue tasks (shortening) - Priority 7-8
        3. Normal tasks - Priority 5-6
        """
        batches = {}
        for task in tasks:
            batch_id = task.get('batch_id', 'default')
            if batch_id not in batches:
                batches[batch_id] = []
            batches[batch_id].append(task)

        # Sort tasks within each batch by priority
        for batch_id in batches:
            batches[batch_id] = self._sort_tasks_by_priority(batches[batch_id])

        return batches

    def _sort_tasks_by_priority(self, tasks: List[Dict]) -> List[Dict]:
        """
        Sort tasks by priority (highest first).

        Priority order:
        - Yellow (re-translation): 9
        - Blue (shortening): 7
        - Normal: 5
        """
        def get_priority(task: Dict) -> int:
            task_type = task.get('task_type', 'normal')

            # Base priority by task type
            if task_type == 'yellow':
                return 9  # Highest priority
            elif task_type == 'blue':
                return 7  # High priority
            else:  # normal
                return 5  # Normal priority

        # Sort by priority (descending) and then by task_id for stability
        return sorted(tasks, key=lambda t: (-get_priority(t), t.get('task_id', '')))


# Global translation executor instance
translation_executor = TranslationExecutor()