"""
Translation API Endpoints - Tasks 6.1-6.4
FastAPI endpoints for translation data persistence
"""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

# Import models
from models.api_models import (
    SessionBatchRequest, TaskBatchRequest,
    BatchResponse, FlushResponse, QueryResponse,
    RecoveryResponse, DeleteResponse, CleanupResponse, StatsResponse,
    Pagination, SessionFilters, TaskFilters
)

# Import services
from services.buffer_manager import buffer_manager
from services.query_service import query_service
from services.recovery_service import recovery_service
from services.stats_service import stats_service
from services.cleanup_service import cleanup_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/translation", tags=["translation"])


# ============================================================================
# Batch Write APIs - Task 6.1
# ============================================================================

@router.post("/sessions/batch", response_model=BatchResponse, status_code=200)
async def batch_persist_sessions(request: SessionBatchRequest):
    """
    Batch persist sessions

    Accepts a batch of session data and adds to internal buffer.
    Data will be flushed to database when buffer is full or after flush_interval.

    - **sessions**: List of session data
    - Returns: Acceptance confirmation with count and timestamp
    """
    try:
        # Convert Pydantic models to dictionaries
        sessions_dict = [s.model_dump(exclude_none=True) for s in request.sessions]

        # Add to buffer
        await buffer_manager.add_sessions(sessions_dict)

        logger.info(f"Accepted {len(request.sessions)} sessions for persistence")

        return BatchResponse(
            status="accepted",
            count=len(request.sessions),
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Failed to persist sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/batch", response_model=BatchResponse, status_code=200)
async def batch_persist_tasks(request: TaskBatchRequest):
    """
    Batch persist tasks

    Accepts a batch of task data and adds to internal buffer.
    Data will be flushed to database when buffer is full or after flush_interval.

    - **tasks**: List of task data
    - Returns: Acceptance confirmation with count and timestamp
    """
    try:
        # Convert Pydantic models to dictionaries
        tasks_dict = [t.model_dump(exclude_none=True) for t in request.tasks]

        # Add to buffer
        await buffer_manager.add_tasks(tasks_dict)

        logger.info(f"Accepted {len(request.tasks)} tasks for persistence")

        return BatchResponse(
            status="accepted",
            count=len(request.tasks),
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Failed to persist tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flush", response_model=FlushResponse, status_code=200)
async def force_flush():
    """
    Force flush buffers to database

    Immediately flushes all buffered data to database without waiting for
    automatic flush triggers.

    - Returns: Flush statistics (sessions written, tasks written, duration)
    """
    try:
        result = await buffer_manager.flush()

        logger.info(
            f"Manual flush: {result['sessions']} sessions, "
            f"{result['tasks']} tasks in {result['duration_ms']}ms"
        )

        return FlushResponse(
            status="flushed" if result['sessions'] + result['tasks'] > 0 else "empty",
            sessions_written=result['sessions'],
            tasks_written=result['tasks'],
            duration_ms=result['duration_ms']
        )

    except Exception as e:
        logger.error(f"Failed to flush: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Query APIs - Task 6.2
# ============================================================================

@router.get("/sessions", response_model=QueryResponse, status_code=200)
async def query_sessions(
    status: Optional[str] = Query(None, description="Filter by status"),
    from_date: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    to_date: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    llm_provider: Optional[str] = Query(None, description="Filter by LLM provider"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: str = Query("created_at", description="Sort by field"),
    order: str = Query("desc", description="Sort order (asc/desc)")
):
    """
    Query sessions with pagination

    Query sessions with optional filters, pagination, and sorting.

    - **status**: Filter by status (pending, processing, completed, failed)
    - **from_date**: Filter from date (ISO format)
    - **to_date**: Filter to date (ISO format)
    - **llm_provider**: Filter by LLM provider
    - **page**: Page number (default: 1)
    - **page_size**: Page size (default: 20, max: 100)
    - **sort_by**: Sort by field (default: created_at)
    - **order**: Sort order (default: desc)
    - Returns: Paginated query results
    """
    try:
        # Parse filters
        filters = SessionFilters(
            status=status,
            from_date=datetime.fromisoformat(from_date) if from_date else None,
            to_date=datetime.fromisoformat(to_date) if to_date else None,
            llm_provider=llm_provider
        )

        # Parse pagination
        pagination = Pagination(
            page=page,
            page_size=min(page_size, 100),
            sort_by=sort_by,
            order=order
        )

        # Query
        result = await query_service.query_sessions(filters, pagination)

        logger.debug(f"Query sessions: {result.total} total, page {page}")

        return result

    except Exception as e:
        logger.error(f"Failed to query sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", status_code=200)
async def get_session(session_id: str):
    """
    Get single session by ID

    Retrieve detailed information for a specific session.

    - **session_id**: Session ID (UUID)
    - Returns: Session details
    """
    try:
        session = await query_service.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

        logger.debug(f"Retrieved session: {session_id}")

        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/tasks", response_model=QueryResponse, status_code=200)
async def get_session_tasks(
    session_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    sheet_name: Optional[str] = Query(None, description="Filter by sheet name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size")
):
    """
    Get tasks for a session

    Retrieve all tasks associated with a specific session.

    - **session_id**: Session ID
    - **status**: Filter by task status (optional)
    - **sheet_name**: Filter by sheet name (optional)
    - **page**: Page number (default: 1)
    - **page_size**: Page size (default: 20, max: 100)
    - Returns: Paginated task results
    """
    try:
        # Parse filters
        filters = TaskFilters(
            session_id=session_id,
            status=status,
            sheet_name=sheet_name
        )

        # Parse pagination
        pagination = Pagination(
            page=page,
            page_size=min(page_size, 100),
            sort_by="row_index",
            order="asc"
        )

        # Query
        result = await query_service.get_session_tasks(session_id, filters, pagination)

        logger.debug(f"Query session tasks: {result.total} total for session {session_id}")

        return result

    except Exception as e:
        logger.error(f"Failed to query session tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=QueryResponse, status_code=200)
async def query_tasks(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    sheet_name: Optional[str] = Query(None, description="Filter by sheet name"),
    from_date: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    to_date: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: str = Query("created_at", description="Sort by field"),
    order: str = Query("desc", description="Sort order (asc/desc)")
):
    """
    Query tasks with pagination

    Query tasks with optional filters, pagination, and sorting.

    - **session_id**: Filter by session ID
    - **status**: Filter by status (pending, processing, completed, failed)
    - **sheet_name**: Filter by sheet name
    - **from_date**: Filter from date (ISO format)
    - **to_date**: Filter to date (ISO format)
    - **page**: Page number (default: 1)
    - **page_size**: Page size (default: 20, max: 100)
    - **sort_by**: Sort by field (default: created_at)
    - **order**: Sort order (default: desc)
    - Returns: Paginated query results
    """
    try:
        # Parse filters
        filters = TaskFilters(
            session_id=session_id,
            status=status,
            sheet_name=sheet_name,
            from_date=datetime.fromisoformat(from_date) if from_date else None,
            to_date=datetime.fromisoformat(to_date) if to_date else None
        )

        # Parse pagination
        pagination = Pagination(
            page=page,
            page_size=min(page_size, 100),
            sort_by=sort_by,
            order=order
        )

        # Query
        result = await query_service.query_tasks(filters, pagination)

        logger.debug(f"Query tasks: {result.total} total, page {page}")

        return result

    except Exception as e:
        logger.error(f"Failed to query tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", status_code=200)
async def get_task(task_id: str):
    """
    Get single task by ID

    Retrieve detailed information for a specific task.

    - **task_id**: Task ID
    - Returns: Task details
    """
    try:
        task = await query_service.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        logger.debug(f"Retrieved task: {task_id}")

        return task

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Recovery APIs - Task 6.3
# ============================================================================

@router.get("/recovery/incomplete-sessions", status_code=200)
async def get_incomplete_sessions():
    """
    Get incomplete sessions

    Retrieve all sessions with status 'pending' or 'processing'.
    Useful for recovery after service restart.

    - Returns: List of incomplete sessions
    """
    try:
        sessions = await recovery_service.get_incomplete_sessions()

        logger.info(f"Retrieved {len(sessions)} incomplete sessions")

        return {
            "count": len(sessions),
            "sessions": sessions
        }

    except Exception as e:
        logger.error(f"Failed to get incomplete sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recovery/restore/{session_id}", response_model=RecoveryResponse, status_code=200)
async def restore_session(session_id: str):
    """
    Restore session data

    Restore complete data for a session including all incomplete tasks.

    - **session_id**: Session ID to restore
    - Returns: Complete session data with tasks
    """
    try:
        result = await recovery_service.restore_session(session_id)

        logger.info(f"Restored session {session_id} with {result['tasks_count']} tasks")

        return RecoveryResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to restore session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Management APIs - Task 6.4
# ============================================================================

@router.delete("/sessions/{session_id}", response_model=DeleteResponse, status_code=200)
async def delete_session(session_id: str):
    """
    Delete session

    Delete a session and all its associated tasks (CASCADE delete).

    - **session_id**: Session ID to delete
    - Returns: Deletion confirmation
    """
    try:
        from storage.registry import StorageBackendRegistry

        backend = StorageBackendRegistry.get_backend("translation_sessions")
        success = await backend.delete("translation_sessions", session_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

        logger.info(f"Deleted session: {session_id}")

        return DeleteResponse(
            status="deleted",
            session_id=session_id,
            timestamp=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/cleanup", response_model=CleanupResponse, status_code=200)
async def cleanup_sessions(
    completed_days: int = Query(90, ge=1, description="Remove completed sessions older than N days"),
    failed_days: int = Query(30, ge=1, description="Remove failed sessions older than N days"),
    dry_run: bool = Query(False, description="Dry run mode (count only, no deletion)")
):
    """
    Cleanup old sessions

    Remove old completed/failed sessions and their tasks.

    - **completed_days**: Remove completed sessions older than N days (default: 90)
    - **failed_days**: Remove failed sessions older than N days (default: 30)
    - **dry_run**: If true, only count without deleting (default: false)
    - Returns: Cleanup results
    """
    try:
        result = await cleanup_service.cleanup(completed_days, failed_days, dry_run)

        logger.info(
            f"Cleanup {'(dry run) ' if dry_run else ''}: "
            f"{result['deleted_sessions']} sessions, "
            f"{result['deleted_tasks']} tasks"
        )

        return CleanupResponse(**result)

    except Exception as e:
        logger.error(f"Failed to cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse, status_code=200)
async def get_stats():
    """
    Get statistics

    Get comprehensive statistics about sessions, tasks, and storage.

    - Returns: Statistics dictionary
    """
    try:
        stats = await stats_service.get_stats()

        logger.debug("Retrieved statistics")

        return StatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))