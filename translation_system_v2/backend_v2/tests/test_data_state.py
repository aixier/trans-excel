"""Comprehensive unit tests for DataState module.

Test Coverage:
    - Cell class (creation, validation, properties)
    - DataState abstract interface
    - ExcelState implementation
    - Integration with ExcelDataFrame
    - Performance benchmarks
"""

import pytest
import pandas as pd
import time
from typing import List

from services.data_state import Cell, DataState, ExcelState
from models.excel_dataframe import ExcelDataFrame


# ============================================================================
# Cell Tests
# ============================================================================

class TestCell:
    """Test suite for Cell class."""

    def test_cell_creation_basic(self):
        """Test basic cell creation."""
        cell = Cell("Sheet1", 0, 0)
        assert cell.sheet == "Sheet1"
        assert cell.row == 0
        assert cell.col == 0
        assert cell.value is None
        assert cell.color is None
        assert cell.comment is None

    def test_cell_creation_with_value(self):
        """Test cell creation with value."""
        cell = Cell("Sheet1", 5, 10, value="Hello")
        assert cell.sheet == "Sheet1"
        assert cell.row == 5
        assert cell.col == 10
        assert cell.value == "Hello"

    def test_cell_creation_with_all_attributes(self):
        """Test cell creation with all attributes."""
        cell = Cell(
            sheet="Sheet1",
            row=1,
            col=2,
            value="Test",
            color="FFFF00",
            comment="Important"
        )
        assert cell.sheet == "Sheet1"
        assert cell.row == 1
        assert cell.col == 2
        assert cell.value == "Test"
        assert cell.color == "FFFF00"
        assert cell.comment == "Important"

    def test_cell_validation_negative_row(self):
        """Test that negative row raises ValueError."""
        with pytest.raises(ValueError, match="Row must be non-negative"):
            Cell("Sheet1", -1, 0)

    def test_cell_validation_negative_col(self):
        """Test that negative col raises ValueError."""
        with pytest.raises(ValueError, match="Col must be non-negative"):
            Cell("Sheet1", 0, -1)

    def test_cell_validation_empty_sheet(self):
        """Test that empty sheet name raises ValueError."""
        with pytest.raises(ValueError, match="Sheet name cannot be empty"):
            Cell("", 0, 0)

    def test_cell_position_property(self):
        """Test position property returns correct tuple."""
        cell = Cell("Sheet1", 5, 10)
        assert cell.position == ("Sheet1", 5, 10)

    def test_cell_has_value_with_string(self):
        """Test has_value with string value."""
        cell = Cell("Sheet1", 0, 0, value="Hello")
        assert cell.has_value is True

    def test_cell_has_value_with_number(self):
        """Test has_value with numeric value."""
        cell = Cell("Sheet1", 0, 0, value=42)
        assert cell.has_value is True

    def test_cell_has_value_with_none(self):
        """Test has_value with None."""
        cell = Cell("Sheet1", 0, 0, value=None)
        assert cell.has_value is False

    def test_cell_has_value_with_empty_string(self):
        """Test has_value with empty string."""
        cell = Cell("Sheet1", 0, 0, value="")
        assert cell.has_value is False

    def test_cell_has_value_with_whitespace(self):
        """Test has_value with whitespace only."""
        cell = Cell("Sheet1", 0, 0, value="   ")
        assert cell.has_value is False

    def test_cell_has_color_true(self):
        """Test has_color when color is set."""
        cell = Cell("Sheet1", 0, 0, color="FFFF00")
        assert cell.has_color is True

    def test_cell_has_color_false(self):
        """Test has_color when color is None."""
        cell = Cell("Sheet1", 0, 0)
        assert cell.has_color is False

    def test_cell_has_color_empty_string(self):
        """Test has_color with empty string."""
        cell = Cell("Sheet1", 0, 0, color="")
        assert cell.has_color is False

    def test_cell_has_comment_true(self):
        """Test has_comment when comment is set."""
        cell = Cell("Sheet1", 0, 0, comment="Note")
        assert cell.has_comment is True

    def test_cell_has_comment_false(self):
        """Test has_comment when comment is None."""
        cell = Cell("Sheet1", 0, 0)
        assert cell.has_comment is False

    def test_cell_has_comment_empty_string(self):
        """Test has_comment with empty string."""
        cell = Cell("Sheet1", 0, 0, comment="   ")
        assert cell.has_comment is False

    def test_cell_immutability(self):
        """Test that Cell is immutable (frozen)."""
        cell = Cell("Sheet1", 0, 0, value="Test")
        with pytest.raises(Exception):  # FrozenInstanceError
            cell.value = "Modified"

    def test_cell_repr(self):
        """Test string representation."""
        cell = Cell("Sheet1", 0, 0, value="Test", color="FFFF00")
        repr_str = repr(cell)
        assert "Sheet1" in repr_str
        assert "[0,0]" in repr_str
        assert "Test" in repr_str
        assert "FFFF00" in repr_str

    def test_cell_str(self):
        """Test string method."""
        cell = Cell("Sheet1", 5, 10, value="Hello")
        str_repr = str(cell)
        assert "Sheet1" in str_repr
        assert "5" in str_repr
        assert "10" in str_repr
        assert "Hello" in str_repr


