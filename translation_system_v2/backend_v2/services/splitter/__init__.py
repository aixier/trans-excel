"""Splitter module for task splitting and rule-based cell matching.

This module provides:
- TaskSplitter: Main splitter class for generating tasks from data state
- SplitRule: Base class for split rules
- Predefined rules: EmptyCellRule, YellowCellRule, BlueCellRule, CapsSheetRule
"""

from .split_rule import (
    SplitRule,
    SplitterError,
    InvalidDataStateError,
    RuleConflictError,
    RuleError
)
from .task_splitter import TaskSplitter

# Import rules
from .rules.empty_cell import EmptyCellRule
from .rules.yellow_cell import YellowCellRule
from .rules.blue_cell import BlueCellRule
from .rules.caps_sheet import CapsSheetRule

__all__ = [
    'TaskSplitter',
    'SplitRule',
    'SplitterError',
    'InvalidDataStateError',
    'RuleConflictError',
    'RuleError',
    'EmptyCellRule',
    'YellowCellRule',
    'BlueCellRule',
    'CapsSheetRule',
]
