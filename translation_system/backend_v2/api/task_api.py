"""Task API endpoints."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import tempfile
import os
import pandas as pd
import asyncio
import logging

from services.task_splitter import TaskSplitter
from services.batch_allocator import BatchAllocator
from utils.session_manager import session_manager
from utils.json_converter import convert_numpy_types


router = APIRouter(prefix="/api/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)

# Store splitting progress for each session
splitting_progress = {}


class ContextOptions(BaseModel):
    """Context extraction options."""
    game_info: bool = True
    comments: bool = True
    neighbors: bool = True
    content_analysis: bool = True
    sheet_type: bool = True


class SplitRequest(BaseModel):
    """Request model for task splitting."""
    session_id: str
    source_lang: Optional[str] = None  # CH/EN, None for auto-detect
    target_langs: List[str]  # [PT, TH, VN]
    extract_context: Optional[bool] = True  # Whether to extract context (slower but more accurate)
    context_options: Optional[ContextOptions] = None  # Which context types to extract (column header always included)


class TaskPreview(BaseModel):
    """Task preview model."""
    task_id: str
    source_text: str
    target_lang: str
    batch_id: str
    group_id: str
    char_count: int


async def _perform_split_async(session_id: str, source_lang: Optional[str], target_langs: List[str], extract_context: bool = True, context_options: Optional[Dict[str, bool]] = None):
    """Background task to perform the actual splitting."""
    try:
        # Update progress
        splitting_progress[session_id] = {
            'status': 'processing',
            'progress': 0,
            'message': '开始拆分任务...',
            'total_sheets': 0,
            'processed_sheets': 0
        }

        # Get session data
        excel_df = session_manager.get_excel_df(session_id)
        if not excel_df:
            splitting_progress[session_id] = {
                'status': 'failed',
                'message': 'Session not found or Excel not loaded'
            }
            return

        game_info = session_manager.get_game_info(session_id)

        # Update progress
        sheet_names = excel_df.get_sheet_names()
        total_sheets = len(sheet_names)
        splitting_progress[session_id].update({
            'total_sheets': total_sheets,
            'progress': 10,
            'message': f'共 {total_sheets} 个表格，开始拆分... (上下文提取: {"开启" if extract_context else "关闭"})'
        })

        # Create task splitter with optimization flag and context options
        splitter = TaskSplitter(excel_df, game_info, extract_context=extract_context, context_options=context_options)

        # Override split_tasks to report progress
        all_tasks = []
        task_counter = 0

        for idx, sheet_name in enumerate(sheet_names, 1):
            splitting_progress[session_id].update({
                'processed_sheets': idx,
                'progress': 10 + (idx / total_sheets) * 70,  # 10-80%
                'message': f'正在处理表格: {sheet_name} ({idx}/{total_sheets})'
            })

            sheet_tasks = splitter._process_sheet(
                sheet_name,
                source_lang,
                target_langs,
                task_counter
            )
            all_tasks.extend(sheet_tasks)
            task_counter += len(sheet_tasks)

            # Small delay to allow other tasks
            await asyncio.sleep(0.01)

        # Allocate batches
        splitting_progress[session_id].update({
            'progress': 85,
            'message': f'分配批次... (共 {len(all_tasks)} 个任务)'
        })
        all_tasks = splitter.batch_allocator.allocate_batches(all_tasks)

        # Create DataFrame
        splitting_progress[session_id].update({
            'progress': 90,
            'message': '创建任务数据表...'
        })

        for task in all_tasks:
            splitter.task_manager.add_task(task)

        # Store task manager in session
        session_manager.set_task_manager(session_id, splitter.task_manager)

        # Get statistics
        stats = splitter.task_manager.get_statistics()

        # Calculate batch statistics
        batch_allocator = BatchAllocator()
        tasks_list = splitter.task_manager.df.to_dict('records')
        batch_stats = batch_allocator.calculate_batch_statistics(tasks_list)

        # 计算任务类型的批次分布
        type_batch_distribution = {}
        for task in tasks_list:
            batch_id = task.get('batch_id', '')
            task_type = task.get('task_type', 'normal')

            if batch_id:
                parts = batch_id.split('_')
                if len(parts) >= 3:
                    type_key = task_type.lower()
                    if type_key not in type_batch_distribution:
                        type_batch_distribution[type_key] = set()
                    type_batch_distribution[type_key].add(batch_id)

        type_batch_counts = {
            task_type: len(batch_ids)
            for task_type, batch_ids in type_batch_distribution.items()
        }

        # Success
        splitting_progress[session_id] = {
            'status': 'completed',
            'progress': 100,
            'message': '拆分完成!',
            'task_count': stats['total'],
            'batch_count': batch_stats['total_batches'],
            'batch_distribution': batch_stats['batch_distribution'],
            'type_batch_distribution': type_batch_counts,
            'statistics': stats
        }

    except Exception as e:
        logger.error(f"Error in async split: {e}", exc_info=True)
        splitting_progress[session_id] = {
            'status': 'failed',
            'progress': 0,
            'message': f'拆分失败: {str(e)}'
        }


@router.post("/split")
async def split_tasks(request: SplitRequest, background_tasks: BackgroundTasks):
    """
    Split Excel into translation tasks (async mode).

    Args:
        request: Split request with session_id and languages

    Returns:
        Immediate response with job status, use /split/status to check progress
    """
    # Get session data
    excel_df = session_manager.get_excel_df(request.session_id)
    if not excel_df:
        raise HTTPException(status_code=404, detail="Session not found or Excel not loaded")

    # Check if already splitting
    if request.session_id in splitting_progress:
        current = splitting_progress[request.session_id]
        if current.get('status') == 'processing':
            return {
                "session_id": request.session_id,
                "status": "already_processing",
                "message": "任务拆分正在进行中，请稍候",
                "progress": current.get('progress', 0)
            }

    # Convert context_options to dict if provided
    context_opts = None
    if request.context_options:
        context_opts = request.context_options.dict()

    # Start async splitting
    background_tasks.add_task(
        _perform_split_async,
        request.session_id,
        request.source_lang,
        request.target_langs,
        request.extract_context,
        context_opts
    )

    # Initialize progress
    splitting_progress[request.session_id] = {
        'status': 'processing',
        'progress': 0,
        'message': '任务已提交，开始拆分...'
    }

    return {
        "session_id": request.session_id,
        "status": "processing",
        "message": "任务拆分已启动，请使用 /api/tasks/split/status/{session_id} 查询进度",
        "status_url": f"/api/tasks/split/status/{request.session_id}"
    }


@router.get("/split/status/{session_id}")
async def get_split_status(session_id: str):
    """
    Get task splitting progress.

    Args:
        session_id: Session ID

    Returns:
        Splitting progress and status
    """
    if session_id not in splitting_progress:
        # Check if tasks already exist
        task_manager = session_manager.get_task_manager(session_id)
        if task_manager and task_manager.df is not None:
            stats = task_manager.get_statistics()
            return {
                "session_id": session_id,
                "status": "completed",
                "progress": 100,
                "message": "任务已完成",
                "task_count": stats['total'],
                "statistics": stats
            }

        return {
            "session_id": session_id,
            "status": "not_found",
            "message": "未找到拆分任务"
        }

    progress_info = splitting_progress[session_id]

    # Add preview and download URL if completed
    if progress_info.get('status') == 'completed':
        task_manager = session_manager.get_task_manager(session_id)
        if task_manager and task_manager.df is not None:
            # Get preview (first 10 tasks)
            preview = []
            for _, row in task_manager.df.head(10).iterrows():
                preview.append({
                    'task_id': row['task_id'],
                    'source_text': row['source_text'][:50] + '...' if len(row['source_text']) > 50 else row['source_text'],
                    'target_lang': row['target_lang'],
                    'batch_id': row['batch_id'],
                    'group_id': row['group_id'],
                    'char_count': row['char_count']
                })

            progress_info['preview'] = preview
            progress_info['download_url'] = f"/api/tasks/export/{session_id}"

    return convert_numpy_types({
        "session_id": session_id,
        **progress_info
    })


@router.get("/export/{session_id}")
async def export_tasks(session_id: str):
    """
    Export task DataFrame as Excel file.

    Args:
        session_id: Session ID

    Returns:
        Excel file download
    """
    # Get task manager
    task_manager = session_manager.get_task_manager(session_id)
    if not task_manager or task_manager.df is None:
        raise HTTPException(status_code=404, detail="No tasks found for this session")

    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_path = tmp_file.name

        # Export to Excel
        task_manager.export_to_excel(tmp_path)

        # Return file
        return FileResponse(
            path=tmp_path,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=f"tasks_{session_id[:8]}.xlsx"
        )

    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Error exporting tasks: {str(e)}")


@router.get("/status/{session_id}")
async def get_task_status(session_id: str):
    """
    Get task statistics for a session.

    This endpoint returns the statistics of already split tasks.
    If tasks are not yet split, check /split/status/{session_id} first.
    """
    # First check if splitting is in progress
    if session_id in splitting_progress:
        split_status = splitting_progress[session_id]
        if split_status.get('status') == 'processing':
            return {
                "session_id": session_id,
                "status": "splitting_in_progress",
                "message": "任务正在拆分中，请使用 /api/tasks/split/status/{session_id} 查询拆分进度",
                "split_progress": split_status.get('progress', 0),
                "split_message": split_status.get('message', '')
            }

    # Check if tasks exist
    task_manager = session_manager.get_task_manager(session_id)

    if not task_manager:
        # Check if split was attempted
        if session_id in splitting_progress:
            split_info = splitting_progress[session_id]
            if split_info.get('status') == 'failed':
                return {
                    "session_id": session_id,
                    "status": "split_failed",
                    "message": f"任务拆分失败: {split_info.get('message', '未知错误')}",
                    "has_tasks": False
                }

        raise HTTPException(status_code=404, detail="No tasks found for this session. Please split tasks first.")

    stats = task_manager.get_statistics()

    return convert_numpy_types({
        "session_id": session_id,
        "status": "ready",
        "statistics": stats,
        "has_tasks": task_manager.df is not None and len(task_manager.df) > 0
    })


@router.get("/dataframe/{session_id}")
async def get_task_dataframe(
    session_id: str,
    status: Optional[str] = None,
    limit: Optional[int] = 100
):
    """
    Get task DataFrame content.

    Args:
        session_id: Session ID
        status: Filter by status (pending/processing/completed/failed)
        limit: Maximum number of tasks to return

    Returns:
        Task DataFrame as JSON
    """
    task_manager = session_manager.get_task_manager(session_id)

    if not task_manager or task_manager.df is None:
        raise HTTPException(status_code=404, detail="No tasks found for this session")

    df = task_manager.df

    # Apply status filter if provided
    if status:
        df = df[df['status'] == status]

    # Apply limit
    if limit and len(df) > limit:
        df = df.head(limit)

    # Convert to JSON-friendly format
    # Handle datetime columns
    df_dict = df.to_dict('records')
    for record in df_dict:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif hasattr(value, 'isoformat'):
                record[key] = value.isoformat()

    return convert_numpy_types({
        "session_id": session_id,
        "total_count": len(task_manager.df),
        "returned_count": len(df_dict),
        "tasks": df_dict
    })