# ============================================================================
# ExcelState Tests
# ============================================================================

class TestExcelState:
    """Test suite for ExcelState class."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        df = pd.DataFrame({
            'A': ['Hello', 'World', None],
            'B': [1, 2, 3],
            'C': ['Test', None, 'Data']
        })
        return df

    @pytest.fixture
    def sample_excel_df(self, sample_dataframe):
        """Create a sample ExcelDataFrame."""
        excel_df = ExcelDataFrame()
        excel_df.filename = "test.xlsx"
        excel_df.excel_id = "test123"
        excel_df.add_sheet("Sheet1", sample_dataframe.copy())

        # Add some colors
        excel_df.set_cell_color("Sheet1", 0, 0, "FFFF00")  # Yellow
        excel_df.set_cell_color("Sheet1", 1, 1, "FF0000")  # Red

        # Add some comments
        excel_df.set_cell_comment("Sheet1", 0, 0, "Important cell")

        return excel_df

    @pytest.fixture
    def sample_state(self, sample_excel_df):
        """Create a sample ExcelState."""
        return ExcelState(sample_excel_df)

    def test_excel_state_creation_empty(self):
        """Test creating empty ExcelState."""
        state = ExcelState()
        assert isinstance(state, DataState)
        assert isinstance(state, ExcelState)
        assert len(state.get_sheet_names()) == 0

    def test_excel_state_creation_with_dataframe(self, sample_excel_df):
        """Test creating ExcelState with ExcelDataFrame."""
        state = ExcelState(sample_excel_df)
        assert len(state.get_sheet_names()) == 1
        assert "Sheet1" in state.get_sheet_names()

    def test_excel_state_from_excel_dataframe_factory(self, sample_excel_df):
        """Test factory method."""
        state = ExcelState.from_excel_dataframe(sample_excel_df)
        assert isinstance(state, ExcelState)
        assert len(state.get_sheet_names()) == 1

    def test_excel_state_excel_dataframe_property(self, sample_state):
        """Test access to underlying ExcelDataFrame."""
        excel_df = sample_state.excel_dataframe
        assert isinstance(excel_df, ExcelDataFrame)
        assert excel_df.filename == "test.xlsx"

    def test_copy_creates_independent_instance(self, sample_state):
        """Test that copy creates independent instance."""
        copy = sample_state.copy()

        # Modify copy
        copy.set_cell_value("Sheet1", 0, 0, "Modified")

        # Original should be unchanged
        original_value = sample_state.get_cell_value("Sheet1", 0, 0)
        copy_value = copy.get_cell_value("Sheet1", 0, 0)

        assert original_value == "Hello"
        assert copy_value == "Modified"

    def test_get_cell_returns_correct_data(self, sample_state):
        """Test get_cell returns Cell with correct data."""
        cell = sample_state.get_cell("Sheet1", 0, 0)

        assert isinstance(cell, Cell)
        assert cell.sheet == "Sheet1"
        assert cell.row == 0
        assert cell.col == 0
        assert cell.value == "Hello"
        assert cell.color == "FFFF00"
        assert cell.comment == "Important cell"

    def test_get_cell_invalid_sheet(self, sample_state):
        """Test get_cell with invalid sheet raises KeyError."""
        with pytest.raises(KeyError, match="Sheet 'NonExistent' not found"):
            sample_state.get_cell("NonExistent", 0, 0)

    def test_get_cell_out_of_bounds_row(self, sample_state):
        """Test get_cell with out of bounds row raises IndexError."""
        with pytest.raises(IndexError, match="Row .* out of bounds"):
            sample_state.get_cell("Sheet1", 999, 0)

    def test_get_cell_out_of_bounds_col(self, sample_state):
        """Test get_cell with out of bounds col raises IndexError."""
        with pytest.raises(IndexError, match="Column .* out of bounds"):
            sample_state.get_cell("Sheet1", 0, 999)

    def test_get_cell_value(self, sample_state):
        """Test get_cell_value returns correct value."""
        value = sample_state.get_cell_value("Sheet1", 0, 0)
        assert value == "Hello"

    def test_get_cell_value_number(self, sample_state):
        """Test get_cell_value with numeric value."""
        value = sample_state.get_cell_value("Sheet1", 0, 1)
        assert value == 1

    def test_get_cell_value_none(self, sample_state):
        """Test get_cell_value with None."""
        value = sample_state.get_cell_value("Sheet1", 2, 0)
        assert value is None or pd.isna(value)

    def test_set_cell_value(self, sample_state):
        """Test set_cell_value modifies value."""
        sample_state.set_cell_value("Sheet1", 0, 0, "Modified")
        value = sample_state.get_cell_value("Sheet1", 0, 0)
        assert value == "Modified"

    def test_set_cell_value_number(self, sample_state):
        """Test set_cell_value with number."""
        sample_state.set_cell_value("Sheet1", 0, 0, 999)
        value = sample_state.get_cell_value("Sheet1", 0, 0)
        assert value == 999

    def test_set_cell_value_invalid_sheet(self, sample_state):
        """Test set_cell_value with invalid sheet raises KeyError."""
        with pytest.raises(KeyError, match="Sheet 'NonExistent' not found"):
            sample_state.set_cell_value("NonExistent", 0, 0, "Value")

    def test_get_cell_color(self, sample_state):
        """Test get_cell_color returns correct color."""
        color = sample_state.get_cell_color("Sheet1", 0, 0)
        assert color == "FFFF00"

    def test_get_cell_color_none(self, sample_state):
        """Test get_cell_color returns None when no color."""
        color = sample_state.get_cell_color("Sheet1", 2, 2)
        assert color is None

    def test_set_cell_color(self, sample_state):
        """Test set_cell_color modifies color."""
        sample_state.set_cell_color("Sheet1", 2, 2, "00FF00")
        color = sample_state.get_cell_color("Sheet1", 2, 2)
        assert color == "00FF00"

    def test_get_cell_comment(self, sample_state):
        """Test get_cell_comment returns correct comment."""
        comment = sample_state.get_cell_comment("Sheet1", 0, 0)
        assert comment == "Important cell"

    def test_get_cell_comment_none(self, sample_state):
        """Test get_cell_comment returns None when no comment."""
        comment = sample_state.get_cell_comment("Sheet1", 1, 1)
        assert comment is None

    def test_set_cell_comment(self, sample_state):
        """Test set_cell_comment modifies comment."""
        sample_state.set_cell_comment("Sheet1", 1, 1, "New comment")
        comment = sample_state.get_cell_comment("Sheet1", 1, 1)
        assert comment == "New comment"

    def test_get_sheet_names(self, sample_state):
        """Test get_sheet_names returns all sheets."""
        names = sample_state.get_sheet_names()
        assert isinstance(names, list)
        assert len(names) == 1
        assert "Sheet1" in names

    def test_get_sheet_dimensions(self, sample_state):
        """Test get_sheet_dimensions returns correct dimensions."""
        rows, cols = sample_state.get_sheet_dimensions("Sheet1")
        assert rows == 3
        assert cols == 3

    def test_get_sheet_dimensions_invalid_sheet(self, sample_state):
        """Test get_sheet_dimensions with invalid sheet raises KeyError."""
        with pytest.raises(KeyError, match="Sheet 'NonExistent' not found"):
            sample_state.get_sheet_dimensions("NonExistent")

    def test_iter_cells_specific_sheet(self, sample_state):
        """Test iter_cells for specific sheet."""
        cells = list(sample_state.iter_cells(sheet="Sheet1", include_empty=False))

        # Should have 7 non-empty cells (3x3 grid with 2 None values)
        non_empty = [c for c in cells if c.has_value]
        assert len(non_empty) == 7

    def test_iter_cells_include_empty(self, sample_state):
        """Test iter_cells including empty cells."""
        cells = list(sample_state.iter_cells(sheet="Sheet1", include_empty=True))

        # Should have all 9 cells (3x3 grid)
        assert len(cells) == 9

    def test_iter_cells_all_sheets(self, sample_excel_df):
        """Test iter_cells for all sheets."""
        # Add another sheet
        df2 = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        sample_excel_df.add_sheet("Sheet2", df2)

        state = ExcelState(sample_excel_df)
        cells = list(state.iter_cells(include_empty=False))

        # Should iterate both sheets
        sheet1_cells = [c for c in cells if c.sheet == "Sheet1"]
        sheet2_cells = [c for c in cells if c.sheet == "Sheet2"]

        assert len(sheet1_cells) > 0
        assert len(sheet2_cells) > 0

    def test_iter_cells_invalid_sheet(self, sample_state):
        """Test iter_cells with invalid sheet raises KeyError."""
        with pytest.raises(KeyError, match="Sheet 'NonExistent' not found"):
            list(sample_state.iter_cells(sheet="NonExistent"))

    def test_iter_cells_yields_cell_objects(self, sample_state):
        """Test that iter_cells yields Cell objects."""
        for cell in sample_state.iter_cells(sheet="Sheet1"):
            assert isinstance(cell, Cell)
            assert cell.sheet == "Sheet1"

    def test_get_metadata(self, sample_state):
        """Test get_metadata returns correct metadata."""
        metadata = sample_state.get_metadata()

        assert metadata['filename'] == "test.xlsx"
        assert metadata['excel_id'] == "test123"
        assert 'color_map' in metadata
        assert 'comment_map' in metadata
        assert isinstance(metadata['color_map'], dict)
        assert isinstance(metadata['comment_map'], dict)

    def test_get_statistics(self, sample_state):
        """Test get_statistics returns correct statistics."""
        stats = sample_state.get_statistics()

        assert stats['filename'] == "test.xlsx"
        assert stats['excel_id'] == "test123"
        assert stats['sheet_count'] == 1
        assert stats['total_rows'] == 3
        assert stats['total_cols'] == 3
        assert stats['total_cells'] == 9
        assert 'sheets' in stats
        assert len(stats['sheets']) == 1

    def test_repr(self, sample_state):
        """Test __repr__ method."""
        repr_str = repr(sample_state)
        assert "ExcelState" in repr_str
        assert "sheets=1" in repr_str

    def test_str(self, sample_state):
        """Test __str__ method."""
        str_repr = str(sample_state)
        assert "ExcelState" in str_repr
        assert "test.xlsx" in str_repr


# ============================================================================
# Multi-Sheet Tests
# ============================================================================

class TestExcelStateMultiSheet:
    """Test ExcelState with multiple sheets."""

    @pytest.fixture
    def multi_sheet_state(self):
        """Create ExcelState with multiple sheets."""
        excel_df = ExcelDataFrame()
        excel_df.filename = "multi.xlsx"
        excel_df.excel_id = "multi123"

        # Sheet 1
        df1 = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6]
        })
        excel_df.add_sheet("Sheet1", df1)
        excel_df.set_cell_color("Sheet1", 0, 0, "FFFF00")

        # Sheet 2
        df2 = pd.DataFrame({
            'X': ['a', 'b'],
            'Y': ['c', 'd']
        })
        excel_df.add_sheet("Sheet2", df2)
        excel_df.set_cell_color("Sheet2", 0, 0, "FF0000")

        # Sheet 3
        df3 = pd.DataFrame({
            'Col1': [10, 20, 30, 40],
            'Col2': [50, 60, 70, 80]
        })
        excel_df.add_sheet("Sheet3", df3)

        return ExcelState(excel_df)

    def test_get_sheet_names_multiple(self, multi_sheet_state):
        """Test get_sheet_names with multiple sheets."""
        names = multi_sheet_state.get_sheet_names()
        assert len(names) == 3
        assert "Sheet1" in names
        assert "Sheet2" in names
        assert "Sheet3" in names

    def test_get_cell_different_sheets(self, multi_sheet_state):
        """Test get_cell from different sheets."""
        cell1 = multi_sheet_state.get_cell("Sheet1", 0, 0)
        cell2 = multi_sheet_state.get_cell("Sheet2", 0, 0)

        assert cell1.value == 1
        assert cell2.value == 'a'
        assert cell1.color == "FFFF00"
        assert cell2.color == "FF0000"

    def test_copy_multi_sheet(self, multi_sheet_state):
        """Test copying state with multiple sheets."""
        copy = multi_sheet_state.copy()

        # Modify copy
        copy.set_cell_value("Sheet1", 0, 0, 999)
        copy.set_cell_value("Sheet2", 0, 0, 'z')

        # Original unchanged
        assert multi_sheet_state.get_cell_value("Sheet1", 0, 0) == 1
        assert multi_sheet_state.get_cell_value("Sheet2", 0, 0) == 'a'

        # Copy changed
        assert copy.get_cell_value("Sheet1", 0, 0) == 999
        assert copy.get_cell_value("Sheet2", 0, 0) == 'z'

    def test_iter_cells_all_sheets(self, multi_sheet_state):
        """Test iterating all cells across all sheets."""
        cells = list(multi_sheet_state.iter_cells(include_empty=False))

        # Count cells per sheet
        sheet1_cells = [c for c in cells if c.sheet == "Sheet1"]
        sheet2_cells = [c for c in cells if c.sheet == "Sheet2"]
        sheet3_cells = [c for c in cells if c.sheet == "Sheet3"]

        assert len(sheet1_cells) == 6  # 3 rows x 2 cols
        assert len(sheet2_cells) == 4  # 2 rows x 2 cols
        assert len(sheet3_cells) == 8  # 4 rows x 2 cols

    def test_statistics_multi_sheet(self, multi_sheet_state):
        """Test statistics with multiple sheets."""
        stats = multi_sheet_state.get_statistics()

        assert stats['sheet_count'] == 3
        assert stats['total_rows'] == 9  # 3 + 2 + 4
        assert len(stats['sheets']) == 3


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Performance tests for DataState operations."""

    @pytest.fixture
    def large_state(self):
        """Create a large ExcelState for performance testing."""
        excel_df = ExcelDataFrame()
        excel_df.filename = "large.xlsx"
        excel_df.excel_id = "large123"

        # Create large DataFrame (1000 rows x 50 cols)
        data = {f'Col{i}': range(1000) for i in range(50)}
        df = pd.DataFrame(data)

        excel_df.add_sheet("Sheet1", df)

        # Add some colors
        for i in range(0, 100, 10):
            excel_df.set_cell_color("Sheet1", i, 0, "FFFF00")

        return ExcelState(excel_df)

    def test_copy_performance(self, large_state):
        """Test that copy is reasonably fast."""
        start = time.time()
        copy = large_state.copy()
        duration = time.time() - start

        # Should complete in less than 1 second
        assert duration < 1.0
        assert copy is not large_state

    def test_iteration_performance(self, large_state):
        """Test that iteration is reasonably fast."""
        start = time.time()
        count = sum(1 for cell in large_state.iter_cells(include_empty=False))
        duration = time.time() - start

        # Should iterate 50K cells in less than 5 seconds
        assert duration < 5.0
        assert count == 50000  # 1000 rows x 50 cols

    def test_cell_access_performance(self, large_state):
        """Test that cell access is fast."""
        start = time.time()

        # Access 1000 cells
        for i in range(1000):
            value = large_state.get_cell_value("Sheet1", i % 1000, 0)

        duration = time.time() - start

        # Should complete in less than 1 second
        assert duration < 1.0


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests with existing code."""

    def test_compatibility_with_excel_dataframe(self):
        """Test that ExcelState is compatible with ExcelDataFrame."""
        # Create ExcelDataFrame using existing pattern
        excel_df = ExcelDataFrame()
        df = pd.DataFrame({
            'A': ['Hello', 'World'],
            'B': [1, 2]
        })
        excel_df.add_sheet("Sheet1", df)
        excel_df.set_cell_color("Sheet1", 0, 0, "FFFF00")
        excel_df.set_cell_comment("Sheet1", 0, 0, "Note")

        # Wrap in ExcelState
        state = ExcelState.from_excel_dataframe(excel_df)

        # Verify data matches
        assert state.get_cell_value("Sheet1", 0, 0) == "Hello"
        assert state.get_cell_color("Sheet1", 0, 0) == "FFFF00"
        assert state.get_cell_comment("Sheet1", 0, 0) == "Note"

        # Verify we can still access ExcelDataFrame
        retrieved_df = state.excel_dataframe
        assert retrieved_df is excel_df
        assert retrieved_df.get_cell_value("Sheet1", 0, 0) == "Hello"

    def test_transformer_pattern(self):
        """Test immutability pattern for transformers."""
        # Create initial state
        excel_df = ExcelDataFrame()
        df = pd.DataFrame({'A': [1, 2, 3]})
        excel_df.add_sheet("Sheet1", df)
        state_0 = ExcelState(excel_df)

        # Simulate transformation
        def transform(input_state: DataState) -> DataState:
            output_state = input_state.copy()
            for i in range(3):
                value = output_state.get_cell_value("Sheet1", i, 0)
                output_state.set_cell_value("Sheet1", i, 0, value * 10)
            return output_state

        # Apply transformation
        state_1 = transform(state_0)

        # Verify original is unchanged
        assert state_0.get_cell_value("Sheet1", 0, 0) == 1
        assert state_0.get_cell_value("Sheet1", 1, 0) == 2

        # Verify new state is transformed
        assert state_1.get_cell_value("Sheet1", 0, 0) == 10
        assert state_1.get_cell_value("Sheet1", 1, 0) == 20

        # Apply another transformation
        state_2 = transform(state_1)

        # Verify chain
        assert state_0.get_cell_value("Sheet1", 0, 0) == 1
        assert state_1.get_cell_value("Sheet1", 0, 0) == 10
        assert state_2.get_cell_value("Sheet1", 0, 0) == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
