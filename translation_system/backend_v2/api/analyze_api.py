"""Analyze API endpoints."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import json
import tempfile
import os

from models.game_info import GameInfo
from services.excel_loader import ExcelLoader
from services.excel_analyzer import ExcelAnalyzer
from utils.session_manager import session_manager
from utils.json_converter import convert_numpy_types


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
        session_manager.set_excel_df(session_id, excel_df)

        if game_info_obj:
            session_manager.set_game_info(session_id, game_info_obj)

        # Analyze Excel
        analyzer = ExcelAnalyzer()
        analysis = analyzer.analyze(excel_df, game_info_obj)

        # Store analysis in session
        session_manager.set_analysis(session_id, analysis)

        # Prepare response
        response = {
            "session_id": session_id,
            "analysis": convert_numpy_types(analysis)
        }

        return response

    except Exception as e:
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