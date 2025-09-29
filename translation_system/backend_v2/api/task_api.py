"""Task API endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import tempfile
import os
import pandas as pd

from services.task_splitter import TaskSplitter
from services.batch_allocator import BatchAllocator
from utils.session_manager import session_manager
from utils.json_converter import convert_numpy_types


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class SplitRequest(BaseModel):
    """Request model for task splitting."""
    session_id: str
    source_lang: Optional[str] = None  # CH/EN, None for auto-detect
    target_langs: List[str]  # [PT, TH, VN]


class TaskPreview(BaseModel):
    """Task preview model."""
    task_id: str
    source_text: str
    target_lang: str
    batch_id: str
    group_id: str
    char_count: int


@router.post("/split")
async def split_tasks(request: SplitRequest):
    """
    Split Excel into translation tasks.

    Args:
        request: Split request with session_id and languages

    Returns:
        Task statistics and preview
    """
    # Get session data
    excel_df = session_manager.get_excel_df(request.session_id)
    if not excel_df:
        raise HTTPException(status_code=404, detail="Session not found or Excel not loaded")

    game_info = session_manager.get_game_info(request.session_id)

    try:
        # Create task splitter
        splitter = TaskSplitter(excel_df, game_info)

        # Split tasks
        task_manager = splitter.split_tasks(
            source_lang=request.source_lang,
            target_langs=request.target_langs
        )

        # Store task manager in session
        session_manager.set_task_manager(request.session_id, task_manager)

        # Get statistics
        stats = task_manager.get_statistics()

        # Calculate batch statistics
        batch_allocator = BatchAllocator()
        if task_manager.df is not None:
            tasks_list = task_manager.df.to_dict('records')
            batch_stats = batch_allocator.calculate_batch_statistics(tasks_list)

            # 计算任务类型的批次分布
            type_batch_distribution = {}
            for task in tasks_list:
                batch_id = task.get('batch_id', '')
                task_type = task.get('task_type', 'normal')

                # 从batch_id中解析语言和类型
                # 格式: BATCH_{lang}_{TYPE}_{num}
                if batch_id:
                    parts = batch_id.split('_')
                    if len(parts) >= 3:
                        # 统计每个类型的批次
                        type_key = task_type.lower()
                        if type_key not in type_batch_distribution:
                            type_batch_distribution[type_key] = set()
                        type_batch_distribution[type_key].add(batch_id)

            # 转换为计数
            type_batch_counts = {
                task_type: len(batch_ids)
                for task_type, batch_ids in type_batch_distribution.items()
            }
        else:
            batch_stats = {'total_batches': 0, 'batch_distribution': {}}
            type_batch_counts = {}

        # Get preview (first 10 tasks)
        preview = []
        if task_manager.df is not None and len(task_manager.df) > 0:
            for _, row in task_manager.df.head(10).iterrows():
                preview.append(TaskPreview(
                    task_id=row['task_id'],
                    source_text=row['source_text'][:50] + '...' if len(row['source_text']) > 50 else row['source_text'],
                    target_lang=row['target_lang'],
                    batch_id=row['batch_id'],
                    group_id=row['group_id'],
                    char_count=row['char_count']
                ))

        return convert_numpy_types({
            "session_id": request.session_id,
            "task_count": stats['total'],
            "batch_count": batch_stats['total_batches'],
            "batch_distribution": batch_stats['batch_distribution'],
            "type_batch_distribution": type_batch_counts,  # 添加任务类型批次分布
            "statistics": stats,
            "preview": preview,
            "download_url": f"/api/tasks/export/{request.session_id}"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error splitting tasks: {str(e)}")


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
    """Get task statistics for a session."""
    task_manager = session_manager.get_task_manager(session_id)

    if not task_manager:
        raise HTTPException(status_code=404, detail="No tasks found for this session")

    stats = task_manager.get_statistics()

    return convert_numpy_types({
        "session_id": session_id,
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