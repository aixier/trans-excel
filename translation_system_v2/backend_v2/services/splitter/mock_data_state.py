"""Mock data state for testing the splitter module.

This is a temporary mock implementation until the real DataState module is ready.
"""

from typing import Dict, Any, Optional
import pandas as pd


class MockDataState:
    """Mock data state for testing.

    This class simulates the interface of the real DataState class
    for testing purposes.
    """

    def __init__(self, sheets: Dict[str, pd.DataFrame], metadata: Optional[Dict[str, Any]] = None):
        """Initialize mock data state.

        Args:
            sheets: Dictionary mapping sheet names to DataFrames
            metadata: Optional metadata including color_map, etc.
        """
        self.sheets = sheets
        self.metadata = metadata or {}

    def get_cell_value(self, sheet: str, row: int, col: int) -> Any:
        """Get value of a specific cell.

        Args:
            sheet: Sheet name
            row: Row index (0-based)
            col: Column index (0-based)

        Returns:
            Cell value, or None if not found
        """
        if sheet not in self.sheets:
            return None

        df = self.sheets[sheet]

        if row >= len(df) or col >= len(df.columns):
            return None

        return df.iloc[row, col]

    def get_cell_color(self, sheet: str, row: int, col: int) -> Optional[str]:
        """Get background color of a specific cell.

        Args:
            sheet: Sheet name
            row: Row index (0-based)
            col: Column index (0-based)

        Returns:
            Color hex code (e.g., 'FFFF00') or None
        """
        color_map = self.metadata.get('color_map', {})
        return color_map.get((sheet, row, col))

    def set_cell_color(self, sheet: str, row: int, col: int, color: str) -> None:
        """Set background color of a specific cell.

        Args:
            sheet: Sheet name
            row: Row index (0-based)
            col: Column index (0-based)
            color: Color hex code (e.g., 'FFFF00')
        """
        if 'color_map' not in self.metadata:
            self.metadata['color_map'] = {}

        self.metadata['color_map'][(sheet, row, col)] = color

    @staticmethod
    def create_test_state() -> 'MockDataState':
        """Create a test data state with sample data.

        Returns:
            MockDataState with test data
        """
        # Create test sheet with various scenarios
        test_data = pd.DataFrame({
            'KEY': ['key1', 'key2', 'key3', 'key4', 'key5'],
            'CH': ['你好', '世界', '测试', '例子', '数据'],
            'EN': ['Hello', 'World', 'Test', 'Example', 'Data'],
            'TH': ['', 'โลก', '', 'ตัวอย่าง', ''],
            'TW': ['', '', '測試', '', ''],
        })

        # Create CAPS sheet
        caps_data = pd.DataFrame({
            'KEY': ['cap1', 'cap2'],
            'CH': ['大写', '测试'],
            'EN': ['uppercase', 'test'],
            'TH': ['', ''],
        })

        sheets = {
            'Sheet1': test_data,
            'CAPS_Sheet': caps_data
        }

        # Create color map
        color_map = {
            # Yellow cells in Sheet1
            ('Sheet1', 1, 3): 'FFFF00',  # TH column, row 1 (โลก)
            ('Sheet1', 3, 3): 'FFFF00',  # TH column, row 3 (ตัวอย่าง)

            # Blue cell in Sheet1
            ('Sheet1', 2, 4): '4472C4',  # TW column, row 2 (測試)
        }

        metadata = {
            'color_map': color_map,
            'filename': 'test.xlsx'
        }

        return MockDataState(sheets, metadata)

    @staticmethod
    def create_empty_state() -> 'MockDataState':
        """Create an empty data state.

        Returns:
            MockDataState with no data
        """
        sheets = {
            'Empty': pd.DataFrame()
        }
        return MockDataState(sheets)

    @staticmethod
    def create_large_state(num_rows: int = 1000) -> 'MockDataState':
        """Create a large data state for performance testing.

        Args:
            num_rows: Number of rows to generate

        Returns:
            MockDataState with large dataset
        """
        data = {
            'KEY': [f'key{i}' for i in range(num_rows)],
            'CH': [f'中文{i}' for i in range(num_rows)],
            'EN': [f'English{i}' for i in range(num_rows)],
            'TH': ['' for _ in range(num_rows)],  # All empty for translation
            'TW': ['' for _ in range(num_rows)],
        }

        df = pd.DataFrame(data)
        sheets = {'Sheet1': df}

        # Add some yellow cells
        color_map = {}
        for i in range(0, min(num_rows, 100), 10):
            color_map[('Sheet1', i, 3)] = 'FFFF00'  # Yellow TH cells

        metadata = {'color_map': color_map}

        return MockDataState(sheets, metadata)
