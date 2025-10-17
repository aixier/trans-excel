"""Execution control API endpoints - Refactored for Pipeline Architecture."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import os
import logging

from models.pipeline_session import TransformationStage
from services.executor.worker_pool import worker_pool
from services.factories.processor_factory import processor_factory
from utils.pipeline_session_manager import pipeline_session_manager
from utils.config_manager import config_manager

router = APIRouter(prefix="/api/execute", tags=["execute"])
logger = logging.getLogger(__name__)


class ExecuteRequest(BaseModel):
    """Execute request model."""
    session_id: str
    processor: Optional[str] = None  # Processor name (e.g., 'llm_qwen', 'uppercase')
    provider: Optional[str] = None  # [DEPRECATED] Override LLM provider (use processor instead)
    max_workers: Optional[int] = None  # Override max workers
    glossary_id: Optional[str] = None  # Glossary ID (simplified parameter)
    glossary_config: Optional[Dict] = None  # Glossary configuration (advanced)


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

    # Validation 1 - Session exists
    session = pipeline_session_manager.get_session(session_id)
    if not session:
        logger.error(f"Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")

    # Validation 2 - TaskManager exists (with lazy loading support)
    task_manager = pipeline_session_manager.get_tasks(session_id)
    if not task_manager:
        logger.error(f"Task manager not found for session {session_id}")
        raise HTTPException(status_code=404, detail="Task manager not found. Please split tasks first.")

    # Validation 3 - Split is complete
    # Check if task manager has tasks (more reliable than stage for backward compatibility)
    if task_manager.df is None or len(task_manager.df) == 0:
        detail = "No tasks found. Please split tasks first."
        logger.error(f"Session {session_id}: {detail}")
        raise HTTPException(status_code=400, detail=detail)

    # Also check stage if it's set
    if session.stage is not None and session.stage != TransformationStage.SPLIT_COMPLETE and session.stage != TransformationStage.COMPLETED:
        detail = f"Session not ready: stage is {session.stage.value}. Must complete split first."
        logger.error(f"Session {session_id}: {detail}")
        raise HTTPException(status_code=400, detail=detail)

    logger.info(f"All validations passed for session {session_id}")

    # Initialize/Reset execution progress
    # Note: PipelineSession doesn't have execution_progress attribute - handle via metadata
    logger.info(f"Initializing execution for session {session_id}")

    # Reset tasks to PENDING if re-executing
    if session.stage == TransformationStage.COMPLETED:
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

    # Override max workers if specified
    if request.max_workers:
        worker_pool.max_workers = request.max_workers

    # === Processor Selection Logic ===
    # Priority:
    # 1. Explicit processor parameter
    # 2. Map rule_set to processor
    # 3. Fall back to LLM provider (backward compatibility)
    processor_name = request.processor

    if not processor_name:
        # Auto-determine processor from rule_set
        rule_set = session.metadata.get('rule_set', 'translation')

        # Map rule_set to processor
        rule_to_processor_map = {
            'translation': 'llm_qwen',
            'caps_only': 'uppercase'
        }
        processor_name = rule_to_processor_map.get(rule_set, 'llm_qwen')
        logger.info(f"Auto-selected processor '{processor_name}' for rule_set '{rule_set}'")

    try:
        # Create processor via factory
        llm_provider = processor_factory.create_processor(processor_name)
        logger.info(f"Created processor: {processor_name}")

        # Build glossary_config from glossary_id if provided
        glossary_config = request.glossary_config
        if request.glossary_id and not glossary_config:
            glossary_config = {'id': request.glossary_id}
            logger.info(f"Using glossary_id: {request.glossary_id}")

        # Start execution
        result = await worker_pool.start_execution(
            session_id,
            llm_provider,
            glossary_config=glossary_config  # ✨ Pass glossary config
        )

        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])

        # Start progress monitoring for WebSocket updates
        try:
            from services.executor.progress_tracker import progress_tracker
            await progress_tracker.start_progress_monitoring(session_id)
            logger.info(f"Progress monitoring initialized for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to start progress monitoring: {e}")
            # Don't fail the execution if monitoring fails

        # Update session stage
        session.update_stage(TransformationStage.EXECUTING)
        pipeline_session_manager._sync_to_cache(session)
        logger.info(f"Execution started for session {session_id} (synced to cache)")

        # Return execution status with progress
        response = {
            **result,
            'progress': {
                'total': result.get('total_tasks', 0),
                'completed': 0,
                'processing': 0,
                'pending': result.get('total_tasks', 0),
                'failed': 0
            }
        }
        logger.info(f"Started execution for session {session_id}")
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start execution: {str(e)}")
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
        Execution status including stage and progress
    """
    # Check if session exists
    session = pipeline_session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if this session is currently executing
    if worker_pool.current_session_id == session_id:
        # Get real-time status from worker_pool
        return worker_pool.get_status()

    # Not currently executing - check stage and tasks
    task_manager = pipeline_session_manager.get_tasks(session_id)
    if not task_manager:
        raise HTTPException(
            status_code=404,
            detail="Task manager not found. Please split tasks first before checking execution status."
        )

    # Get task statistics
    stats = task_manager.get_statistics()
    total = stats.get('total', 0)
    completed = stats.get('by_status', {}).get('completed', 0)

    # Determine status based on stage and task completion
    if session.stage == TransformationStage.COMPLETED:
        return {
            'status': 'completed',
            'session_id': session_id,
            'statistics': stats,
            'message': '翻译已完成',
            'ready_for_download': True
        }
    elif session.stage == TransformationStage.EXECUTING:
        # Was executing but not running now
        if total > 0 and completed >= total:
            # All tasks completed, update stage
            session.update_stage(TransformationStage.COMPLETED)
            pipeline_session_manager._sync_to_cache(session)
            return {
                'status': 'completed',
                'session_id': session_id,
                'statistics': stats,
                'message': '翻译已完成',
                'ready_for_download': True
            }
        else:
            return {
                'status': 'stopped',
                'session_id': session_id,
                'statistics': stats,
                'message': '执行已停止'
            }
    elif session.stage == TransformationStage.SPLIT_COMPLETE:
        # Tasks exist but execution never started
        return {
            'status': 'idle',
            'session_id': session_id,
            'message': 'No execution started for this session',
            'ready_for_execution': True
        }
    else:
        return {
            'status': 'unknown',
            'session_id': session_id,
            'stage': session.stage.value,
            'message': f'Session in unexpected stage: {session.stage.value}'
        }


@router.get("/config")
async def get_execution_config():
    """
    Get execution configuration.

    Returns:
        Current execution configuration including available processors
    """
    config = config_manager.get_config()
    llm_config = config.get('llm', {})
    task_execution_config = config.get('task_execution', {})
    batch_control = task_execution_config.get('batch_control', {})

    # Get available processors from factory
    available_processors = processor_factory.list_available_processors()

    return {
        'max_concurrent_workers': batch_control.get('max_concurrent_workers', 10),
        'max_chars_per_batch': batch_control.get('max_chars_per_batch', 50000),
        'default_processor': processor_factory.config.get('default_processor', 'llm_qwen'),
        'available_processors': available_processors,
        'retry_config': llm_config.get('retry', {
            'max_attempts': 3,
            'delay_seconds': 5.0,
            'exponential_backoff': True
        })
    }