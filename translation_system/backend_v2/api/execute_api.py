"""Execution control API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import logging

from models.session_state import SessionStage
from services.split_state import SplitProgress, SplitStatus
from services.execution_state import ExecutionProgress, ExecutionStatus
from services.executor.worker_pool import worker_pool
from services.llm.llm_factory import LLMFactory
from utils.session_manager import session_manager
from utils.config_manager import config_manager

router = APIRouter(prefix="/api/execute", tags=["execute"])
logger = logging.getLogger(__name__)


class ExecuteRequest(BaseModel):
    """Execute request model."""
    session_id: str
    provider: Optional[str] = None  # Override LLM provider
    max_workers: Optional[int] = None  # Override max workers
    glossary_config: Optional[Dict] = None  # ✨ Glossary configuration


@router.post("/start")
async def start_execution(request: ExecuteRequest):
    """
    Start translation execution with strict validation.

    Args:
        request: Execution request with session_id

    Returns:
        Execution status with ready_for_monitoring flag
    """
    session_id = request.session_id

    # ✨ T10: Validation 1 - Session exists
    session = session_manager.get_session(session_id)
    if not session:
        logger.error(f"Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")

    # ✨ T10: Validation 2 - TaskManager exists (with lazy loading support)
    task_manager = session_manager.get_task_manager(session_id)
    if not task_manager:
        logger.error(f"Task manager not found for session {session_id}")
        raise HTTPException(status_code=404, detail="Task manager not found. Please split tasks first.")

    # ✨ T10: Validation 3 - Split is complete and ready (KEY!)
    split_progress = session.split_progress
    if not split_progress or not split_progress.is_ready():
        # Provide detailed error message
        if not split_progress:
            detail = "Session not ready: split not started"
            logger.error(f"Session {session_id}: {detail}")
        elif split_progress.status != SplitStatus.COMPLETED:
            detail = f"Session not ready: split status is {split_progress.status.value}"
            logger.error(f"Session {session_id}: {detail}")
        else:
            detail = "Session not ready: split not verified (ready_for_next_stage=False)"
            logger.error(f"Session {session_id}: {detail}")
        raise HTTPException(status_code=400, detail=detail)

    # ✨ T10: Validation 4 - Session stage correct
    # Allow execution in these cases:
    # 1. SPLIT_COMPLETE: First time execution
    # 2. COMPLETED: Re-execute completed tasks
    # 3. EXECUTING: Re-execute if previous execution stopped/failed
    allowed_stages = [SessionStage.SPLIT_COMPLETE, SessionStage.COMPLETED]
    current_stage = session.session_status.stage

    if current_stage == SessionStage.EXECUTING:
        # Check if we can restart
        exec_progress = session.execution_progress
        if exec_progress and exec_progress.status in [ExecutionStatus.STOPPED, ExecutionStatus.FAILED, ExecutionStatus.COMPLETED]:
            # Previous execution finished, allow restart
            logger.info(f"Session {session_id} in EXECUTING stage but previous execution {exec_progress.status.value}, allowing restart")
        else:
            # Currently running, don't allow
            detail = f"Cannot execute: session is currently executing (status: {exec_progress.status.value if exec_progress else 'unknown'})"
            logger.error(f"Session {session_id}: {detail}")
            raise HTTPException(status_code=400, detail=detail)
    elif current_stage not in allowed_stages:
        detail = f"Cannot execute in stage: {current_stage.value}. Must be in SPLIT_COMPLETE or COMPLETED stage."
        logger.error(f"Session {session_id}: {detail}")
        raise HTTPException(status_code=400, detail=detail)

    logger.info(f"✨ All validations passed for session {session_id}")

    # ✨ T10: Initialize/Reset execution progress
    # Force create new execution progress to reset state when re-executing
    session.execution_progress = ExecutionProgress(session_id)
    exec_progress = session.execution_progress
    exec_progress.mark_initializing()

    # Reset tasks to PENDING if re-executing
    if current_stage in [SessionStage.COMPLETED, SessionStage.EXECUTING]:
        from models.task_dataframe import TaskStatus
        if task_manager.df is not None:
            completed_count = (task_manager.df['status'] == TaskStatus.COMPLETED).sum()
            failed_count = (task_manager.df['status'] == TaskStatus.FAILED).sum()
            if completed_count > 0 or failed_count > 0:
                # Reset all completed/failed tasks to pending for re-execution
                task_manager.df.loc[task_manager.df['status'].isin([TaskStatus.COMPLETED, TaskStatus.FAILED]), 'status'] = TaskStatus.PENDING
                task_manager.df.loc[task_manager.df['status'].isin([TaskStatus.PENDING]), 'start_time'] = None
                task_manager.df.loc[task_manager.df['status'].isin([TaskStatus.PENDING]), 'end_time'] = None
                task_manager.df.loc[task_manager.df['status'].isin([TaskStatus.PENDING]), 'error'] = None
                logger.info(f"Reset {completed_count + failed_count} tasks to PENDING for re-execution")

    logger.info(f"Initialized execution progress for session {session_id}")

    # Get configuration
    config = config_manager.get_config()
    llm_config = config.get('llm', {})

    # Determine provider
    provider_name = request.provider or llm_config.get('default_provider', 'openai')

    # Override max workers if specified
    if request.max_workers:
        worker_pool.max_workers = request.max_workers

    try:
        # Create LLM provider
        llm_provider = LLMFactory.create_from_config_file(config, provider_name)

        # Start execution
        result = await worker_pool.start_execution(
            session_id,
            llm_provider,
            glossary_config=request.glossary_config  # ✨ Pass glossary config
        )

        if result['status'] == 'error':
            exec_progress.mark_failed(result['message'])
            raise HTTPException(status_code=400, detail=result['message'])

        # Start progress monitoring for WebSocket updates
        try:
            from services.executor.progress_tracker import progress_tracker
            await progress_tracker.start_progress_monitoring(session_id)
            logger.info(f"Progress monitoring initialized for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to start progress monitoring: {e}")
            # Don't fail the execution if monitoring fails

        # ✨ T10: Mark as running (monitoring ready)
        exec_progress.mark_running()
        session.session_status.update_stage(SessionStage.EXECUTING)

        # ✅ Sync to cache so other workers can see the stage update
        session_manager._sync_to_cache(session)
        logger.info(f"✨ Execution started, ready_for_monitoring={exec_progress.ready_for_monitoring} (synced to cache)")

        # ✨ T10: Return execution progress with ready_for_monitoring flag
        # Include progress field for frontend compatibility
        response = {
            **result,
            **exec_progress.to_dict(),
            'progress': {
                'total': result.get('total_tasks', 0),
                'completed': 0,
                'processing': 0,
                'pending': result.get('total_tasks', 0),
                'failed': 0
            }
        }
        logger.info(f"Started execution for session {session_id} (memory-only mode)")
        return response

    except ValueError as e:
        exec_progress.mark_failed(str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start execution: {str(e)}")
        exec_progress.mark_failed(str(e))
        raise HTTPException(status_code=500, detail=f"Execution start failed: {str(e)}")


@router.post("/stop/{session_id}")
async def stop_execution(session_id: str):
    """
    Stop translation execution.

    Args:
        session_id: Session ID

    Returns:
        Stop status
    """
    if worker_pool.current_session_id != session_id:
        raise HTTPException(
            status_code=400,
            detail="Session ID does not match current execution"
        )

    result = await worker_pool.stop_execution()

    if result['status'] == 'error':
        raise HTTPException(status_code=400, detail=result['message'])

    logger.info(f"Stopped execution for session {session_id} (memory-only mode)")
    return result


@router.post("/pause/{session_id}")
async def pause_execution(session_id: str):
    """
    Pause translation execution.

    Args:
        session_id: Session ID

    Returns:
        Pause status
    """
    if worker_pool.current_session_id != session_id:
        raise HTTPException(
            status_code=400,
            detail="Session ID does not match current execution"
        )

    result = await worker_pool.pause_execution()

    if result['status'] == 'error':
        raise HTTPException(status_code=400, detail=result['message'])

    logger.info(f"Paused execution for session {session_id}")
    return result


@router.post("/resume/{session_id}")
async def resume_execution(session_id: str):
    """
    Resume paused execution.

    Args:
        session_id: Session ID

    Returns:
        Resume status
    """
    if worker_pool.current_session_id != session_id:
        raise HTTPException(
            status_code=400,
            detail="Session ID does not match current execution"
        )

    result = await worker_pool.resume_execution()

    if result['status'] == 'error':
        raise HTTPException(status_code=400, detail=result['message'])

    logger.info(f"Resumed execution for session {session_id}")
    return result


@router.get("/status/{session_id}")
async def get_execution_status(session_id: str):
    """
    Get execution status.

    Args:
        session_id: Session ID

    Returns:
        Execution status including execution_progress state
    """
    # Check if session exists
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if this session is currently executing
    if worker_pool.current_session_id == session_id:
        # Get real-time status from worker_pool
        worker_status = worker_pool.get_status()

        # Merge with execution_progress if available
        if session.execution_progress:
            exec_progress_dict = session.execution_progress.to_dict()
            # Worker status takes precedence for real-time stats
            return {
                **exec_progress_dict,
                **worker_status
            }

        return worker_status

    # Not currently executing - check execution_progress for historical status
    if session.execution_progress:
        exec_progress = session.execution_progress
        progress_dict = exec_progress.to_dict()

        # Provide helpful status based on execution state
        if exec_progress.status == ExecutionStatus.INITIALIZING:
            return {
                **progress_dict,
                'message': '执行初始化中，请稍候...'
            }
        elif exec_progress.status == ExecutionStatus.RUNNING:
            # May have completed or stopped
            task_manager = session_manager.get_task_manager(session_id)
            if task_manager:
                stats = task_manager.get_statistics()
                total = stats.get('total', 0)
                completed = stats.get('completed', 0)

                if total > 0 and completed >= total:
                    # All tasks completed
                    exec_progress.mark_completed()
                    session.session_status.update_stage(SessionStage.COMPLETED)
                    return {
                        **exec_progress.to_dict(),
                        'statistics': stats,
                        'message': '翻译已完成'
                    }

            return {
                **progress_dict,
                'message': '执行状态未更新，可能已停止'
            }
        elif exec_progress.status == ExecutionStatus.COMPLETED:
            return {
                **progress_dict,
                'message': '翻译已完成'
            }
        elif exec_progress.status == ExecutionStatus.FAILED:
            return {
                **progress_dict,
                'message': f'翻译失败: {exec_progress.error or "未知错误"}'
            }
        else:
            return progress_dict

    # No execution_progress - check if tasks exist
    task_manager = session_manager.get_task_manager(session_id)
    if not task_manager:
        raise HTTPException(
            status_code=404,
            detail="Task manager not found. Please split tasks first before checking execution status."
        )

    # Tasks exist but execution never started
    return {
        'status': 'idle',
        'session_id': session_id,
        'message': 'No execution started for this session',
        'ready_for_monitoring': False,
        'ready_for_download': False
    }


@router.get("/config")
async def get_execution_config():
    """
    Get execution configuration.

    Returns:
        Current execution configuration
    """
    config = config_manager.get_config()
    llm_config = config.get('llm', {})
    task_execution_config = config.get('task_execution', {})
    batch_control = task_execution_config.get('batch_control', {})

    return {
        'max_concurrent_workers': batch_control.get('max_concurrent_workers', 10),
        'max_chars_per_batch': batch_control.get('max_chars_per_batch', 50000),
        'default_provider': llm_config.get('default_provider', 'openai'),
        'available_providers': LLMFactory.get_supported_providers(),
        'retry_config': llm_config.get('retry', {
            'max_attempts': 3,
            'delay_seconds': 5.0,
            'exponential_backoff': True
        })
    }