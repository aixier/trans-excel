"""
Data Converters - Task 3.4
Convert between Pydantic models and dictionaries
"""
import json
from typing import Dict, Any, List
from datetime import datetime
from .api_models import SessionData, TaskData


def session_to_dict(session: SessionData) -> Dict[str, Any]:
    """
    Convert SessionData to dictionary

    Args:
        session: SessionData instance

    Returns:
        Dictionary representation
    """
    return session.model_dump(exclude_none=True)


def dict_to_session(data: Dict[str, Any]) -> SessionData:
    """
    Convert dictionary to SessionData

    Args:
        data: Dictionary data

    Returns:
        SessionData instance
    """
    return SessionData(**data)


def task_to_dict(task: TaskData) -> Dict[str, Any]:
    """
    Convert TaskData to dictionary

    Args:
        task: TaskData instance

    Returns:
        Dictionary representation
    """
    return task.model_dump(exclude_none=True)


def dict_to_task(data: Dict[str, Any]) -> TaskData:
    """
    Convert dictionary to TaskData

    Args:
        data: Dictionary data

    Returns:
        TaskData instance
    """
    return TaskData(**data)


def serialize_json_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize JSON fields (game_info, metadata) for database storage

    Args:
        data: Dictionary with JSON fields

    Returns:
        Dictionary with serialized JSON fields
    """
    result = data.copy()

    # Serialize game_info
    if 'game_info' in result and isinstance(result['game_info'], dict):
        result['game_info'] = json.dumps(result['game_info'])

    # Serialize metadata
    if 'metadata' in result and isinstance(result['metadata'], dict):
        result['metadata'] = json.dumps(result['metadata'])

    return result


def deserialize_json_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deserialize JSON fields (game_info, metadata) from database

    Args:
        data: Dictionary with JSON string fields

    Returns:
        Dictionary with parsed JSON fields
    """
    result = data.copy()

    # Deserialize game_info
    if 'game_info' in result and isinstance(result['game_info'], str):
        try:
            result['game_info'] = json.loads(result['game_info'])
        except json.JSONDecodeError:
            pass

    # Deserialize metadata
    if 'metadata' in result and isinstance(result['metadata'], str):
        try:
            result['metadata'] = json.loads(result['metadata'])
        except json.JSONDecodeError:
            pass

    return result


def datetime_to_str(dt: datetime) -> str:
    """
    Convert datetime to ISO format string

    Args:
        dt: Datetime object

    Returns:
        ISO format string
    """
    return dt.isoformat() if dt else None


def str_to_datetime(dt_str: str) -> datetime:
    """
    Convert ISO format string to datetime

    Args:
        dt_str: ISO format string

    Returns:
        Datetime object
    """
    return datetime.fromisoformat(dt_str) if dt_str else None


def batch_sessions_to_dicts(sessions: List[SessionData]) -> List[Dict[str, Any]]:
    """
    Convert list of SessionData to list of dictionaries

    Args:
        sessions: List of SessionData instances

    Returns:
        List of dictionaries
    """
    return [session_to_dict(s) for s in sessions]


def batch_tasks_to_dicts(tasks: List[TaskData]) -> List[Dict[str, Any]]:
    """
    Convert list of TaskData to list of dictionaries

    Args:
        tasks: List of TaskData instances

    Returns:
        List of dictionaries
    """
    return [task_to_dict(t) for t in tasks]