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

from models.session_state import SessionStage
from services.split_state import SplitProgress, SplitStatus, SplitStage
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


def _sync_split_progress(session, split_progress):
    """Helper function to sync split_progress to both legacy dict and cache.

    Args:
        session: SessionData instance (already retrieved, don't re-fetch to avoid object replacement)
        split_progress: SplitProgress instance to sync
    """
    # Update legacy dict for backward compatibility
    splitting_progress[session.session_id] = split_progress.to_dict()

    # Update session's split_progress and sync to cache
    session.split_progress = split_progress
    session_manager._sync_to_cache(session)


async def _perform_split_async(session_id: str, source_lang: Optional[str], target_langs: List[str], extract_context: bool = True, context_options: Optional[Dict[str, bool]] = None):
    """Background task to perform the actual splitting."""
    # ✨ T08: Get session and split_progress
    session = session_manager.get_session(session_id)
    if not session or not session.split_progress:
        logger.error(f"Session or split_progress not found for {session_id}")
        return

    split_progress = session.split_progress

    try:
        logger.info(f"========== 开始任务拆分 ==========")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"源语言: {source_lang or 'auto-detect'}")
        logger.info(f"目标语言: {target_langs}")
        logger.info(f"上下文提取: {extract_context}")

        # Update progress
        split_progress.update(
            status=SplitStatus.PROCESSING,
            stage=SplitStage.ANALYZING,
            progress=0,
            message='开始拆分任务...'
        )
        _sync_split_progress(session, split_progress)
        logger.info(f"初始化进度: {split_progress.to_dict()}")

        # Get session data (with lazy loading support)
        excel_df = session_manager.get_excel_df(session_id)
        if not excel_df:
            split_progress.mark_failed('Session not found or Excel not loaded')
            _sync_split_progress(session, split_progress)
            return

        game_info = session.game_info

        # Update progress
        sheet_names = excel_df.get_sheet_names()
        total_sheets = len(sheet_names)
        split_progress.update(
            progress=10,
            message=f'共 {total_sheets} 个表格，开始拆分... (上下文提取: {"开启" if extract_context else "关闭"})'
        )
        split_progress.metadata['total_sheets'] = total_sheets
        split_progress.metadata['processed_sheets'] = 0
        splitting_progress[session_id] = split_progress.to_dict()

        # Create task splitter with optimization flag and context options
        splitter = TaskSplitter(excel_df, game_info, extract_context=extract_context, context_options=context_options)

        # Override split_tasks to report progress
        all_tasks = []
        task_counter = 0

        for idx, sheet_name in enumerate(sheet_names, 1):
            progress_percent = 10 + (idx / total_sheets) * 70
            split_progress.update(
                stage=SplitStage.ANALYZING,
                progress=progress_percent,
                message=f'正在处理表格: {sheet_name} ({idx}/{total_sheets})'
            )
            split_progress.metadata['processed_sheets'] = idx
            splitting_progress[session_id] = split_progress.to_dict()
            logger.info(f"处理表格 {idx}/{total_sheets}: {sheet_name}, 进度: {progress_percent:.1f}%")

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
        logger.info(f"拆分完成，共生成 {len(all_tasks)} 个任务，开始分配批次...")
        split_progress.update(
            stage=SplitStage.ALLOCATING,
            progress=85,
            message=f'分配批次... (共 {len(all_tasks)} 个任务)'
        )
        splitting_progress[session_id] = split_progress.to_dict()
        all_tasks = splitter.batch_allocator.allocate_batches(all_tasks)
        logger.info(f"批次分配完成")

        # Create DataFrame (use batch method for performance)
        split_progress.update(
            stage=SplitStage.CREATING_DF,
            progress=90,
            message='创建任务数据表...'
        )
        splitting_progress[session_id] = split_progress.to_dict()
        logger.info("开始创建任务DataFrame...")

        # Use batch add for much better performance
        splitter.task_manager.add_tasks_batch(all_tasks)

        logger.info(f"任务DataFrame创建完成，共 {len(all_tasks)} 个任务")

        # ✨ T08 KEY: Mark as SAVING before actual save (fixes 0-42s race condition)
        split_progress.mark_saving()
        split_progress.update(progress=93, message='保存任务管理器...')
        splitting_progress[session_id] = split_progress.to_dict()
        logger.info(f"✨ Marked as SAVING, ready_for_next_stage={split_progress.ready_for_next_stage}")

        # Store task manager in session (this may take 0-42 seconds)
        success = session_manager.set_task_manager(session_id, splitter.task_manager)
        if not success:
            raise Exception(f"Failed to save task_manager to session {session_id}")

        logger.info(f"Task manager已保存到session: {session_id}")

        # ✅ Save task_manager to file for cross-worker access
        try:
            from pathlib import Path
            import os

            # Create data/sessions directory if it doesn't exist
            data_dir = Path(__file__).parent.parent / 'data' / 'sessions'
            data_dir.mkdir(parents=True, exist_ok=True)

            # Save to parquet file
            task_file_path = str(data_dir / f'{session_id}_tasks.parquet')
            splitter.task_manager.df.to_parquet(task_file_path, index=False)

            # Store file path in session metadata for cross-worker loading
            session_manager.set_metadata(session_id, 'task_file_path', task_file_path)

            # Sync to cache so other workers can see the file path
            session = session_manager.get_session(session_id)
            if session:
                session_manager._sync_to_cache(session)

            logger.info(f"Task manager已保存到文件: {task_file_path} ({len(splitter.task_manager.df)} tasks)")
        except Exception as e:
            logger.error(f"Failed to save task_manager to file: {e}")
            # Don't fail the whole operation if file save fails

        # Verification stage
        split_progress.update(
            stage=SplitStage.VERIFYING,
            progress=98,
            message='验证数据完整性...'
        )
        splitting_progress[session_id] = split_progress.to_dict()

        verify_manager = session_manager.get_task_manager(session_id)
        if not verify_manager:
            raise Exception(f"Failed to verify task_manager in session {session_id}")
        logger.info(f"Task manager验证成功")

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

        # ✨ T08 KEY: Mark as COMPLETED (ONLY here is ready_for_next_stage=True)
        completion_metadata = {
            'task_count': stats['total'],
            'batch_count': batch_stats['total_batches'],
            'batch_distribution': batch_stats['batch_distribution'],
            'type_batch_distribution': type_batch_counts,
            'statistics': stats
        }
        split_progress.mark_completed(completion_metadata)

        # ✨ Update session global stage to SPLIT_COMPLETE
        session.session_status.update_stage(SessionStage.SPLIT_COMPLETE)

        # Sync split_progress and session_status to cache (single sync call)
        _sync_split_progress(session, split_progress)

        logger.info(f"========== 任务拆分完成 ==========")
        logger.info(f"总任务数: {stats['total']}")
        logger.info(f"批次数: {batch_stats['total_batches']}")
        logger.info(f"任务类型分布: {type_batch_counts}")
        logger.info(f"✨ 状态: ready_for_next_stage = {split_progress.ready_for_next_stage}")
        logger.info(f"✨ Session stage: {session.session_status.stage.value}")

    except Exception as e:
        logger.error(f"========== 任务拆分失败 ==========")
        logger.error(f"错误: {e}", exc_info=True)
        split_progress.mark_failed(str(e))
        _sync_split_progress(session, split_progress)


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
    logger.info(f"Split request for session: {request.session_id}")

    # ✨ T07: Validation 1 - Session exists
    session = session_manager.get_session(request.session_id)
    if not session:
        logger.error(f"Session {request.session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")

    # ✨ T07: Validation 2 - Excel loaded (with lazy loading support)
    excel_df = session_manager.get_excel_df(request.session_id)
    if not excel_df:
        logger.error(f"Session {request.session_id} has no Excel data")
        raise HTTPException(status_code=404, detail="Excel not loaded for this session")

    # ✨ T07: Validation 3 - Session stage check
    if not session.session_status.stage.can_split():
        logger.error(f"Session {request.session_id} cannot split in stage: {session.session_status.stage.value}")
        raise HTTPException(
            status_code=400,
            detail=f"Cannot split in stage: {session.session_status.stage.value}. Must be in ANALYZED stage."
        )

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

    # ✨ T07: Initialize SplitProgress
    split_progress = session.init_split_progress()
    split_progress.update(
        status=SplitStatus.PROCESSING,
        stage=SplitStage.ANALYZING,
        progress=0,
        message="开始拆分任务..."
    )

    # Sync to legacy dict for backward compatibility
    splitting_progress[request.session_id] = split_progress.to_dict()

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

    return split_progress.to_dict()


