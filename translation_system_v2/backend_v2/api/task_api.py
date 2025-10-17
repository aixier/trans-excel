"""Task API endpoints - Refactored for Session-per-Transformation architecture.

This module implements the new Split API that supports:
1. File upload (with integrated analyze logic)
2. Parent session inheritance (for multi-stage pipelines)
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import tempfile
import os
import pandas as pd
import asyncio
import logging
import json

from models.excel_dataframe import ExcelDataFrame
from models.game_info import GameInfo
from services.task_splitter import TaskSplitter
from services.excel_analyzer import ExcelAnalyzer
from services.excel_loader import ExcelLoader
from services.factories.rule_factory import rule_factory
from utils.pipeline_session_manager import pipeline_session_manager
from models.pipeline_session import TransformationStage
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


class SplitResponse(BaseModel):
    """Split API response."""
    session_id: str
    parent_session_id: Optional[str] = None
    status: str
    message: str
    input_source: str  # 'file' or 'parent_session'


@router.post("/split")
async def split_tasks(
    background_tasks: BackgroundTasks,
    # Mode A: File upload
    file: Optional[UploadFile] = File(None),
    # Mode B: Parent session inheritance
    parent_session_id: Optional[str] = Form(None),
    # Common parameters
    source_lang: Optional[str] = Form(None),
    target_langs: Optional[str] = Form(None),  # JSON string: '["EN", "JP"]'
    rule_set: str = Form("translation"),
    extract_context: bool = Form(True),
    max_chars_per_batch: Optional[int] = Form(None)
):
    """
    Split Excel into translation tasks (new architecture).

    Supports two input modes:
    1. File upload: Provide 'file' parameter
    2. Parent session inheritance: Provide 'parent_session_id'

    Args:
        file: Excel file to upload (Mode A)
        parent_session_id: Parent session to inherit from (Mode B)
        source_lang: Source language (CH/EN)
        target_langs: JSON array of target languages ["PT", "TH", "VN"]
        rule_set: Rule set to use (translation/caps_only)
        extract_context: Whether to extract context
        max_chars_per_batch: Custom batch size

    Returns:
        Session info and status
    """
    # Validate input mode
    if not file and not parent_session_id:
        raise HTTPException(
            status_code=400,
            detail="Must provide either 'file' (for upload) or 'parent_session_id' (for inheritance)"
        )

    if file and parent_session_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot provide both 'file' and 'parent_session_id'. Choose one input mode."
        )

    # Parse target_langs if provided as JSON string
    target_langs_list = None
    if target_langs:
        try:
            target_langs_list = json.loads(target_langs)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid target_langs JSON: {e}")

    # === MODE A: File Upload ===
    if file:
        logger.info(f"Split Mode A: File upload - {file.filename}")

        # Create new session
        session = pipeline_session_manager.create_session(parent_session_id=None)
        session_id = session.session_id

        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")

        try:
            # Save uploaded file to temp
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_path = tmp_file.name

            # Load Excel (includes analyze logic)
            excel_df = ExcelLoader.load_excel(tmp_path)

            # Analyze Excel structure
            analyzer = ExcelAnalyzer()
            analysis_result = analyzer.analyze(excel_df)

            # Store metadata in session
            session.metadata['source_file'] = file.filename
            session.metadata['analysis'] = analysis_result

            # Auto-detect languages if not provided
            if not source_lang and analysis_result.get('language_detection'):
                lang_detection = analysis_result['language_detection']
                source_lang = lang_detection.get('suggested_config', {}).get('source_lang')

            if not target_langs_list and analysis_result.get('language_detection'):
                lang_detection = analysis_result['language_detection']
                target_langs_list = lang_detection.get('suggested_config', {}).get('target_langs', [])

            # Set input state
            pipeline_session_manager.set_input_from_file(session_id, excel_df)

            # Store file path for lazy loading
            pipeline_session_manager.set_metadata(session_id, 'input_file_path', tmp_path)

            logger.info(f"File uploaded and analyzed: {file.filename}, session={session_id}")

        except Exception as e:
            logger.error(f"Failed to process uploaded file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

    # === MODE B: Parent Session Inheritance ===
    else:
        logger.info(f"Split Mode B: Inherit from parent session {parent_session_id}")

        # Validate parent session exists
        parent = pipeline_session_manager.get_session(parent_session_id)
        if not parent:
            raise HTTPException(status_code=404, detail=f"Parent session {parent_session_id} not found")

        # Validate parent has output or is completed
        # Note: output_state might be None due to pickle deserialization failure after restart
        # In that case, check if session is completed and has input_state
        if not parent.output_state and parent.stage != TransformationStage.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Parent session {parent_session_id} has no output. Must complete execution first."
            )

        # If output_state is None but session is completed, use input_state as fallback
        if not parent.output_state and parent.stage == TransformationStage.COMPLETED:
            if not parent.input_state:
                # Try to reload from file
                input_file_path = parent.metadata.get('input_file_path')
                if input_file_path and os.path.exists(input_file_path):
                    logger.warning(f"output_state unavailable for completed session, reloading from file")
                    excel_df = ExcelLoader.load_excel(input_file_path)
                    pipeline_session_manager.set_output_state(parent_session_id, excel_df)
                    parent = pipeline_session_manager.get_session(parent_session_id)
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Parent session {parent_session_id} has no accessible output state"
                    )

        # Create child session
        session = pipeline_session_manager.create_session(parent_session_id=parent_session_id)
        session_id = session.session_id

        # Inherit input from parent's output
        success = pipeline_session_manager.set_input_from_parent(session_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to inherit from parent session")

        logger.info(f"Created child session {session_id} from parent {parent_session_id}")

    # Validate that we have required parameters for splitting
    if not target_langs_list:
        raise HTTPException(status_code=400, detail="target_langs is required")

    # Store rules configuration
    session.rules = rule_factory.config['rule_sets'].get(rule_set, [])
    session.metadata['rule_set'] = rule_set

    # Start background splitting
    background_tasks.add_task(
        _perform_split_async,
        session_id,
        source_lang,
        target_langs_list,
        extract_context,
        max_chars_per_batch
    )

    return SplitResponse(
        session_id=session_id,
        parent_session_id=session.parent_session_id,
        status="processing",
        message="Task splitting started",
        input_source=session.input_source
    )


async def _perform_split_async(
    session_id: str,
    source_lang: Optional[str],
    target_langs: List[str],
    extract_context: bool,
    max_chars_per_batch: Optional[int]
):
    """Background task to perform the actual splitting."""
    try:
        logger.info(f"========== Starting Split for session {session_id} ==========")

        # Get session and input
        session = pipeline_session_manager.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return

        excel_df = pipeline_session_manager.get_input_state(session_id)
        if not excel_df:
            logger.error(f"Session {session_id} has no input state")
            return

        # Get game info from metadata if available
        game_info = None
        if session.metadata.get('game_name'):
            game_info = GameInfo(
                game_name=session.metadata.get('game_name'),
                game_genre=session.metadata.get('game_genre'),
                target_audience=session.metadata.get('target_audience')
            )

        # Initialize progress tracking
        splitting_progress[session_id] = {
            'status': 'processing',
            'progress': 10,
            'message': 'Splitting tasks...'
        }

        # Get enabled rules from session
        enabled_rules = session.rules if session.rules else ['empty', 'yellow', 'blue']

        # Create task splitter with enabled rules
        splitter = TaskSplitter(
            excel_df,
            game_info,
            extract_context=extract_context,
            max_chars_per_batch=max_chars_per_batch,
            enabled_rules=enabled_rules
        )

        # Split tasks
        task_manager = splitter.split_tasks(source_lang, target_langs)

        # Get statistics
        stats = task_manager.get_statistics()

        # Store tasks in session
        pipeline_session_manager.set_tasks(session_id, task_manager, stats)

        # Save to file for persistence
        from pathlib import Path
        data_dir = Path(__file__).parent.parent / 'data' / 'sessions'
        data_dir.mkdir(parents=True, exist_ok=True)
        task_file_path = str(data_dir / f'{session_id}_tasks.parquet')
        task_manager.df.to_parquet(task_file_path, index=False)
        pipeline_session_manager.set_metadata(session_id, 'task_file_path', task_file_path)

        # Update session stage to SPLIT_COMPLETE
        session.update_stage(TransformationStage.SPLIT_COMPLETE)
        pipeline_session_manager._sync_to_cache(session)

        # Update progress
        splitting_progress[session_id] = {
            'status': 'completed',
            'progress': 100,
            'message': 'Task splitting completed',
            'task_count': stats['total'],
            'statistics': stats
        }

        logger.info(f"========== Split completed: {stats['total']} tasks ==========")

    except Exception as e:
        logger.error(f"Split failed for session {session_id}: {e}", exc_info=True)
        splitting_progress[session_id] = {
            'status': 'failed',
            'progress': 0,
            'message': f'Split failed: {str(e)}'
        }


@router.get("/split/status/{session_id}")
async def get_split_status(session_id: str):
    """Get task splitting progress."""
    session = pipeline_session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check splitting progress
    if session_id in splitting_progress:
        progress = splitting_progress[session_id]
        return convert_numpy_types(progress)

    # Check if already completed
    if session.stage == TransformationStage.SPLIT_COMPLETE:
        stats = session.task_statistics
        return {
            "status": "completed",
            "progress": 100,
            "message": "Task splitting completed",
            "task_count": stats.get('total', 0),
            "statistics": stats
        }

    return {
        "status": "not_started",
        "progress": 0,
        "message": "Task splitting not started"
    }


@router.get("/export/{session_id}")
async def export_tasks(session_id: str, export_type: str = "dataframe"):
    """
    Export session data as Excel file.

    Args:
        session_id: Session identifier
        export_type: Type of export
            - "dataframe" (default): Export translated DataFrame (output_state or input_state)
            - "tasks": Export task breakdown DataFrame

    Returns:
        Excel file response
    """
    session = pipeline_session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_path = tmp_file.name

        if export_type == "tasks":
            # Export task breakdown
            task_manager = pipeline_session_manager.get_tasks(session_id)
            if not task_manager or task_manager.df is None:
                raise HTTPException(status_code=404, detail="No tasks found for this session")

            task_manager.export_to_excel(tmp_path)
            filename = f"tasks_{session_id[:8]}.xlsx"

        else:  # export_type == "dataframe"
            # Export complete DataFrame (including color_*, comment_* metadata columns)
            # Get output_state or input_state
            excel_df = session.output_state if session.output_state else session.input_state

            if not excel_df:
                raise HTTPException(
                    status_code=404,
                    detail="No DataFrame available for this session"
                )

            # Export complete DataFrame structure to Excel using pandas
            with pd.ExcelWriter(tmp_path, engine='openpyxl') as writer:
                for sheet_name in excel_df.get_sheet_names():
                    df = excel_df.get_sheet(sheet_name)
                    # Export ALL columns (including color_*, comment_*)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            filename = f"dataframe_{session_id[:8]}.xlsx"

        # Return file
        return FileResponse(
            path=tmp_path,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=filename,
            background=None  # Don't delete file immediately
        )

    except HTTPException:
        raise
    except Exception as e:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error exporting: {str(e)}")


@router.get("/status/{session_id}")
async def get_task_status(session_id: str):
    """Get task statistics for a session."""
    task_manager = pipeline_session_manager.get_tasks(session_id)

    if task_manager and task_manager.df is not None:
        stats = task_manager.get_statistics()
        return convert_numpy_types({
            "session_id": session_id,
            "status": "ready",
            "statistics": stats,
            "has_tasks": len(task_manager.df) > 0
        })

    raise HTTPException(status_code=404, detail="No tasks found for this session")
