"""Analyze API endpoints."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import json
import tempfile
import os
import logging

from models.game_info import GameInfo
from models.session_state import SessionStage
from services.excel_loader import ExcelLoader
from services.excel_analyzer import ExcelAnalyzer
from utils.session_manager import session_manager
from utils.json_converter import convert_numpy_types

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analyze", tags=["analyze"])


@router.post("/upload")
async def upload_and_analyze(
    file: UploadFile = File(...),
    game_info: Optional[str] = Form(None)
):
    """
    Upload Excel file and analyze it.

    Args:
        file: Excel file to upload
        game_info: JSON string with game information

    Returns:
        Analysis results with session_id
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")

    # Parse game info if provided
    game_info_obj = None
    if game_info:
        try:
            game_data = json.loads(game_info)
            game_info_obj = GameInfo.from_dict(game_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid game_info JSON")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        # Load Excel file
        loader = ExcelLoader()
        excel_df = loader.load_excel(tmp_path)

        # Create session
        session_id = session_manager.create_session()
        logger.info(f"Created session: {session_id}")

        # Set excel_df
        result = session_manager.set_excel_df(session_id, excel_df)
        logger.info(f"Set excel_df for session {session_id}: {result}")

        # ✅ Save excel_df to file for cross-worker access
        try:
            from pathlib import Path

            # Create data/sessions directory
            data_dir = Path(__file__).parent.parent / 'data' / 'sessions'
            data_dir.mkdir(parents=True, exist_ok=True)

            # Save excel_df to pickle file (preserves all DataFrame features)
            excel_file_path = str(data_dir / f'{session_id}_excel.pkl')
            excel_df.save_to_pickle(excel_file_path)

            # Store file path in metadata
            session_manager.set_metadata(session_id, 'excel_file_path', excel_file_path)

            logger.info(f"Excel data saved to file: {excel_file_path}")
        except Exception as e:
            logger.error(f"Failed to save excel_df to file: {e}")
            # Don't fail the operation

        if game_info_obj:
            session_manager.set_game_info(session_id, game_info_obj)

        # Analyze Excel
        analyzer = ExcelAnalyzer()
        analysis = analyzer.analyze(excel_df, game_info_obj)

        # Store analysis in session
        session_manager.set_analysis(session_id, analysis)

        # ✨ Update session status to ANALYZED (ready for split)
        session = session_manager.get_session(session_id)
        if session:
            session.session_status.update_stage(SessionStage.ANALYZED)
            logger.info(f"Session {session_id} status updated to ANALYZED")

        # Prepare response
        response = {
            "session_id": session_id,
            "stage": session.session_status.stage.value if session else "unknown",
            "analysis": convert_numpy_types(analysis)
        }

        return response

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        # Clean up session if it was created
        if 'session_id' in locals():
            logger.warning(f"Cleaning up failed session: {session_id}")
            # Note: We should add a method to delete session, but for now just log it
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/status/{session_id}")
async def get_analysis_status(session_id: str):
    """Get analysis results for a session."""
    analysis = session_manager.get_analysis(session_id)

    if not analysis:
        raise HTTPException(status_code=404, detail="Session not found")

    excel_df = session_manager.get_excel_df(session_id)
    game_info = session_manager.get_game_info(session_id)

    return {
        "session_id": session_id,
        "analysis": convert_numpy_types(analysis),
        "has_excel": excel_df is not None,
        "has_game_info": game_info is not None
    }