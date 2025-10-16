"""Real-world usage examples for DataState module.

This file demonstrates how to use DataState in practical scenarios,
including integration with the existing codebase.
"""

import pandas as pd
from typing import List

from services.data_state import Cell, DataState, ExcelState
from models.excel_dataframe import ExcelDataFrame


def example_1_basic_usage():
    """Example 1: Basic usage pattern."""
    # Create Excel data
    excel_df = ExcelDataFrame()
    excel_df.filename = "translation.xlsx"
    excel_df.excel_id = "trans_001"

    # Add sheet with data
    df = pd.DataFrame({
        'CH': ['你好', '世界', '测试'],
        'EN': ['Hello', 'World', 'Test'],
        'PT': [None, None, None]  # To be translated
    })
    excel_df.add_sheet("Sheet1", df)

    # Mark cells that need translation (yellow)
    for row in range(3):
        excel_df.set_cell_color("Sheet1", row, 2, "FFFF00")

    # Wrap in DataState
    state = ExcelState.from_excel_dataframe(excel_df)

    # Find cells that need translation
    cells_to_translate = []
    for cell in state.iter_cells(sheet="Sheet1"):
        if cell.has_color and cell.color == "FFFF00":
            cells_to_translate.append(cell)

    print(f"Found {len(cells_to_translate)} cells to translate")
    return state


def example_2_splitter_pattern():
    """Example 2: Splitter pattern - analyze state to create tasks."""
    # Create state
    excel_df = ExcelDataFrame()
    df = pd.DataFrame({
        'CH': ['你好', '世界', None, '测试'],
        'PT': [None, None, None, None]
    })
    excel_df.add_sheet("Sheet1", df)
    excel_df.set_cell_color("Sheet1", 1, 0, "FFFF00")  # Yellow = retranslate

    state = ExcelState(excel_df)

    # Simulate splitter: find empty PT cells with CH source
    tasks = []
    for row in range(len(df)):
        ch_cell = state.get_cell("Sheet1", row, 0)
        pt_cell = state.get_cell("Sheet1", row, 1)

        if ch_cell.has_value and not pt_cell.has_value:
            # Check if yellow (priority translation)
            is_priority = ch_cell.has_color and ch_cell.color == "FFFF00"

            task = {
                'sheet': "Sheet1",
                'row': row,
                'col': 1,  # PT column
                'source_text': ch_cell.value,
                'priority': 10 if is_priority else 5
            }
            tasks.append(task)

    print(f"Created {len(tasks)} translation tasks")
    return tasks


def example_3_transformer_pattern():
    """Example 3: Transformer pattern - modify state based on tasks."""
    # Create initial state
    excel_df = ExcelDataFrame()
    df = pd.DataFrame({
        'CH': ['你好', '世界', '测试'],
        'PT': [None, None, None]
    })
    excel_df.add_sheet("Sheet1", df)

    state_0 = ExcelState(excel_df)

    # Simulate translation tasks
    tasks = [
        {'row': 0, 'col': 1, 'result': 'Olá'},
        {'row': 1, 'col': 1, 'result': 'Mundo'},
        {'row': 2, 'col': 1, 'result': 'Teste'}
    ]

    # Transformer: apply tasks to create new state
    def transform(input_state: DataState, task_list: List[dict]) -> DataState:
        """Apply translation tasks to create new state."""
        # Always copy first (immutability)
        output_state = input_state.copy()

        # Apply each task
        for task in task_list:
            output_state.set_cell_value(
                "Sheet1",
                task['row'],
                task['col'],
                task['result']
            )

        return output_state

    # Apply transformation
    state_1 = transform(state_0, tasks)

    # Verify original unchanged
    assert state_0.get_cell_value("Sheet1", 0, 1) is None
    print("Original state unchanged: PT column is still empty")

    # Verify new state has translations
    assert state_1.get_cell_value("Sheet1", 0, 1) == 'Olá'
    print("New state has translations: PT column filled")

    return state_0, state_1


