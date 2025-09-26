"""Excel DataFrame model definition."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd


@dataclass
class ExcelDataFrame:
    """Structure to store Excel data with metadata."""

    # Main data storage
    sheets: Dict[str, pd.DataFrame] = field(default_factory=dict)

    # Color information: {sheet_name: {(row, col): color_hex}}
    color_map: Dict[str, Dict[Tuple[int, int], str]] = field(default_factory=dict)

    # Comment information: {sheet_name: {(row, col): comment_text}}
    comment_map: Dict[str, Dict[Tuple[int, int], str]] = field(default_factory=dict)

    # File metadata
    filename: str = ""
    excel_id: str = ""
    total_rows: int = 0
    total_cols: int = 0

    def add_sheet(self, sheet_name: str, df: pd.DataFrame) -> None:
        """Add a sheet to the Excel structure."""
        self.sheets[sheet_name] = df
        self.total_rows += len(df)
        self.total_cols = max(self.total_cols, len(df.columns))

        # Initialize maps for this sheet if not exists
        if sheet_name not in self.color_map:
            self.color_map[sheet_name] = {}
        if sheet_name not in self.comment_map:
            self.comment_map[sheet_name] = {}

    def get_sheet(self, sheet_name: str) -> Optional[pd.DataFrame]:
        """Get a specific sheet DataFrame."""
        return self.sheets.get(sheet_name)

    def set_cell_color(self, sheet_name: str, row: int, col: int, color: str) -> None:
        """Set color for a specific cell."""
        if sheet_name not in self.color_map:
            self.color_map[sheet_name] = {}
        self.color_map[sheet_name][(row, col)] = color

    def get_cell_color(self, sheet_name: str, row: int, col: int) -> Optional[str]:
        """Get color of a specific cell."""
        return self.color_map.get(sheet_name, {}).get((row, col))

    def set_cell_comment(self, sheet_name: str, row: int, col: int, comment: str) -> None:
        """Set comment for a specific cell."""
        if sheet_name not in self.comment_map:
            self.comment_map[sheet_name] = {}
        self.comment_map[sheet_name][(row, col)] = comment

    def get_cell_comment(self, sheet_name: str, row: int, col: int) -> Optional[str]:
        """Get comment of a specific cell."""
        return self.comment_map.get(sheet_name, {}).get((row, col))

    def get_cell_value(self, sheet_name: str, row: int, col: int) -> Any:
        """Get value of a specific cell."""
        sheet = self.get_sheet(sheet_name)
        if sheet is not None and row < len(sheet) and col < len(sheet.columns):
            return sheet.iloc[row, col]
        return None

    def set_cell_value(self, sheet_name: str, row: int, col: int, value: Any) -> None:
        """Set value of a specific cell."""
        sheet = self.get_sheet(sheet_name)
        if sheet is not None and row < len(sheet) and col < len(sheet.columns):
            sheet.iloc[row, col] = value

    def get_sheet_names(self) -> List[str]:
        """Get all sheet names."""
        return list(self.sheets.keys())

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the Excel file."""
        stats = {
            'filename': self.filename,
            'excel_id': self.excel_id,
            'sheet_count': len(self.sheets),
            'sheets': []
        }

        for sheet_name, df in self.sheets.items():
            # Convert numpy types to Python types
            non_empty = df.notna().sum().sum()
            sheet_stats = {
                'name': sheet_name,
                'rows': int(len(df)),
                'cols': int(len(df.columns)),
                'cells': int(len(df) * len(df.columns)),
                'non_empty_cells': int(non_empty),
                'colored_cells': int(len(self.color_map.get(sheet_name, {}))),
                'cells_with_comments': int(len(self.comment_map.get(sheet_name, {})))
            }
            stats['sheets'].append(sheet_stats)

        stats['total_rows'] = int(sum(s['rows'] for s in stats['sheets']))
        stats['total_cols'] = int(max((s['cols'] for s in stats['sheets']), default=0))
        stats['total_cells'] = int(sum(s['cells'] for s in stats['sheets']))
        stats['total_non_empty'] = int(sum(s['non_empty_cells'] for s in stats['sheets']))

        return stats

    def clone(self) -> 'ExcelDataFrame':
        """Create a deep copy of the Excel structure."""
        new_excel = ExcelDataFrame()
        new_excel.filename = self.filename
        new_excel.excel_id = self.excel_id

        for sheet_name, df in self.sheets.items():
            new_excel.add_sheet(sheet_name, df.copy())

        new_excel.color_map = {
            sheet: dict(colors) for sheet, colors in self.color_map.items()
        }
        new_excel.comment_map = {
            sheet: dict(comments) for sheet, comments in self.comment_map.items()
        }

        return new_excel