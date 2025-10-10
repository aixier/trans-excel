"""Glossary management API endpoints."""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional, List, Dict, Any
import logging
import json

from services.glossary_manager import glossary_manager
from utils.json_converter import convert_numpy_types

router = APIRouter(prefix="/api/glossaries", tags=["glossaries"])
logger = logging.getLogger(__name__)


@router.get("/list")
async def get_glossaries_list():
    """
    Get list of all available glossaries.

    Returns:
        List of glossaries with metadata
    """
    try:
        glossaries = glossary_manager.list_available_glossaries()

        return convert_numpy_types({
            'glossaries': glossaries,
            'count': len(glossaries)
        })

    except Exception as e:
        logger.error(f"Failed to get glossaries list: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get glossaries: {str(e)}")


@router.get("/{glossary_id}")
async def get_glossary(glossary_id: str):
    """
    Get specific glossary by ID.

    Args:
        glossary_id: Glossary identifier

    Returns:
        Glossary data
    """
    try:
        glossary = glossary_manager.load_glossary(glossary_id)

        if not glossary:
            raise HTTPException(status_code=404, detail=f"Glossary '{glossary_id}' not found")

        return convert_numpy_types(glossary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get glossary {glossary_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get glossary: {str(e)}")


@router.post("/upload")
async def upload_glossary(
    file: UploadFile = File(...),
    glossary_id: Optional[str] = None
):
    """
    Upload a new glossary file.

    Args:
        file: JSON file containing glossary data
        glossary_id: Optional custom ID (uses filename if not provided)

    Returns:
        Upload status
    """
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Only JSON files are supported")

        # Read file content
        content = await file.read()
        glossary_data = json.loads(content.decode('utf-8'))

        # Use provided ID or extract from data or filename
        if not glossary_id:
            glossary_id = glossary_data.get('id') or file.filename.replace('.json', '')

        # Validate glossary structure
        if 'terms' not in glossary_data:
            raise HTTPException(status_code=400, detail="Invalid glossary format: missing 'terms' field")

        # Save glossary
        success = glossary_manager.save_glossary(glossary_id, glossary_data)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save glossary")

        return {
            'status': 'success',
            'glossary_id': glossary_id,
            'term_count': len(glossary_data.get('terms', [])),
            'message': 'Glossary uploaded successfully'
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload glossary: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.delete("/{glossary_id}")
async def delete_glossary(glossary_id: str):
    """
    Delete a glossary.

    Args:
        glossary_id: Glossary identifier

    Returns:
        Deletion status
    """
    try:
        # Don't allow deleting default glossary
        if glossary_id == 'default':
            raise HTTPException(status_code=400, detail="Cannot delete default glossary")

        # Delete file
        from pathlib import Path
        glossaries_dir = Path(__file__).parent.parent / 'data' / 'glossaries'
        file_path = glossaries_dir / f"{glossary_id}.json"

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Glossary '{glossary_id}' not found")

        file_path.unlink()

        # Clear cache
        if hasattr(glossary_manager, 'cache') and glossary_id in glossary_manager.cache:
            del glossary_manager.cache[glossary_id]

        return {
            'status': 'success',
            'glossary_id': glossary_id,
            'message': 'Glossary deleted successfully'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete glossary {glossary_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
