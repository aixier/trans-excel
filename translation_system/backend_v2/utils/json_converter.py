"""Convert numpy types to Python native types for JSON serialization."""

import numpy as np
from typing import Any, Dict, List, Union


def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert numpy types to Python native types.

    Args:
        obj: Any object that might contain numpy types

    Returns:
        Object with numpy types converted to Python types
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return type(obj)(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif hasattr(obj, 'item'):  # For numpy scalars
        return obj.item()
    else:
        return obj