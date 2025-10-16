"""Abstract base class for data state management.

This module defines the core abstraction for representing Excel data at any
point in the transformation pipeline. DataState provides immutability through
copy semantics and efficient cell-level access.

Architecture Principle:
    原始数据 = 结果数据 = 数据状态
    数据状态0 → [转换] → 数据状态1 → [转换] → 数据状态2

Key Concepts:
    - DataState is a snapshot of data at a specific point in time
    - Immutability is achieved through the copy() method
    - Each transformation creates a new DataState
    - DataState is NOT a task container (use TaskDataFrame for that)
    - DataState is NOT a transformation engine (use Transformer for that)
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict, Iterator, Tuple

from .cell import Cell


class DataState(ABC):
    """
    Abstract base class for data state management.

    This class provides the fundamental abstraction for representing spreadsheet
    data at any point in the transformation pipeline. Concrete implementations
    (like ExcelState) handle the actual storage and manipulation.

    Design Principles:
        1. Immutability through Copy: DataState itself is mutable for performance,
           but provides copy() for creating snapshots
        2. Cell-level Access: Efficient access to individual cells with metadata
        3. Multi-sheet Support: Handle Excel files with multiple sheets
        4. Metadata Preservation: Maintain colors, comments, and formatting

    Examples:
        >>> # Get a cell with all metadata
        >>> cell = state.get_cell("Sheet1", 0, 0)
        >>> print(cell.value, cell.color, cell.comment)

        >>> # Iterate over non-empty cells
        >>> for cell in state.iter_cells(include_empty=False):
        ...     process(cell)

        >>> # Transformer pattern: copy before modify
        >>> def transform(input_state):
        ...     output_state = input_state.copy()
        ...     output_state.set_cell_value("Sheet1", 0, 0, "Translated")
        ...     return output_state
    """

    @abstractmethod
    def copy(self) -> 'DataState':
        """
        Create a deep copy of this state.

        This is the key method for achieving immutability. Transformers should
        always call copy() before modifying state to preserve the input state.

        Returns:
            New DataState instance with copied data (independent of original)

        Examples:
            >>> original = ExcelState(...)
            >>> modified = original.copy()
            >>> modified.set_cell_value("Sheet1", 0, 0, "New")
            >>> # original is unchanged
            >>> assert original.get_cell_value("Sheet1", 0, 0) != "New"

        Note:
            Implementation should use efficient deep copy mechanisms
            (e.g., pandas DataFrame.copy()) to minimize performance overhead.
        """
        pass

    @abstractmethod
    def get_cell(self, sheet: str, row: int, col: int) -> Cell:
        """
        Get a Cell object with all metadata (value, color, comment).

        Args:
            sheet: Sheet name
            row: Zero-based row index
            col: Zero-based column index

        Returns:
            Cell object containing value, color, and comment

        Raises:
            KeyError: If sheet doesn't exist
            IndexError: If row or col is out of bounds

        Examples:
            >>> cell = state.get_cell("Sheet1", 0, 0)
            >>> print(f"Value: {cell.value}")
            >>> print(f"Color: {cell.color}")
            >>> print(f"Has comment: {cell.has_comment}")
        """
        pass

    @abstractmethod
    def get_cell_value(self, sheet: str, row: int, col: int) -> Any:
        """
        Get cell value only (optimized for performance).

        This is faster than get_cell() when you only need the value.

        Args:
            sheet: Sheet name
            row: Zero-based row index
            col: Zero-based column index

        Returns:
            Cell value (can be str, int, float, None, etc.)

        Raises:
            KeyError: If sheet doesn't exist
            IndexError: If row or col is out of bounds

        Examples:
            >>> value = state.get_cell_value("Sheet1", 0, 0)
            >>> if value is not None:
            ...     print(f"Cell contains: {value}")
        """
        pass

    @abstractmethod
    def set_cell_value(self, sheet: str, row: int, col: int, value: Any) -> None:
        """
        Set cell value.

        Args:
            sheet: Sheet name
            row: Zero-based row index
            col: Zero-based column index
            value: Value to set (str, int, float, etc.)

        Raises:
            KeyError: If sheet doesn't exist
            IndexError: If row or col is out of bounds

        Examples:
            >>> state.set_cell_value("Sheet1", 0, 0, "Translated Text")
            >>> state.set_cell_value("Sheet1", 1, 0, 42)

        Note:
            This modifies the state in-place. Use copy() first if you need
            to preserve the original state.
        """
        pass

    @abstractmethod
    def get_cell_color(self, sheet: str, row: int, col: int) -> Optional[str]:
        """
        Get cell background color.

        Args:
            sheet: Sheet name
            row: Zero-based row index
            col: Zero-based column index

        Returns:
            Color as hex string (e.g., 'FFFF00' for yellow) or None if no color

        Raises:
            KeyError: If sheet doesn't exist

        Examples:
            >>> color = state.get_cell_color("Sheet1", 0, 0)
            >>> if color == 'FFFF00':
            ...     print("This cell is yellow!")
        """
        pass

    @abstractmethod
    def set_cell_color(self, sheet: str, row: int, col: int, color: str) -> None:
        """
        Set cell background color.

        Args:
            sheet: Sheet name
            row: Zero-based row index
            col: Zero-based column index
            color: Color as hex string (e.g., 'FFFF00' for yellow)

        Raises:
            KeyError: If sheet doesn't exist

        Examples:
            >>> state.set_cell_color("Sheet1", 0, 0, "FFFF00")  # Set yellow
        """
        pass

    @abstractmethod
    def get_cell_comment(self, sheet: str, row: int, col: int) -> Optional[str]:
        """
        Get cell comment/note.

        Args:
            sheet: Sheet name
            row: Zero-based row index
            col: Zero-based column index

        Returns:
            Comment text or None if no comment

        Raises:
            KeyError: If sheet doesn't exist

        Examples:
            >>> comment = state.get_cell_comment("Sheet1", 0, 0)
            >>> if comment:
            ...     print(f"Note: {comment}")
        """
        pass

    @abstractmethod
    def set_cell_comment(self, sheet: str, row: int, col: int, comment: str) -> None:
        """
        Set cell comment/note.

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
        pass

    @abstractmethod
    def get_sheet_names(self) -> List[str]:
        """
        Get all sheet names in the workbook.

        Returns:
            List of sheet names in order

        Examples:
            >>> for sheet in state.get_sheet_names():
            ...     print(f"Processing sheet: {sheet}")
        """
        pass

    @abstractmethod
    def get_sheet_dimensions(self, sheet: str) -> Tuple[int, int]:
        """
        Get dimensions of a specific sheet.

        Args:
            sheet: Sheet name

        Returns:
            Tuple of (num_rows, num_cols)

        Raises:
            KeyError: If sheet doesn't exist

        Examples:
            >>> rows, cols = state.get_sheet_dimensions("Sheet1")
            >>> print(f"Sheet1 has {rows} rows and {cols} columns")
        """
        pass

    @abstractmethod
    def iter_cells(self,
                   sheet: Optional[str] = None,
                   include_empty: bool = False) -> Iterator[Cell]:
        """
        Iterate over cells in the state.

        Args:
            sheet: Specific sheet name or None for all sheets
            include_empty: Include cells with no value (default: False)

        Yields:
            Cell objects

        Examples:
            >>> # Iterate all non-empty cells in specific sheet
            >>> for cell in state.iter_cells(sheet="Sheet1"):
            ...     if cell.has_color:
            ...         print(f"{cell.position}: {cell.value}")

            >>> # Iterate all cells (including empty) in all sheets
            >>> for cell in state.iter_cells(include_empty=True):
            ...     process(cell)

        Note:
            This method uses lazy iteration to handle large datasets efficiently.
            Cells are created on-the-fly rather than all at once.
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get state metadata including color and comment maps.

        Returns:
            Dictionary with metadata:
            {
                'filename': str,              # Original filename
                'excel_id': str,              # Unique identifier
                'total_rows': int,            # Total rows across all sheets
                'total_cols': int,            # Maximum columns in any sheet
                'color_map': Dict[str, Dict[Tuple[int, int], str]],
                'comment_map': Dict[str, Dict[Tuple[int, int], str]]
            }

        Examples:
            >>> metadata = state.get_metadata()
            >>> print(f"File: {metadata['filename']}")
            >>> print(f"Total rows: {metadata['total_rows']}")
            >>> # Access color map
            >>> sheet_colors = metadata['color_map'].get('Sheet1', {})
            >>> if (0, 0) in sheet_colors:
            ...     print(f"Cell A1 color: {sheet_colors[(0, 0)]}")

        Note:
            The color_map and comment_map are preserved in metadata for
            compatibility with existing code and for efficient batch access.
        """
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the state.

        Returns:
            Dictionary with statistics:
            {
                'filename': str,
                'excel_id': str,
                'sheet_count': int,
                'total_rows': int,
                'total_cols': int,
                'total_cells': int,
                'total_non_empty': int,
                'sheets': [
                    {
                        'name': str,
                        'rows': int,
                        'cols': int,
                        'cells': int,
                        'non_empty_cells': int,
                        'colored_cells': int,
                        'cells_with_comments': int
                    },
                    ...
                ]
            }

        Examples:
            >>> stats = state.get_statistics()
            >>> print(f"Total cells: {stats['total_cells']}")
            >>> print(f"Non-empty: {stats['total_non_empty']}")
            >>> for sheet_stats in stats['sheets']:
            ...     print(f"{sheet_stats['name']}: {sheet_stats['rows']}x{sheet_stats['cols']}")
        """
        pass

    def __repr__(self) -> str:
        """
        Return string representation of the state.

        Returns:
            Human-readable string with basic info
        """
        stats = self.get_statistics()
        return (f"{self.__class__.__name__}("
                f"sheets={stats['sheet_count']}, "
                f"rows={stats['total_rows']}, "
                f"cols={stats['total_cols']})")

    def __str__(self) -> str:
        """
        Return detailed string representation.

        Returns:
            Multi-line string with statistics
        """
        stats = self.get_statistics()
        lines = [
            f"{self.__class__.__name__}:",
            f"  File: {stats['filename']}",
            f"  Sheets: {stats['sheet_count']}",
            f"  Total Cells: {stats['total_cells']} ({stats['total_non_empty']} non-empty)",
        ]
        return '\n'.join(lines)
