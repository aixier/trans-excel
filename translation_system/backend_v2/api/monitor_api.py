"""Monitoring API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
import pandas as pd

from services.executor.worker_pool import worker_pool
from services.monitor.performance_monitor import performance_monitor
from utils.session_manager import session_manager
from utils.json_converter import convert_numpy_types
from models.task_dataframe import TaskStatus

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


@router.get("/status/{session_id}")
async def get_execution_progress(session_id: str):
    """
    Get detailed execution progress.

    Args:
        session_id: Session ID

    Returns:
        Detailed progress information
    """
    # Check if this session is currently executing
    if worker_pool.current_session_id == session_id:
        status = worker_pool.get_status()

        # Add recent completions
        task_manager = session_manager.get_task_manager(session_id)
        if task_manager and task_manager.df is not None:
            # Get recently completed tasks
            completed_df = task_manager.df[
                task_manager.df['status'] == TaskStatus.COMPLETED
            ].sort_values('end_time', ascending=False).head(10)

            recent_completions = []
            for _, row in completed_df.iterrows():
                recent_completions.append({
                    'task_id': row['task_id'],
                    'source_text': row['source_text'][:50] + '...'
                                  if len(row['source_text']) > 50 else row['source_text'],
                    'result': row['result'][:50] + '...'
                             if len(row['result']) > 50 else row['result'],
                    'target_lang': row['target_lang'],
                    'confidence': row['confidence'],
                    'duration_ms': row['duration_ms']
                })

            status['recent_completions'] = recent_completions

            # Add current processing tasks
            processing_df = task_manager.df[
                task_manager.df['status'] == TaskStatus.PROCESSING
            ]
            status['current_tasks'] = list(processing_df['task_id'].values)

        return convert_numpy_types(status)

    # Check if session exists
    task_manager = session_manager.get_task_manager(session_id)
    if not task_manager:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get task statistics
    stats = task_manager.get_statistics()

    return convert_numpy_types({
        'status': 'idle',
        'session_id': session_id,
        'progress': {
            'total': stats['total'],
            'completed': stats['by_status'].get('completed', 0),
            'processing': stats['by_status'].get('processing', 0),
            'pending': stats['by_status'].get('pending', 0),
            'failed': stats['by_status'].get('failed', 0)
        },
        'completion_rate': (
            (stats['by_status'].get('completed', 0) / stats['total'] * 100)
            if stats['total'] > 0 else 0
        ),
        'message': 'No active execution for this session'
    })


@router.get("/dataframe/{session_id}")
async def get_task_dataframe(
    session_id: str,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: Optional[str] = None,
    sort_order: str = "asc"
):
    """
    Get task DataFrame content with pagination.

    Args:
        session_id: Session ID
        status: Filter by status (pending/processing/completed/failed)
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        sort_by: Column to sort by
        sort_order: Sort order (asc/desc)

    Returns:
        Paginated task DataFrame
    """
    task_manager = session_manager.get_task_manager(session_id)

    if not task_manager or task_manager.df is None:
        raise HTTPException(status_code=404, detail="No tasks found for this session")

    df = task_manager.df

    # Apply status filter if provided
    if status:
        df = df[df['status'] == status]

    # Apply sorting if specified
    if sort_by and sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=(sort_order == "asc"))

    # Get total count before pagination
    total_count = len(df)

    # Apply pagination
    df = df.iloc[offset:offset + limit]

    # Convert to JSON-friendly format
    df_dict = df.to_dict('records')

    # Handle datetime and NaN values
    for record in df_dict:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif hasattr(value, 'isoformat'):
                record[key] = value.isoformat()

    return convert_numpy_types({
        "session_id": session_id,
        "total_count": total_count,
        "returned_count": len(df_dict),
        "offset": offset,
        "limit": limit,
        "tasks": df_dict
    })


@router.get("/batches/{session_id}")
async def get_batch_status(session_id: str):
    """
    Get batch-level status information.

    Args:
        session_id: Session ID

    Returns:
        Batch status information
    """
    task_manager = session_manager.get_task_manager(session_id)

    if not task_manager or task_manager.df is None:
        raise HTTPException(status_code=404, detail="No tasks found for this session")

    # Group by batch_id and get status counts
    batch_status = {}

    for batch_id, group in task_manager.df.groupby('batch_id'):
        status_counts = group['status'].value_counts().to_dict()
        batch_status[batch_id] = {
            'total': len(group),
            'pending': status_counts.get(TaskStatus.PENDING, 0),
            'processing': status_counts.get(TaskStatus.PROCESSING, 0),
            'completed': status_counts.get(TaskStatus.COMPLETED, 0),
            'failed': status_counts.get(TaskStatus.FAILED, 0),
            'char_count': int(group['char_count'].sum())
        }

    return convert_numpy_types({
        'session_id': session_id,
        'batches': batch_status,
        'total_batches': len(batch_status)
    })


@router.get("/failed/{session_id}")
async def get_failed_tasks(session_id: str, limit: int = 50):
    """
    Get failed tasks with error details.

    Args:
        session_id: Session ID
        limit: Maximum number of failed tasks to return

    Returns:
        Failed tasks with error messages
    """
    task_manager = session_manager.get_task_manager(session_id)

    if not task_manager or task_manager.df is None:
        raise HTTPException(status_code=404, detail="No tasks found for this session")

    # Get failed tasks
    failed_df = task_manager.df[
        task_manager.df['status'] == TaskStatus.FAILED
    ].head(limit)

    failed_tasks = []
    for _, row in failed_df.iterrows():
        failed_tasks.append({
            'task_id': row['task_id'],
            'batch_id': row['batch_id'],
            'source_text': row['source_text'],
            'target_lang': row['target_lang'],
            'error_message': row.get('error_message', 'Unknown error'),
            'retry_count': row.get('retry_count', 0)
        })

    return convert_numpy_types({
        'session_id': session_id,
        'failed_tasks': failed_tasks,
        'total_failed': len(task_manager.df[task_manager.df['status'] == TaskStatus.FAILED])
    })


@router.get("/summary/{session_id}")
async def get_execution_summary(session_id: str):
    """
    Get execution summary with statistics.

    Args:
        session_id: Session ID

    Returns:
        Execution summary
    """
    task_manager = session_manager.get_task_manager(session_id)

    if not task_manager:
        raise HTTPException(status_code=404, detail="Session not found")

    stats = task_manager.get_statistics()

    # Calculate additional metrics
    summary = {
        'session_id': session_id,
        'task_statistics': stats,
        'language_distribution': stats.get('by_language', {}),
        'group_distribution': stats.get('by_group', {}),
        'total_characters': stats.get('total_chars', 0),
        'average_confidence': stats.get('avg_confidence', 0.0)
    }

    # Add cost estimation if tasks are completed
    if task_manager.df is not None and not task_manager.df.empty:
        completed_df = task_manager.df[task_manager.df['status'] == TaskStatus.COMPLETED]

        if not completed_df.empty:
            summary['execution_metrics'] = {
                'total_duration_ms': int(completed_df['duration_ms'].sum()),
                'average_duration_ms': int(completed_df['duration_ms'].mean()),
                'total_tokens': int(completed_df['token_count'].sum()),
                'estimated_cost': float(completed_df['cost'].sum()) if 'cost' in completed_df.columns else 0.0
            }

    return convert_numpy_types(summary)


@router.get("/performance")
async def get_performance_metrics(session_id: Optional[str] = None, hours: int = 1):
    """
    Get system performance metrics.

    Args:
        session_id: Specific session ID (optional)
        hours: Hours of historical data to retrieve

    Returns:
        Performance metrics
    """
    try:
        # Get current metrics
        current = performance_monitor.get_current_metrics()

        # Get historical metrics
        historical = performance_monitor.get_historical_metrics(session_id, hours)

        return convert_numpy_types({
            'current': current,
            'historical': historical
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")