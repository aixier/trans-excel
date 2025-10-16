"""Excel-based implementation of DataState.

This module provides a concrete implementation of DataState that wraps
the existing ExcelDataFrame class, providing backward compatibility while
adding the new DataState interface.
"""

from typing import Any, Optional, List, Dict, Iterator, Tuple

from models.excel_dataframe import ExcelDataFrame
from .data_state import DataState
from .cell import Cell


class ExcelState(DataState):
    """
    Excel-based implementation of DataState.

    This class wraps ExcelDataFrame and provides the DataState interface
    while maintaining full backward compatibility with existing code.

    Design:
        - Delegates storage to ExcelDataFrame
        - Adds immutability through copy()
        - Adds Cell abstraction
        - Maintains all existing functionality

    Examples:
        >>> # Create from existing ExcelDataFrame
        >>> excel_df = ExcelDataFrame()
        >>> state = ExcelState(excel_df)

        >>> # Or use factory method
        >>> state = ExcelState.from_excel_dataframe(excel_df)

        >>> # Access through new API
        >>> cell = state.get_cell("Sheet1", 0, 0)
        >>> value = state.get_cell_value("Sheet1", 0, 0)

        >>> # Access underlying ExcelDataFrame if needed
        >>> excel_df = state.excel_dataframe

        >>> # Immutability pattern
        >>> new_state = state.copy()
        >>> new_state.set_cell_value("Sheet1", 0, 0, "Modified")
        >>> # original state is unchanged

    Attributes:
        _data: Underlying ExcelDataFrame instance
    """

    def __init__(self, excel_df: Optional[ExcelDataFrame] = None):
        """
        Initialize ExcelState from ExcelDataFrame.

        Args:
            excel_df: Existing ExcelDataFrame or None for empty state

        Examples:
            >>> # Create empty state
            >>> state = ExcelState()

            >>> # Create from existing ExcelDataFrame
            >>> excel_df = load_excel("file.xlsx")
            >>> state = ExcelState(excel_df)
        """
        if excel_df is None:
            excel_df = ExcelDataFrame()
        self._data = excel_df

    @classmethod
    def from_excel_dataframe(cls, excel_df: ExcelDataFrame) -> 'ExcelState':
        """
        Factory method to create ExcelState from ExcelDataFrame.

        Args:
            excel_df: Existing ExcelDataFrame instance

        Returns:
            New ExcelState instance wrapping the ExcelDataFrame

        Examples:
            >>> excel_df = load_excel("file.xlsx")
            >>> state = ExcelState.from_excel_dataframe(excel_df)
        """
        return cls(excel_df)

    @property
    def excel_dataframe(self) -> ExcelDataFrame:
        """
        Get underlying ExcelDataFrame.

        This property provides access to the underlying ExcelDataFrame
        for backward compatibility with existing code.

        Returns:
            The wrapped ExcelDataFrame instance

        Examples:
            >>> state = ExcelState(...)
            >>> excel_df = state.excel_dataframe
            >>> # Use with existing code
            >>> exporter.export(excel_df)
        """
        return self._data

    @property
    def sheets(self) -> Dict[str, Any]:
        """
        Get sheets dictionary for backward compatibility.

        Returns:
            Dictionary mapping sheet names to DataFrames

        Examples:
            >>> state = ExcelState(...)
            >>> for sheet_name in state.sheets.keys():
            ...     print(sheet_name)
        """
        return self._data.sheets

    def copy(self) -> 'ExcelState':
        """
        Create a deep copy of this state.

        Uses ExcelDataFrame.clone() for efficient deep copying.

        Returns:
            New ExcelState instance with copied data

        Examples:
            >>> original = ExcelState(...)
            >>> copy = original.copy()
            >>> copy.set_cell_value("Sheet1", 0, 0, "Modified")
            >>> # original is unchanged
            >>> assert original.get_cell_value("Sheet1", 0, 0) != "Modified"
        """
        return ExcelState(self._data.clone())

    def get_cell(self, sheet: str, row: int, col: int) -> Cell:
        """
        Get a Cell object with all metadata.

        Args:
            sheet: Sheet name
            row: Zero-based row index
            col: Zero-based column index

        Returns:
            Cell object with value, color, and comment

        Raises:
            KeyError: If sheet doesn't exist
            IndexError: If row or col is out of bounds

        Examples:
            >>> cell = state.get_cell("Sheet1", 0, 0)
            >>> print(f"Value: {cell.value}, Color: {cell.color}")
        """
        # Validate sheet exists
        if sheet not in self._data.sheets:
            raise KeyError(f"Sheet '{sheet}' not found")

        # Validate indices
        sheet_df = self._data.get_sheet(sheet)
        if sheet_df is None:
            raise KeyError(f"Sheet '{sheet}' not found")

        num_rows, num_cols = len(sheet_df), len(sheet_df.columns)
        if row < 0 or row >= num_rows:
            raise IndexError(f"Row {row} out of bounds (0-{num_rows-1})")
        if col < 0 or col >= num_cols:
            raise IndexError(f"Column {col} out of bounds (0-{num_cols-1})")

        # Get cell data
        value = self._data.get_cell_value(sheet, row, col)
        color = self._data.get_cell_color(sheet, row, col)
        comment = self._data.get_cell_comment(sheet, row, col)

        return Cell(
            sheet=sheet,
            row=row,
            col=col,
            value=value,
            color=color,
            comment=comment
        )

    def get_cell_value(self, sheet: str, row: int, col: int) -> Any:
        """
        Get cell value only (optimized).

        Args:
            sheet: Sheet name
            row: Zero-based row index
            col: Zero-based column index

        Returns:
            Cell value

        Raises:
            KeyError: If sheet doesn't exist
            IndexError: If row or col is out of bounds

        Examples:
            >>> value = state.get_cell_value("Sheet1", 0, 0)
        """
        if sheet not in self._data.sheets:
            raise KeyError(f"Sheet '{sheet}' not found")

        sheet_df = self._data.get_sheet(sheet)
        if sheet_df is None:
            raise KeyError(f"Sheet '{sheet}' not found")

        num_rows, num_cols = len(sheet_df), len(sheet_df.columns)
        if row < 0 or row >= num_rows:
            raise IndexError(f"Row {row} out of bounds (0-{num_rows-1})")
        if col < 0 or col >= num_cols:
            raise IndexError(f"Column {col} out of bounds (0-{num_cols-1})")

        return self._data.get_cell_value(sheet, row, col)

    def set_cell_value(self, sheet: str, row: int, col: int, value: Any) -> None:
        """
        Set cell value.

        Args:
            sheet: Sheet name
            row: Zero-based row index
            col: Zero-based column index
            value: Value to set

        Raises:
            KeyError: If sheet doesn't exist
            IndexError: If row or col is out of bounds

        Examples:
            >>> state.set_cell_value("Sheet1", 0, 0, "New Value")
        """
        if sheet not in self._data.sheets:
            raise KeyError(f"Sheet '{sheet}' not found")

        sheet_df = self._data.get_sheet(sheet)
        if sheet_df is None:
            raise KeyError(f"Sheet '{sheet}' not found")

        num_rows, num_cols = len(sheet_df), len(sheet_df.columns)
        if row < 0 or row >= num_rows:
            raise IndexError(f"Row {row} out of bounds (0-{num_rows-1})")
        if col < 0 or col >= num_cols:
            raise IndexError(f"Column {col} out of bounds (0-{num_cols-1})")

        self._data.set_cell_value(sheet, row, col, value)

    def get_cell_color(self, sheet: str, row: int, col: int) -> Optional[str]:
        """
        Get cell color.

        Args:
            sheet: Sheet name
            row: Zero-based row index
            col: Zero-based column index

        Returns:
            Color hex string or None

        Raises:
            KeyError: If sheet doesn't exist

        Examples:
            >>> color = state.get_cell_color("Sheet1", 0, 0)
        """
        if sheet not in self._data.sheets:
            raise KeyError(f"Sheet '{sheet}' not found")

        return self._data.get_cell_color(sheet, row, col)

    def set_cell_color(self, sheet: str, row: int, col: int, color: str) -> None:
        """
        Set cell color.

        Args:
            sheet: Sheet name
            row: Zero-based row index
            col: Zero-based column index
            color: Color hex string

        Raises:
            KeyError: If sheet doesn't exist

        Examples:
            >>> state.set_cell_color("Sheet1", 0, 0, "FFFF00")
        """
        if sheet not in self._data.sheets:
            raise KeyError(f"Sheet '{sheet}' not found")

        self._data.set_cell_color(sheet, row, col, color)

    def get_cell_comment(self, sheet: str, row: int, col: int) -> Optional[str]:
        """
        Get cell comment.

        Args:
            sheet: Sheet name
            row: Zero-based row index
            col: Zero-based column index

        Returns:
            Comment text or None

        Raises:
            KeyError: If sheet doesn't exist

        Examples:
            >>> comment = state.get_cell_comment("Sheet1", 0, 0)
        """
        if sheet not in self._data.sheets:
            raise KeyError(f"Sheet '{sheet}' not found")

        return self._data.get_cell_comment(sheet, row, col)

    def set_cell_comment(self, sheet: str, row: int, col: int, comment: str) -> None:
        """
        Set cell comment.

        Args:
            sheet: Sheet name
            row: Zero-based row index
            col: Zero-based column index
            comment: Comment text

        Raises:
            KeyError: If sheet doesn't exist

        Examples:
            >>> state.set_cell_comment("Sheet1", 0, 0, "Important note")
        """
        if sheet not in self._data.sheets:
            raise KeyError(f"Sheet '{sheet}' not found")

        self._data.set_cell_comment(sheet, row, col, comment)

    def get_sheet_names(self) -> List[str]:
        """
        Get all sheet names.

        Returns:
            List of sheet names

        Examples:
            >>> for sheet in state.get_sheet_names():
            ...     print(sheet)
        """
        return self._data.get_sheet_names()

    def get_sheet_dimensions(self, sheet: str) -> Tuple[int, int]:
        """
        Get sheet dimensions.

        Args:
            sheet: Sheet name

        Returns:
            Tuple of (num_rows, num_cols)

        Raises:
            KeyError: If sheet doesn't exist

        Examples:
            >>> rows, cols = state.get_sheet_dimensions("Sheet1")
        """
        if sheet not in self._data.sheets:
            raise KeyError(f"Sheet '{sheet}' not found")

        sheet_df = self._data.get_sheet(sheet)
        if sheet_df is None:
            raise KeyError(f"Sheet '{sheet}' not found")

        return len(sheet_df), len(sheet_df.columns)

    def iter_cells(self,
                   sheet: Optional[str] = None,
                   include_empty: bool = False) -> Iterator[Cell]:
        """
        Iterate over cells.

        Args:
            sheet: Specific sheet name or None for all sheets
            include_empty: Include cells with no value

        Yields:
            Cell objects

        Examples:
            >>> # Iterate specific sheet
            >>> for cell in state.iter_cells(sheet="Sheet1"):
            ...     print(cell.value)

            >>> # Iterate all sheets, including empty cells
            >>> for cell in state.iter_cells(include_empty=True):
            ...     process(cell)
        """
        # Determine which sheets to iterate
        if sheet is not None:
            if sheet not in self._data.sheets:
                raise KeyError(f"Sheet '{sheet}' not found")
            sheet_names = [sheet]
        else:
            sheet_names = self.get_sheet_names()

        # Iterate over sheets
        for sheet_name in sheet_names:
            sheet_df = self._data.get_sheet(sheet_name)
            if sheet_df is None:
                continue

            num_rows, num_cols = len(sheet_df), len(sheet_df.columns)

            # Iterate over cells
            for row in range(num_rows):
                for col in range(num_cols):
                    # Get cell data
                    value = self._data.get_cell_value(sheet_name, row, col)
                    color = self._data.get_cell_color(sheet_name, row, col)
                    comment = self._data.get_cell_comment(sheet_name, row, col)

                    # Create cell
                    cell = Cell(
                        sheet=sheet_name,
                        row=row,
                        col=col,
                        value=value,
                        color=color,
                        comment=comment
                    )

                    # Filter empty cells if requested
                    if include_empty or cell.has_value:
                        yield cell

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get state metadata.

        Returns:
            Dictionary with metadata including color_map and comment_map

        Examples:
            >>> metadata = state.get_metadata()
            >>> print(metadata['filename'])
            >>> color_map = metadata['color_map']
        """
        return {
            'filename': self._data.filename,
            'excel_id': self._data.excel_id,
            'total_rows': self._data.total_rows,
            'total_cols': self._data.total_cols,
            'color_map': self._data.color_map,
            'comment_map': self._data.comment_map
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the state.

        Returns:
            Dictionary with statistics

        Examples:
            >>> stats = state.get_statistics()
            >>> print(f"Total cells: {stats['total_cells']}")
        """
        return self._data.get_statistics()
