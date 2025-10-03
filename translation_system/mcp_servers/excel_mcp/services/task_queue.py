"""Simple async task queue for processing Excel analysis tasks."""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from io import BytesIO
from pathlib import Path

from models.session_data import SessionData, SessionStatus
from utils.session_manager import session_manager
from services.excel_loader import excel_loader
from services.excel_analyzer import excel_analyzer
from services.task_splitter_service import task_splitter_service
from services.task_exporter import task_exporter

logger = logging.getLogger(__name__)


class TaskQueue:
    """Simple async task queue for Excel analysis."""

    def __init__(self):
        self._queue = asyncio.Queue()
        self._processing = False

    async def submit_analysis_task(
        self,
        session_id: str,
        file_data: Optional[BytesIO] = None,
        file_url: Optional[str] = None,
        filename: str = "uploaded.xlsx",
        options: Dict[str, Any] = None
    ) -> None:
        """
        Submit an Excel analysis task to the queue.

        Args:
            session_id: Session ID for tracking
            file_data: File data as BytesIO (if uploading)
            file_url: URL to download file from (if using URL)
            filename: Original filename
            options: Analysis options
        """
        task = {
            'session_id': session_id,
            'file_data': file_data,
            'file_url': file_url,
            'filename': filename,
            'options': options or {}
        }

        await self._queue.put(task)
        logger.info(f"Task submitted to queue: {session_id}")

        # Start processing if not already running
        if not self._processing:
            asyncio.create_task(self._process_queue())

    async def _process_queue(self):
        """Process tasks from the queue."""
        self._processing = True

        try:
            while not self._queue.empty():
                task = await self._queue.get()
                await self._process_task(task)
                self._queue.task_done()

        except Exception as e:
            logger.error(f"Error processing queue: {e}")

        finally:
            self._processing = False

    async def _process_task(self, task: Dict[str, Any]):
        """
        Process a single task (analysis, split, or export).

        Args:
            task: Task dictionary
        """
        task_type = task.get('type', 'analysis')

        if task_type == 'split':
            await self._process_split_task(task)
        elif task_type == 'export':
            await self._process_export_task(task)
        else:
            await self._process_analysis_task(task)

    async def _process_analysis_task(self, task: Dict[str, Any]):
        """
        Process an analysis task.

        Args:
            task: Task dictionary
        """
        session_id = task['session_id']
        session = session_manager.get_session(session_id)

        if not session:
            logger.error(f"Session not found: {session_id}")
            return

        try:
            # Update status to processing
            session.status = SessionStatus.ANALYZING
            session.progress = 10
            logger.info(f"Processing analysis task: {session_id}")

            # Load Excel file
            if task['file_url']:
                logger.info(f"Loading Excel from URL: {task['file_url']}")
                excel_df = await asyncio.to_thread(
                    excel_loader.load_from_url,
                    task['file_url']
                )
            elif task['file_data']:
                logger.info(f"Loading Excel from bytes: {task['filename']}")
                excel_df = await asyncio.to_thread(
                    excel_loader.load_from_bytes,
                    task['file_data'],
                    task['filename']
                )
            else:
                raise ValueError("Either file_url or file_data must be provided")

            session.progress = 40
            session.excel_df = excel_df
            session.file_info = {
                'filename': excel_df.filename,
                'excel_id': excel_df.excel_id,
                'sheets': excel_df.get_sheet_names(),
                'sheet_count': len(excel_df.sheets)
            }

            # Perform analysis
            logger.info(f"Analyzing Excel: {session_id}")
            analysis_result = await asyncio.to_thread(
                excel_analyzer.analyze,
                excel_df,
                task['options']
            )

            session.progress = 90
            session.analysis = analysis_result.to_dict()

            # Mark analysis as completed
            session.has_analysis = True
            session.status = SessionStatus.COMPLETED
            session.progress = 100
            logger.info(f"Analysis task completed: {session_id}")

        except Exception as e:
            logger.error(f"Analysis task failed: {session_id}, error: {e}")
            session.status = SessionStatus.FAILED
            session.error = {
                'code': 'ANALYSIS_FAILED',
                'message': str(e)
            }

    async def _process_split_task(self, task: Dict[str, Any]):
        """
        Process a task splitting task.

        Args:
            task: Task dictionary
        """
        session_id = task['session_id']
        session = session_manager.get_session(session_id)

        if not session:
            logger.error(f"Session not found: {session_id}")
            return

        try:
            # Update status to splitting
            session.status = SessionStatus.SPLITTING
            session.progress = 10
            logger.info(f"Processing split task: {session_id}")
            logger.info(f"Split parameters: source_lang={task['source_lang']}, target_langs={task['target_langs']}, extract_context={task['extract_context']}")

            # Perform task splitting directly with ExcelDataFrame
            logger.info(f"Calling task_splitter_service.split_excel...")
            split_result = await asyncio.to_thread(
                task_splitter_service.split_excel,
                excel_df=session.excel_df,
                source_lang=task['source_lang'],
                target_langs=task['target_langs'],
                extract_context=task['extract_context'],
                context_options=task['context_options']
            )
            logger.info(f"Task splitting completed, result keys: {split_result.keys()}")

            session.progress = 90

            # Store tasks and summary
            session.tasks = split_result['tasks']
            session.tasks_summary = split_result['summary']
            session.has_tasks = True

            # Mark as completed
            session.status = SessionStatus.COMPLETED
            session.progress = 100
            logger.info(f"Split task completed: {session_id}, {len(session.tasks)} tasks created")

        except Exception as e:
            logger.error(f"Split task failed: {session_id}, error: {e}", exc_info=True)
            session.status = SessionStatus.FAILED
            session.error = {
                'code': 'SPLIT_FAILED',
                'message': str(e)
            }

    async def _process_export_task(self, task: Dict[str, Any]):
        """
        Process an export task.

        Args:
            task: Task dictionary
        """
        session_id = task['session_id']
        session = session_manager.get_session(session_id)

        if not session:
            logger.error(f"Session not found: {session_id}")
            return

        try:
            # Update status to processing
            session.status = SessionStatus.PROCESSING
            session.progress = 10
            logger.info(f"Processing export task: {session_id}")

            # Perform export
            export_path = await asyncio.to_thread(
                task_exporter.export,
                tasks=session.tasks,
                session_id=session_id,
                format=task['export_format']
            )

            session.progress = 90

            # Generate download URL (独立的 exports 路由)
            filename = Path(export_path).name
            download_url = f"/exports/{filename}"

            # Store export info in metadata
            session.metadata['export_path'] = export_path
            session.metadata['download_url'] = download_url

            # Mark as completed
            session.status = SessionStatus.COMPLETED
            session.progress = 100
            logger.info(f"Export task completed: {session_id}")

        except Exception as e:
            logger.error(f"Export task failed: {session_id}, error: {e}")
            session.status = SessionStatus.FAILED
            session.error = {
                'code': 'EXPORT_FAILED',
                'message': str(e)
            }

    async def submit_task_split(
        self,
        session_id: str,
        source_lang: Optional[str],
        target_langs: list,
        extract_context: bool = True,
        context_options: Dict[str, Any] = None
    ) -> None:
        """
        Submit a task splitting job to the queue.

        Args:
            session_id: Session ID
            source_lang: Source language (optional, auto-detect if None)
            target_langs: Target languages list
            extract_context: Whether to extract context
            context_options: Context extraction options
        """
        task = {
            'type': 'split',
            'session_id': session_id,
            'source_lang': source_lang,
            'target_langs': target_langs,
            'extract_context': extract_context,
            'context_options': context_options or {}
        }

        await self._queue.put(task)
        logger.info(f"Task split submitted to queue: {session_id}")

        # Start processing if not already running
        if not self._processing:
            asyncio.create_task(self._process_queue())

    async def submit_export_task(
        self,
        session_id: str,
        export_format: str = 'excel',
        include_context: bool = True
    ) -> None:
        """
        Submit an export task to the queue.

        Args:
            session_id: Session ID
            export_format: Export format (excel/json/csv)
            include_context: Include context in export
        """
        task = {
            'type': 'export',
            'session_id': session_id,
            'export_format': export_format,
            'include_context': include_context
        }

        await self._queue.put(task)
        logger.info(f"Export task submitted to queue: {session_id}")

        # Start processing if not already running
        if not self._processing:
            asyncio.create_task(self._process_queue())


# Global task queue instance
task_queue = TaskQueue()