@router.get("/split/status/{session_id}")
async def get_split_status(session_id: str):
    """
    Get task splitting progress.

    Args:
        session_id: Session ID

    Returns:
        Splitting progress and status
    """
    # ✨ T09: Priority 1 - Get from Session.split_progress
    session = session_manager.get_session(session_id)
    if session and session.split_progress:
        progress_dict = session.split_progress.to_dict()

        # Add preview and download URL if completed
        if session.split_progress.status == SplitStatus.COMPLETED:
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

                progress_dict['preview'] = preview
                progress_dict['download_url'] = f"/api/tasks/export/{session_id}"

        return convert_numpy_types(progress_dict)

    # ✨ T09: Fallback - Check legacy dict for backward compatibility
    if session_id in splitting_progress:
        return convert_numpy_types(splitting_progress[session_id])

    # ✨ T09: Check if session exists but split not started
    if session:
        # Check if tasks already exist (from previous session)
        task_manager = session_manager.get_task_manager(session_id)
        if task_manager and task_manager.df is not None:
            stats = task_manager.get_statistics()
            return {
                "session_id": session_id,
                "status": "completed",
                "ready_for_next_stage": True,
                "progress": 100,
                "message": "任务已完成",
                "metadata": {
                    "task_count": stats['total']
                },
                "statistics": stats
            }

    return {
        "session_id": session_id,
        "status": "not_found",
        "message": "未找到拆分任务"
    }


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
    # Check if tasks exist
    task_manager = session_manager.get_task_manager(session_id)

    if task_manager:
        # Tasks exist, return statistics
        stats = task_manager.get_statistics()
        return convert_numpy_types({
            "session_id": session_id,
            "status": "ready",
            "statistics": stats,
            "has_tasks": task_manager.df is not None and len(task_manager.df) > 0
        })

    # No task_manager - check if splitting is in progress or attempted
    if session_id in splitting_progress:
        split_info = splitting_progress[session_id]
        split_status = split_info.get('status', 'unknown')

        # Handle different split states
        if split_status in ['processing', 'not_started']:
            return {
                "session_id": session_id,
                "status": "splitting_in_progress",
                "message": "任务正在拆分中，请使用 /api/tasks/split/status/{session_id} 查询拆分进度",
                "split_progress": split_info.get('progress', 0),
                "split_status": split_status,
                "split_message": split_info.get('message', '')
            }
        elif split_status == 'saving':
            return {
                "session_id": session_id,
                "status": "saving_in_progress",
                "message": "任务正在保存中，请稍候...",
                "split_progress": split_info.get('progress', 0),
                "split_status": split_status,
                "split_message": split_info.get('message', '正在保存任务数据...')
            }
        elif split_status == 'failed':
            return {
                "session_id": session_id,
                "status": "split_failed",
                "message": f"任务拆分失败: {split_info.get('error', split_info.get('message', '未知错误'))}",
                "has_tasks": False
            }
        elif split_status == 'completed':
            # Split completed but task_manager not found - unusual case
            return {
                "session_id": session_id,
                "status": "split_completed_loading",
                "message": "任务拆分已完成，正在加载任务管理器...",
                "split_progress": 100,
                "ready_for_next_stage": split_info.get('ready_for_next_stage', False)
            }

    # No splitting progress found - session may not have started splitting
    raise HTTPException(status_code=404, detail="No tasks found for this session. Please split tasks first.")


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