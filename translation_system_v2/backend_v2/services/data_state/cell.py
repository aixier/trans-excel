"""Cell abstraction for spreadsheet cells.

This module provides a clean abstraction for working with individual cells
in a spreadsheet, encapsulating coordinates, values, and metadata.
"""

from dataclasses import dataclass
from typing import Any, Optional, Tuple


@dataclass(frozen=True)
class Cell:
    """
    Represents a single cell in a spreadsheet.

    Attributes:
        sheet: Sheet name where the cell is located
        row: Zero-based row index
        col: Zero-based column index
        value: Cell value (can be any type: str, int, float, etc.)
        color: Cell background color as hex string (e.g., 'FFFF00' for yellow)
        comment: Cell comment/note text

    Examples:
        >>> cell = Cell("Sheet1", 0, 0, "Hello", "FFFF00", "Important")
        >>> cell.position
        ('Sheet1', 0, 0)
        >>> cell.has_value
        True
        >>> cell.has_color
        True

    Note:
        This class is immutable (frozen=True) to prevent accidental modifications.
        Create a new Cell instance if you need to change values.
    """

    sheet: str
    row: int
    col: int
    value: Any = None
    color: Optional[str] = None
    comment: Optional[str] = None

    def __post_init__(self):
        """Validate cell coordinates."""
        if self.row < 0:
            raise ValueError(f"Row must be non-negative, got {self.row}")
        if self.col < 0:
            raise ValueError(f"Col must be non-negative, got {self.col}")
        if not self.sheet:
            raise ValueError("Sheet name cannot be empty")

    @property
    def position(self) -> Tuple[str, int, int]:
        """
        Get cell position as a tuple.

        Returns:
            Tuple of (sheet, row, col)

        Examples:
            >>> cell = Cell("Sheet1", 5, 10)
            >>> cell.position
            ('Sheet1', 5, 10)
        """
        return (self.sheet, self.row, self.col)

    @property
    def has_value(self) -> bool:
        """
        Check if cell has a non-empty value.

        Returns:
            True if cell has a value (not None and not empty string)

        Examples:
            >>> Cell("Sheet1", 0, 0, "Hello").has_value
            True
            >>> Cell("Sheet1", 0, 0, "").has_value
            False
            >>> Cell("Sheet1", 0, 0, None).has_value
            False
            >>> Cell("Sheet1", 0, 0, "   ").has_value
            False
        """
        if self.value is None:
            return False
        # Convert to string and check if it's not just whitespace
        return str(self.value).strip() != ''

    @property
    def has_color(self) -> bool:
        """
        Check if cell has a background color.

        Returns:
            True if cell has a color defined

        Examples:
            >>> Cell("Sheet1", 0, 0, color="FFFF00").has_color
            True
            >>> Cell("Sheet1", 0, 0).has_color
            False
        """
        return self.color is not None and self.color != ''

    @property
    def has_comment(self) -> bool:
        """
        Check if cell has a comment.

        Returns:
            True if cell has a comment defined

        Examples:
            >>> Cell("Sheet1", 0, 0, comment="Note").has_comment
            True
            >>> Cell("Sheet1", 0, 0).has_comment
            False
        """
        return self.comment is not None and self.comment.strip() != ''

    def __repr__(self) -> str:
        """
        Return detailed string representation.

        Returns:
            String representation with all non-None attributes
        """
        parts = [f"{self.sheet}[{self.row},{self.col}]"]
        if self.has_value:
            # Truncate long values
            value_str = str(self.value)
            if len(value_str) > 30:
                value_str = value_str[:27] + "..."
            parts.append(f"value={value_str!r}")
        if self.has_color:
            parts.append(f"color={self.color}")
        if self.has_comment:
            comment_str = self.comment
            if len(comment_str) > 20:
                comment_str = comment_str[:17] + "..."
            parts.append(f"comment={comment_str!r}")
        return f"Cell({', '.join(parts)})"

    def __str__(self) -> str:
        """
        Return simple string representation.

        Returns:
            Human-readable string
        """
        return f"Cell at {self.sheet}[{self.row},{self.col}]: {self.value}"