def example_4_multi_stage_pipeline():
    """Example 4: Multi-stage transformation pipeline."""
    # Stage 0: Original data
    excel_df = ExcelDataFrame()
    df = pd.DataFrame({
        'CH': ['你好', '世界'],
        'EN': [None, None],
        'PT': [None, None]
    })
    excel_df.add_sheet("Sheet1", df)
    state_0 = ExcelState(excel_df)

    print("State 0: Original data (CH only)")

    # Stage 1: Translate CH -> EN
    state_1 = state_0.copy()
    state_1.set_cell_value("Sheet1", 0, 1, "Hello")
    state_1.set_cell_value("Sheet1", 1, 1, "World")
    print("State 1: Added EN translations")

    # Stage 2: Translate EN -> PT
    state_2 = state_1.copy()
    state_2.set_cell_value("Sheet1", 0, 2, "Olá")
    state_2.set_cell_value("Sheet1", 1, 2, "Mundo")
    print("State 2: Added PT translations")

    # Stage 3: Convert to uppercase (CAPS)
    state_3 = state_2.copy()
    for row in range(2):
        for col in range(1, 3):  # EN and PT columns
            value = state_3.get_cell_value("Sheet1", row, col)
            if value:
                state_3.set_cell_value("Sheet1", row, col, value.upper())
    print("State 3: Converted to uppercase")

    # Verify all states are independent
    assert state_0.get_cell_value("Sheet1", 0, 1) is None
    assert state_1.get_cell_value("Sheet1", 0, 1) == "Hello"
    assert state_2.get_cell_value("Sheet1", 0, 2) == "Olá"
    assert state_3.get_cell_value("Sheet1", 0, 1) == "HELLO"

    print("All states are independent!")
    return state_0, state_1, state_2, state_3


def example_5_cell_filtering():
    """Example 5: Advanced cell filtering."""
    # Create complex state
    excel_df = ExcelDataFrame()
    df = pd.DataFrame({
        'A': ['Text1', None, 'Text3', None],
        'B': [1, 2, 3, 4],
        'C': ['', 'Value', None, 'Data']
    })
    excel_df.add_sheet("Sheet1", df)

    # Add colors
    excel_df.set_cell_color("Sheet1", 0, 0, "FFFF00")  # Yellow
    excel_df.set_cell_color("Sheet1", 2, 0, "FFFF00")  # Yellow

    # Add comments
    excel_df.set_cell_comment("Sheet1", 1, 1, "Important")

    state = ExcelState(excel_df)

    # Find yellow cells with values
    yellow_cells = [
        cell for cell in state.iter_cells()
        if cell.has_color and cell.color == "FFFF00" and cell.has_value
    ]
    print(f"Yellow cells with values: {len(yellow_cells)}")

    # Find cells with comments
    commented_cells = [
        cell for cell in state.iter_cells()
        if cell.has_comment
    ]
    print(f"Cells with comments: {len(commented_cells)}")

    # Find empty cells
    empty_cells = [
        cell for cell in state.iter_cells(include_empty=True)
        if not cell.has_value
    ]
    print(f"Empty cells: {len(empty_cells)}")

    return yellow_cells, commented_cells, empty_cells


def example_6_statistics_and_metadata():
    """Example 6: Using statistics and metadata."""
    # Create multi-sheet workbook
    excel_df = ExcelDataFrame()
    excel_df.filename = "complex.xlsx"
    excel_df.excel_id = "complex_001"

    # Sheet 1: Translations
    df1 = pd.DataFrame({
        'CH': ['你好', '世界', '测试'],
        'EN': ['Hello', 'World', 'Test'],
        'PT': ['Olá', None, 'Teste']
    })
    excel_df.add_sheet("Translations", df1)
    excel_df.set_cell_color("Translations", 1, 2, "FFFF00")

    # Sheet 2: Metadata
    df2 = pd.DataFrame({
        'Key': ['Author', 'Date', 'Version'],
        'Value': ['John', '2025-10-16', '1.0']
    })
    excel_df.add_sheet("Metadata", df2)

    state = ExcelState(excel_df)

    # Get statistics
    stats = state.get_statistics()
    print(f"File: {stats['filename']}")
    print(f"Total sheets: {stats['sheet_count']}")
    print(f"Total cells: {stats['total_cells']}")
    print(f"Non-empty cells: {stats['total_non_empty']}")

    for sheet_stats in stats['sheets']:
        print(f"  {sheet_stats['name']}: {sheet_stats['rows']}x{sheet_stats['cols']}")
        print(f"    Colored cells: {sheet_stats['colored_cells']}")

    # Get metadata
    metadata = state.get_metadata()
    print(f"\nMetadata:")
    print(f"  Excel ID: {metadata['excel_id']}")
    print(f"  Color map: {len(metadata['color_map'])} sheets")

    return stats, metadata


if __name__ == '__main__':
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    example_1_basic_usage()

    print("\n" + "=" * 60)
    print("Example 2: Splitter Pattern")
    print("=" * 60)
    example_2_splitter_pattern()

    print("\n" + "=" * 60)
    print("Example 3: Transformer Pattern")
    print("=" * 60)
    example_3_transformer_pattern()

    print("\n" + "=" * 60)
    print("Example 4: Multi-Stage Pipeline")
    print("=" * 60)
    example_4_multi_stage_pipeline()

    print("\n" + "=" * 60)
    print("Example 5: Cell Filtering")
    print("=" * 60)
    example_5_cell_filtering()

    print("\n" + "=" * 60)
    print("Example 6: Statistics and Metadata")
    print("=" * 60)
    example_6_statistics_and_metadata()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
