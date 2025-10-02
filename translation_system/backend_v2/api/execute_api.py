"""Execution control API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import logging

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


@router.post("/start")
async def start_execution(request: ExecuteRequest):
    """
    Start translation execution.

    Args:
        request: Execution request with session_id

    Returns:
        Execution status
    """
    # Check if session exists
    task_manager = session_manager.get_task_manager(request.session_id)
    if not task_manager:
        raise HTTPException(status_code=404, detail="Session not found")

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
        result = await worker_pool.start_execution(request.session_id, llm_provider)

        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])

        # Start progress monitoring for WebSocket updates
        try:
            from services.executor.progress_tracker import progress_tracker
            await progress_tracker.start_progress_monitoring(request.session_id)
            logger.info(f"Started progress monitoring for session {request.session_id}")
        except Exception as e:
            logger.warning(f"Failed to start progress monitoring: {e}")
            # Don't fail the execution if monitoring fails

        logger.info(f"Started execution for session {request.session_id} (memory-only mode)")
        return result

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
        Execution status
    """
    # Check if this session is currently executing
    if worker_pool.current_session_id == session_id:
        return worker_pool.get_status()

    # Check if session exists
    if not session_manager.get_task_manager(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    # Session exists but not executing
    return {
        'status': 'idle',
        'session_id': session_id,
        'message': 'No active execution for this session'
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