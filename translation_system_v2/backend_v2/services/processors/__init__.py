"""Data processor module for translation system.

Processors are responsible for transforming task data without modifying
task status or data state. They follow the principle:
    Input data -> [Processor] -> Output data

Each processor implements a specific operation (translate, uppercase, trim, etc.)
and returns only the processed result.
"""

from .processor import Processor
from .uppercase_processor import UppercaseProcessor
from .trim_processor import TrimProcessor
from .normalize_processor import NormalizeProcessor
from .llm_processor import LLMProcessor

__all__ = [
    'Processor',
    'UppercaseProcessor',
    'TrimProcessor',
    'NormalizeProcessor',
    'LLMProcessor',
]
