"""Download API for translated Excel files."""

import os
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse

from services.export.excel_exporter import excel_exporter
from utils.session_manager import session_manager


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["download"])


@router.get("/download/{session_id}")
async def download_translated_excel(session_id: str):
    """
    Download translated Excel file.

    Args:
        session_id: Session identifier

    Returns:
        FileResponse: Translated Excel file
    """
    try:
        # Validate session exists
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        # Check if file already exported
        export_info = excel_exporter.get_export_info(session_id)

        if export_info['has_export'] and export_info['file_exists']:
            # Return existing file
            file_path = export_info['exported_file']
            filename = Path(file_path).name

            logger.info(f"Returning existing export file: {filename}")

            return FileResponse(
                path=file_path,
                filename=filename,
                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        # Generate new export
        try:
            exported_file = await excel_exporter.export_final_excel(session_id)
            filename = Path(exported_file).name

            logger.info(f"Generated new export file: {filename}")

            return FileResponse(
                path=exported_file,
                filename=filename,
                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot export file: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to export file for session {session_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate export file"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in download endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/download/{session_id}/summary")
async def download_task_summary(session_id: str):
    """
    Download task summary Excel file.

    Args:
        session_id: Session identifier

    Returns:
        FileResponse: Task summary Excel file
    """
    try:
        # Validate session exists
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        # Generate task summary
        try:
            summary_file = await excel_exporter.export_task_summary(session_id)
            filename = Path(summary_file).name

            logger.info(f"Generated task summary file: {filename}")

            return FileResponse(
                path=summary_file,
                filename=filename,
                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot generate summary: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Failed to generate summary for session {session_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate summary file"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in summary endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/download/{session_id}/info")
async def get_download_info(session_id: str):
    """
    Get download information for a session.

    Args:
        session_id: Session identifier

    Returns:
        JSON response with download information including execution status
    """
    try:
        # Validate session exists
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        # Get task manager and statistics
        task_manager = session_manager.get_task_manager(session_id)

        if not task_manager:
            # No task manager - need to split tasks first
            return JSONResponse(content={
                "session_id": session_id,
                "status": "no_tasks",
                "message": "任务尚未拆分，无法下载",
                "ready_for_download": False,
                "can_download": False,
                "execution_status": None,
                "task_statistics": {},
                "export_info": {
                    "has_export": False,
                    "file_exists": False
                }
            })

        task_stats = task_manager.get_statistics()

        # Check execution progress
        execution_progress = session.execution_progress
        execution_status = None
        ready_for_download = False
        status = "unknown"
        message = ""

        if execution_progress:
            execution_status = {
                "status": execution_progress.status.value,
                "ready_for_download": execution_progress.ready_for_download,
                "error": execution_progress.error
            }
            ready_for_download = execution_progress.ready_for_download

            if execution_progress.status.value == "completed":
                status = "completed"
                message = "翻译已完成，可以下载结果"
            elif execution_progress.status.value == "running":
                status = "executing"
                completed = task_stats.get('completed', 0)
                total = task_stats.get('total', 0)
                message = f"翻译进行中 ({completed}/{total})，请等待完成后下载"
            elif execution_progress.status.value == "initializing":
                status = "initializing"
                message = "执行初始化中，请稍候..."
            elif execution_progress.status.value == "failed":
                status = "failed"
                message = f"翻译失败: {execution_progress.error or '未知错误'}"
            else:
                status = execution_progress.status.value
                message = "执行状态未知"
        else:
            # No execution started yet
            total = task_stats.get('total', 0)
            if total > 0:
                status = "not_started"
                message = "任务已拆分但尚未执行，请先开始翻译"
            else:
                status = "no_tasks"
                message = "无可用任务"

        # Get export information
        export_info = excel_exporter.get_export_info(session_id)

        # Determine if can download
        # Can download if:
        # 1. Execution is completed (ready_for_download=True), OR
        # 2. Already has exported file
        can_download = ready_for_download or export_info['has_export']

        # Combine information
        download_info = {
            "session_id": session_id,
            "status": status,
            "message": message,
            "ready_for_download": ready_for_download,
            "can_download": can_download,
            "execution_status": execution_status,
            "task_statistics": task_stats,
            "export_info": export_info
        }

        return JSONResponse(content=download_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get download info for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve download information"
        )


@router.delete("/download/{session_id}/files")
async def cleanup_session_files(session_id: str):
    """
    Clean up exported files for a session.

    Args:
        session_id: Session identifier

    Returns:
        JSON response with cleanup results
    """
    try:
        # Validate session exists
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        cleanup_count = 0
        cleanup_errors = []

        # Get export info
        export_info = excel_exporter.get_export_info(session_id)

        if export_info['has_export'] and export_info['file_exists']:
            try:
                os.remove(export_info['exported_file'])
                cleanup_count += 1

                # Clear metadata
                session_manager.set_metadata(session_id, 'exported_file', None)
                session_manager.set_metadata(session_id, 'export_timestamp', None)

                logger.info(f"Cleaned up export file for session {session_id}")

            except Exception as e:
                error_msg = f"Failed to remove export file: {str(e)}"
                cleanup_errors.append(error_msg)
                logger.error(error_msg)

        # Clean up any other files in output directory matching session
        try:
            output_dir = excel_exporter.output_dir
            for file_path in output_dir.glob(f"*{session_id[:8]}*.xlsx"):
                try:
                    file_path.unlink()
                    cleanup_count += 1
                except Exception as e:
                    error_msg = f"Failed to remove file {file_path}: {str(e)}"
                    cleanup_errors.append(error_msg)

        except Exception as e:
            error_msg = f"Failed to scan output directory: {str(e)}"
            cleanup_errors.append(error_msg)

        return JSONResponse(content={
            "session_id": session_id,
            "files_removed": cleanup_count,
            "errors": cleanup_errors,
            "success": len(cleanup_errors) == 0
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup files for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to cleanup session files"
        )