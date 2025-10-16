"""Debug API for session data inspection and manipulation."""

import logging
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import pandas as pd

from utils.pipeline_session_manager import pipeline_session_manager
from models.excel_dataframe import ExcelDataFrame
from models.task_dataframe import TaskDataFrameManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/session/{session_id}/info")
async def get_session_debug_info(session_id: str):
    """
    获取 Session 的完整调试信息

    返回所有阶段的数据状态，方便调试
    """
    try:
        session = pipeline_session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # 收集完整的状态信息
        info = {
            "session_id": session_id,
            "stage": session.stage.value,
            "created_at": session.created_at.isoformat(),
            "last_accessed": session.last_accessed.isoformat(),

            # Input 信息
            "input": {
                "source": session.input_source,
                "parent_session_id": session.parent_session_id,
                "has_data": session.input_state is not None,
                "row_count": session.input_state.total_rows if session.input_state else 0,
                "column_count": session.input_state.total_cols if session.input_state else 0,
                "sheet_count": len(session.input_state.sheets) if session.input_state else 0,
            },

            # 配置信息
            "config": {
                "rules": session.rules,
                "processor": session.processor,
            },

            # Tasks 信息
            "tasks": {
                "has_tasks": session.tasks is not None and session.tasks.df is not None,
                "task_count": len(session.tasks.df) if (session.tasks and session.tasks.df is not None) else 0,
                "statistics": session.task_statistics,
            },

            # Output 信息
            "output": {
                "has_data": session.output_state is not None,
                "row_count": session.output_state.total_rows if session.output_state else 0,
                "column_count": session.output_state.total_cols if session.output_state else 0,
                "sheet_count": len(session.output_state.sheets) if session.output_state else 0,
                "execution_statistics": session.execution_statistics,
            },

            # 链式关系
            "chain": {
                "parent_session_id": session.parent_session_id,
                "child_session_ids": session.child_session_ids,
            },

            # 元数据
            "metadata": session.metadata,
        }

        return JSONResponse(content=info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get debug info for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/download/input")
async def download_input_dataframe(session_id: str):
    """
    下载 Input State (ExcelDataFrame)

    返回原始输入的 Excel 文件
    """
    try:
        session = pipeline_session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        if not session.input_state:
            raise HTTPException(status_code=400, detail="No input data available")

        # 导出为临时 Excel 文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_path = temp_file.name
        temp_file.close()

        # ExcelDataFrame has multiple sheets
        with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:
            for sheet_name, df in session.input_state.sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        filename = f"{session_id[:8]}_input_state.xlsx"

        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download input for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/download/tasks")
async def download_task_dataframe(session_id: str):
    """
    下载 Task DataFrame

    Split 完成后可以下载任务列表，方便查看和调试
    """
    try:
        session = pipeline_session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        task_manager = pipeline_session_manager.get_tasks(session_id)
        if task_manager is None or task_manager.df is None or task_manager.df.empty:
            raise HTTPException(status_code=400, detail="No tasks available. Please split first.")

        # 导出为临时 Excel 文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_path = temp_file.name
        temp_file.close()

        task_manager.df.to_excel(temp_path, index=False)

        filename = f"{session_id[:8]}_tasks.xlsx"

        logger.info(f"Exporting {len(task_manager.df)} tasks for session {session_id}")

        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download tasks for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/download/output")
async def download_output_dataframe(session_id: str):
    """
    下载 Output State (ExcelDataFrame)

    执行完成后下载结果数据
    """
    try:
        session = pipeline_session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        if not session.output_state:
            raise HTTPException(status_code=400, detail="No output data available. Please complete execution first.")

        # 导出为临时 Excel 文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_path = temp_file.name
        temp_file.close()

        # ExcelDataFrame has multiple sheets
        with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:
            for sheet_name, df in session.output_state.sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        filename = f"{session_id[:8]}_output_state.xlsx"

        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download output for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/upload/tasks")
async def upload_task_dataframe(
    session_id: str,
    file: UploadFile = File(...)
):
    """
    上传修改后的 Task DataFrame

    允许手动修改任务列表后重新上传
    """
    try:
        session = pipeline_session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # 读取上传的 Excel 文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_path = temp_file.name

        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        # 读取为 DataFrame
        df = pd.read_excel(temp_path)

        # 验证必需的列
        required_columns = ['task_id', 'source_text', 'target_lang', 'status']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )

        # 创建 TaskDataFrameManager 并设置
        task_manager = TaskDataFrameManager()
        task_manager.import_from_dataframe(df)

        # 更新统计信息
        session.task_statistics = {
            'total': len(df),
            'by_status': df['status'].value_counts().to_dict(),
            'by_language': df['target_lang'].value_counts().to_dict() if 'target_lang' in df.columns else {},
        }

        # 保存任务到session
        pipeline_session_manager.set_tasks(session_id, task_manager, session.task_statistics)

        logger.info(f"Uploaded {len(df)} tasks for session {session_id}")

        # 清理临时文件
        Path(temp_path).unlink()

        return JSONResponse(content={
            "status": "success",
            "message": f"Uploaded {len(df)} tasks",
            "task_count": len(df),
            "statistics": session.task_statistics
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload tasks for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/upload/output")
async def upload_output_dataframe(
    session_id: str,
    file: UploadFile = File(...)
):
    """
    上传 Output State (ExcelDataFrame)

    允许手动设置执行结果（用于测试或恢复）
    """
    try:
        session = pipeline_session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # 读取上传的 Excel 文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_path = temp_file.name

        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        # 读取为 ExcelDataFrame
        output_state = ExcelDataFrame()

        # Read all sheets from the Excel file
        xls = pd.ExcelFile(temp_path)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            output_state.add_sheet(sheet_name, df)

        output_state.filename = file.filename or 'uploaded_output.xlsx'

        # 设置 output_state
        session.output_state = output_state
        pipeline_session_manager.set_output_state(session_id, output_state)

        # 更新阶段为 COMPLETED
        from models.pipeline_session import TransformationStage
        session.update_stage(TransformationStage.COMPLETED)

        logger.info(f"Uploaded output state for session {session_id}: {output_state.total_rows} rows, {len(output_state.sheets)} sheets")

        # 清理临时文件
        Path(temp_path).unlink()

        return JSONResponse(content={
            "status": "success",
            "message": f"Uploaded output state with {output_state.total_rows} rows, {len(output_state.sheets)} sheets",
            "row_count": output_state.total_rows,
            "column_count": output_state.total_cols,
            "sheet_count": len(output_state.sheets),
            "stage": session.stage.value
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload output for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/preview/input")
async def preview_input_data(session_id: str, limit: int = 10):
    """
    预览 Input State 数据（前N行）
    """
    try:
        session = pipeline_session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        if not session.input_state:
            raise HTTPException(status_code=400, detail="No input data available")

        # Get first sheet for preview
        if not session.input_state.sheets:
            raise HTTPException(status_code=400, detail="No sheets in input data")

        first_sheet_name = list(session.input_state.sheets.keys())[0]
        df = session.input_state.sheets[first_sheet_name]
        preview_df = df.head(limit)

        return JSONResponse(content={
            "session_id": session_id,
            "sheet_name": first_sheet_name,
            "sheet_count": len(session.input_state.sheets),
            "total_rows": len(df),
            "total_rows_all_sheets": session.input_state.total_rows,
            "preview_rows": len(preview_df),
            "columns": list(preview_df.columns),
            "data": preview_df.to_dict(orient='records')
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview input for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/preview/tasks")
async def preview_task_data(session_id: str, limit: int = 10):
    """
    预览 Task DataFrame 数据（前N行）
    """
    try:
        session = pipeline_session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        task_manager = pipeline_session_manager.get_tasks(session_id)
        if task_manager is None or task_manager.df is None or task_manager.df.empty:
            raise HTTPException(status_code=400, detail="No tasks available")

        preview_df = task_manager.df.head(limit)

        return JSONResponse(content={
            "session_id": session_id,
            "total_tasks": len(task_manager.df),
            "preview_rows": len(preview_df),
            "columns": list(task_manager.df.columns),
            "data": preview_df.to_dict(orient='records')
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview tasks for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/preview/output")
async def preview_output_data(session_id: str, limit: int = 10):
    """
    预览 Output State 数据（前N行）
    """
    try:
        session = pipeline_session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        if not session.output_state:
            raise HTTPException(status_code=400, detail="No output data available")

        # Get first sheet for preview
        if not session.output_state.sheets:
            raise HTTPException(status_code=400, detail="No sheets in output data")

        first_sheet_name = list(session.output_state.sheets.keys())[0]
        df = session.output_state.sheets[first_sheet_name]
        preview_df = df.head(limit)

        return JSONResponse(content={
            "session_id": session_id,
            "sheet_name": first_sheet_name,
            "sheet_count": len(session.output_state.sheets),
            "total_rows": len(df),
            "total_rows_all_sheets": session.output_state.total_rows,
            "preview_rows": len(preview_df),
            "columns": list(preview_df.columns),
            "data": preview_df.to_dict(orient='records')
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview output for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
