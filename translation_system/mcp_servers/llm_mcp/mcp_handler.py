"""
MCP Tool Handler for LLM Translation Server
"""

import asyncio
import logging
import base64
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from utils.session_manager import session_manager
from utils.token_validator import token_validator
from utils.http_client import download_file
from services.task_loader import task_loader
from services.translation_executor import translation_executor
from services.result_exporter import result_exporter
from models.session_data import SessionStatus

logger = logging.getLogger(__name__)


class MCPHandler:
    """Handle MCP tool calls for LLM translation."""

    def __init__(self):
        self.executor = translation_executor

    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Route tool calls to appropriate handlers."""

        logger.info(f"=" * 60)
        logger.info(f"MCP Tool Called: {tool_name}")
        logger.info(f"Arguments keys: {list(arguments.keys())}")
        logger.info(f"=" * 60)

        # Extract and validate token
        token = arguments.get('token')
        if not token:
            logger.error("Missing token in request")
            return self._error_response("Missing token")

        try:
            payload = token_validator.validate(token)
            logger.info(f"Token validated: {payload.get('user_id')}")
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return self._error_response(f"Token validation failed: {str(e)}")

        # Route to appropriate handler
        handlers = {
            "llm_translate_tasks": self._handle_translate_tasks,
            "llm_get_status": self._handle_get_status,
            "llm_pause_resume": self._handle_pause_resume,
            "llm_stop_translation": self._handle_stop_translation,
            "llm_get_results": self._handle_get_results,
            "llm_export_results": self._handle_export_results,
            "llm_retry_failed": self._handle_retry_failed,
            "llm_get_statistics": self._handle_get_statistics,
            "llm_list_sessions": self._handle_list_sessions,
            "llm_validate_provider": self._handle_validate_provider
        }

        handler = handlers.get(tool_name)
        if not handler:
            return self._error_response(f"Unknown tool: {tool_name}")

        try:
            logger.info(f"Calling handler for: {tool_name}")
            result = await handler(arguments, payload)
            logger.info(f"Handler completed: {tool_name}")
            logger.info(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            return result
        except Exception as e:
            logger.error(f"Tool handler error: {e}", exc_info=True)
            return self._error_response(str(e))

    async def _handle_translate_tasks(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle llm_translate_tasks tool."""
        logger.info("Starting translate_tasks handler")

        # Load tasks from file or URL
        tasks_data = None

        if 'file' in arguments:
            logger.info("Loading tasks from base64 file")
            # Decode base64 file
            try:
                file_content = base64.b64decode(arguments['file'])
                tasks_data = file_content
            except Exception as e:
                return self._error_response(f"Failed to decode file: {str(e)}")

        elif 'file_url' in arguments:
            # Download file from URL
            try:
                file_path = await download_file(arguments['file_url'])
                with open(file_path, 'rb') as f:
                    tasks_data = f.read()
            except Exception as e:
                return self._error_response(f"Failed to download file: {str(e)}")

        else:
            return self._error_response("Either 'file' or 'file_url' is required")

        # Parse tasks
        try:
            logger.info("Parsing tasks file")
            tasks = await asyncio.to_thread(
                task_loader.load_tasks,
                tasks_data,
                format='excel'  # Auto-detect from content
            )
            logger.info(f"Successfully loaded {len(tasks)} tasks")
        except Exception as e:
            logger.error(f"Failed to parse tasks: {e}", exc_info=True)
            return self._error_response(f"Failed to parse tasks: {str(e)}")

        # Create session
        session = session_manager.create_session(session_type='llm')
        session.tasks = tasks
        session.provider = arguments.get('provider')
        session.model = arguments.get('model')
        session.config = {
            'max_workers': arguments.get('max_workers', 5),
            'temperature': arguments.get('temperature', 0.3)
        }

        # Calculate statistics
        stats = {
            'total_tasks': len(tasks),
            'total_batches': len(set(t.get('batch_id') for t in tasks if t.get('batch_id'))),
            'languages': list(set(f"{t.get('source_lang')}->{t.get('target_lang')}" for t in tasks)),
            'task_types': {}
        }

        for task in tasks:
            task_type = task.get('task_type', 'normal')
            stats['task_types'][task_type] = stats['task_types'].get(task_type, 0) + 1

        # Estimate cost
        total_chars = sum(len(task.get('source_text', '')) for task in tasks)
        estimated_tokens = total_chars // 4  # Rough estimate
        estimated_cost = (estimated_tokens / 1000) * 0.05  # $0.05 per 1K tokens (example)

        stats['estimated_tokens'] = estimated_tokens
        stats['estimated_cost'] = round(estimated_cost, 2)

        session.metadata['stats'] = stats

        # Start translation in background
        logger.info(f"Starting background translation for session: {session.session_id}")
        logger.info(f"Provider: {session.provider}, Model: {session.model}")
        logger.info(f"Max workers: {session.config.get('max_workers')}, Temperature: {session.config.get('temperature')}")

        asyncio.create_task(
            self.executor.execute_translation(session.session_id)
        )

        response = {
            'session_id': session.session_id,
            'status': 'translating',
            'message': 'Translation started',
            'stats': stats
        }

        logger.info(f"Returning response: {response}")
        return response

    async def _handle_get_status(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle llm_get_status tool."""
        session_id = arguments.get('session_id')
        if not session_id:
            return self._error_response("Missing session_id")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        # Get translation statistics
        stats = session.translation_stats or {}

        return {
            'session_id': session_id,
            'status': session.status.value,
            'progress': session.progress,
            'completed_tasks': stats.get('completed_tasks', 0),
            'total_tasks': stats.get('total_tasks', 0),
            'failed_tasks': stats.get('failed_tasks', 0),
            'current_batch': stats.get('current_batch', 0),
            'total_batches': stats.get('total_batches', 0),
            'elapsed_time': stats.get('elapsed_time', 0),
            'estimated_remaining': stats.get('estimated_remaining', 0),
            'current_cost': stats.get('current_cost', 0),
            'tokens_used': stats.get('tokens_used', 0)
        }

    async def _handle_pause_resume(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle llm_pause_resume tool."""
        session_id = arguments.get('session_id')
        action = arguments.get('action')

        if not session_id:
            return self._error_response("Missing session_id")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        if action == 'pause':
            if session.status != SessionStatus.TRANSLATING:
                return self._error_response("Session is not running")

            session.status = SessionStatus.PAUSED
            return {
                'session_id': session_id,
                'status': 'paused',
                'message': 'Translation paused'
            }

        elif action == 'resume':
            if session.status != SessionStatus.PAUSED:
                return self._error_response("Session is not paused")

            session.status = SessionStatus.TRANSLATING
            # Resume execution
            asyncio.create_task(
                self.executor.resume_translation(session_id)
            )

            return {
                'session_id': session_id,
                'status': 'resumed',
                'message': 'Translation resumed'
            }

        return self._error_response(f"Invalid action: {action}")

    async def _handle_stop_translation(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle llm_stop_translation tool."""
        session_id = arguments.get('session_id')

        if not session_id:
            return self._error_response("Missing session_id")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        # Stop translation
        session.status = SessionStatus.STOPPED

        return {
            'session_id': session_id,
            'status': 'stopped',
            'message': 'Translation stopped'
        }

    async def _handle_get_results(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle llm_get_results tool."""
        session_id = arguments.get('session_id')
        filter_type = arguments.get('filter', 'all')
        preview_limit = arguments.get('preview_limit', 10)

        if not session_id:
            return self._error_response("Missing session_id")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        # Filter tasks
        tasks = session.tasks or []
        filtered_tasks = []

        for task in tasks:
            status = task.get('status', 'pending')
            if filter_type == 'all' or filter_type == status:
                filtered_tasks.append(task)

        # Get preview
        preview_tasks = filtered_tasks[:preview_limit]

        # Calculate summary
        summary = {
            'total': len(tasks),
            'completed': len([t for t in tasks if t.get('status') == 'completed']),
            'failed': len([t for t in tasks if t.get('status') == 'failed']),
            'pending': len([t for t in tasks if t.get('status') == 'pending'])
        }

        return {
            'session_id': session_id,
            'filter': filter_type,
            'summary': summary,
            'preview_tasks': preview_tasks,
            'total_filtered': len(filtered_tasks)
        }

    async def _handle_export_results(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle llm_export_results tool."""
        session_id = arguments.get('session_id')
        export_format = arguments.get('format', 'excel')
        merge_source = arguments.get('merge_source', True)

        if not session_id:
            return self._error_response("Missing session_id")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        # Export results
        try:
            export_path = await asyncio.to_thread(
                result_exporter.export,
                session.tasks,
                session_id,
                format=export_format,
                merge_source=merge_source
            )

            # Generate download URL
            filename = Path(export_path).name
            download_url = f"/exports/{filename}"

            # Save to session metadata
            session.metadata['export_path'] = str(export_path)
            session.metadata['download_url'] = download_url

            return {
                'session_id': session_id,
                'status': 'exported',
                'download_url': download_url,
                'export_path': str(export_path),
                'format': export_format
            }

        except Exception as e:
            return self._error_response(f"Export failed: {str(e)}")

    async def _handle_retry_failed(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle llm_retry_failed tool."""
        session_id = arguments.get('session_id')
        task_ids = arguments.get('task_ids', [])
        max_retries = arguments.get('max_retries', 3)

        if not session_id:
            return self._error_response("Missing session_id")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        # Get failed tasks
        failed_tasks = []
        for task in session.tasks:
            if task.get('status') == 'failed':
                if not task_ids or task.get('task_id') in task_ids:
                    task['status'] = 'pending'
                    task['retry_count'] = task.get('retry_count', 0)
                    failed_tasks.append(task)

        if not failed_tasks:
            return {
                'session_id': session_id,
                'message': 'No failed tasks to retry',
                'retry_count': 0
            }

        # Start retry in background
        asyncio.create_task(
            self.executor.retry_tasks(session_id, failed_tasks, max_retries)
        )

        return {
            'session_id': session_id,
            'status': 'retrying',
            'message': f'Retrying {len(failed_tasks)} failed tasks',
            'retry_count': len(failed_tasks)
        }

    async def _handle_get_statistics(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle llm_get_statistics tool."""
        session_id = arguments.get('session_id')

        if not session_id:
            return self._error_response("Missing session_id")

        session = session_manager.get_session(session_id)
        if not session:
            return self._error_response("Session not found")

        # Calculate detailed statistics
        tasks = session.tasks or []
        stats = {
            'overview': {
                'total_tasks': len(tasks),
                'completed_tasks': len([t for t in tasks if t.get('status') == 'completed']),
                'failed_tasks': len([t for t in tasks if t.get('status') == 'failed']),
                'success_rate': 0,
                'total_duration': session.translation_stats.get('elapsed_time', 0) if session.translation_stats else 0
            },
            'by_language': {},
            'by_task_type': {},
            'token_usage': session.translation_stats.get('token_usage', {}) if session.translation_stats else {},
            'cost_breakdown': session.translation_stats.get('cost_breakdown', {}) if session.translation_stats else {}
        }

        # Calculate success rate
        if stats['overview']['total_tasks'] > 0:
            stats['overview']['success_rate'] = round(
                (stats['overview']['completed_tasks'] / stats['overview']['total_tasks']) * 100,
                2
            )

        # Group by language
        for task in tasks:
            lang_pair = f"{task.get('source_lang')}->{task.get('target_lang')}"
            if lang_pair not in stats['by_language']:
                stats['by_language'][lang_pair] = {
                    'total': 0,
                    'completed': 0,
                    'failed': 0
                }

            stats['by_language'][lang_pair]['total'] += 1
            if task.get('status') == 'completed':
                stats['by_language'][lang_pair]['completed'] += 1
            elif task.get('status') == 'failed':
                stats['by_language'][lang_pair]['failed'] += 1

        # Group by task type
        for task in tasks:
            task_type = task.get('task_type', 'normal')
            if task_type not in stats['by_task_type']:
                stats['by_task_type'][task_type] = {
                    'total': 0,
                    'completed': 0,
                    'failed': 0
                }

            stats['by_task_type'][task_type]['total'] += 1
            if task.get('status') == 'completed':
                stats['by_task_type'][task_type]['completed'] += 1
            elif task.get('status') == 'failed':
                stats['by_task_type'][task_type]['failed'] += 1

        return {
            'session_id': session_id,
            'statistics': stats
        }

    async def _handle_list_sessions(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle llm_list_sessions tool."""
        status_filter = arguments.get('status', 'all')

        sessions = []
        for session in session_manager.get_all_sessions():
            if session.session_type == 'llm':
                if status_filter == 'all' or session.status.value == status_filter:
                    sessions.append({
                        'session_id': session.session_id,
                        'status': session.status.value,
                        'progress': session.progress,
                        'created_at': session.created_at.isoformat(),
                        'provider': session.provider,
                        'task_count': len(session.tasks) if session.tasks else 0
                    })

        return {
            'sessions': sessions,
            'total': len(sessions)
        }

    async def _handle_validate_provider(self, arguments: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle llm_validate_provider tool."""
        provider = arguments.get('provider')
        api_key = arguments.get('api_key')
        test_translation = arguments.get('test_translation', True)

        # Import provider dynamically
        try:
            if provider == 'openai':
                from services.llm.openai_provider import OpenAIProvider
                llm = OpenAIProvider(api_key=api_key)
            elif provider == 'qwen':
                from services.llm.qwen_provider import QwenProvider
                llm = QwenProvider(api_key=api_key)
            else:
                return self._error_response(f"Unsupported provider: {provider}")

            # Validate API key
            is_valid = await llm.validate_key()

            result = {
                'provider': provider,
                'valid': is_valid
            }

            # Perform test translation if requested
            if is_valid and test_translation:
                try:
                    test_result = await llm.translate(
                        text="Hello",
                        source_lang="EN",
                        target_lang="ZH",
                        context={}
                    )
                    result['test_translation'] = {
                        'success': True,
                        'result': test_result.text,
                        'tokens': test_result.tokens_used
                    }
                except Exception as e:
                    result['test_translation'] = {
                        'success': False,
                        'error': str(e)
                    }

            return result

        except Exception as e:
            return self._error_response(f"Validation failed: {str(e)}")

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Create error response."""
        return {
            'error': {
                'message': message
            }
        }