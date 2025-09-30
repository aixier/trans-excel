"""Execution control API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import logging

from services.executor.worker_pool import worker_pool
from services.llm.llm_factory import LLMFactory
from services.persistence.task_persister import task_persister
from services.persistence.checkpoint_service import CheckpointService
from utils.session_manager import session_manager
from utils.config_manager import config_manager

# Initialize checkpoint service
checkpoint_service = CheckpointService()

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

        # Start auto-persistence for this session
        try:
            await task_persister.start_auto_persist(request.session_id)
            logger.info(f"Started auto-persistence for session {request.session_id}")
        except Exception as e:
            logger.warning(f"Failed to start auto-persistence: {e}")
            # Don't fail the execution if persistence fails

        logger.info(f"Started execution for session {request.session_id}")
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

    # Stop auto-persistence
    try:
        await task_persister.stop_auto_persist(session_id)
        logger.info(f"Stopped auto-persistence for session {session_id}")
    except Exception as e:
        logger.warning(f"Failed to stop auto-persistence: {e}")

    # Create final checkpoint before stopping
    try:
        checkpoint_info = await checkpoint_service.save_checkpoint(session_id, 'manual')
        logger.info(f"Created final checkpoint: {checkpoint_info['checkpoint_id']}")
    except Exception as e:
        logger.warning(f"Failed to create final checkpoint: {e}")

    logger.info(f"Stopped execution for session {session_id}")
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


@router.post("/checkpoint/{session_id}")
async def create_checkpoint(session_id: str, checkpoint_type: str = "manual"):
    """
    Create a checkpoint for the session.

    Args:
        session_id: Session ID
        checkpoint_type: Type of checkpoint (manual, auto, error)

    Returns:
        Checkpoint information
    """
    try:
        checkpoint_info = await checkpoint_service.save_checkpoint(session_id, checkpoint_type)
        logger.info(f"Created {checkpoint_type} checkpoint for session {session_id}")
        return checkpoint_info
    except Exception as e:
        logger.error(f"Failed to create checkpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkpoint: {str(e)}")


@router.post("/checkpoint/restore/{session_id}")
async def restore_checkpoint(session_id: str, checkpoint_id: Optional[str] = None):
    """
    Restore from a checkpoint.

    Args:
        session_id: Session ID
        checkpoint_id: Specific checkpoint ID (latest if None)

    Returns:
        Restore information
    """
    try:
        restore_info = await checkpoint_service.restore_checkpoint(session_id, checkpoint_id)
        logger.info(f"Restored checkpoint for session {session_id}")
        return restore_info
    except Exception as e:
        logger.error(f"Failed to restore checkpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restore checkpoint: {str(e)}")


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