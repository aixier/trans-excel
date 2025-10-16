"""Data state management module.

This module provides the core abstraction for representing Excel data at any
point in the transformation pipeline.

Public API:
    - Cell: Immutable cell representation with value, color, and comment
    - DataState: Abstract base class for state management
    - ExcelState: Concrete implementation using ExcelDataFrame

Examples:
    >>> from services.data_state import Cell, DataState, ExcelState
    >>> from models.excel_dataframe import ExcelDataFrame

    >>> # Create state from ExcelDataFrame
    >>> excel_df = ExcelDataFrame()
    >>> state = ExcelState.from_excel_dataframe(excel_df)

    >>> # Access cells
    >>> cell = state.get_cell("Sheet1", 0, 0)
    >>> print(f"Value: {cell.value}, Color: {cell.color}")

    >>> # Iterate cells
    >>> for cell in state.iter_cells(sheet="Sheet1"):
    ...     if cell.has_color:
    ...         print(cell)

    >>> # Copy state (immutability pattern)
    >>> new_state = state.copy()
    >>> new_state.set_cell_value("Sheet1", 0, 0, "Modified")
    >>> # original state unchanged
"""

from .cell import Cell
from .data_state import DataState
from .excel_state import ExcelState

__all__ = [
    'Cell',
    'DataState',
    'ExcelState',
]

__version__ = '1.0.0'
