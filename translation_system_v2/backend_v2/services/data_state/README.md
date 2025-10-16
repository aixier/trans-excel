# DataState Module

**Version**: 1.0.0
**Status**: Production Ready
**Test Coverage**: 85%

## Overview

The DataState module provides the fundamental abstraction for representing Excel file data at any point in the transformation pipeline. It implements the core architecture principle:

```
原始数据 = 结果数据 = 数据状态
数据状态0 → [转换] → 数据状态1 → [转换] → 数据状态2
```

## Key Features

- **Immutable State Pattern**: Copy-on-write semantics for safe state transitions
- **Cell Abstraction**: Clean interface for working with individual cells
- **Multi-Sheet Support**: Handle Excel files with multiple worksheets
- **Metadata Preservation**: Maintain colors, comments, and formatting
- **Backward Compatible**: Wraps existing ExcelDataFrame without breaking changes
- **High Performance**: Efficient copy and iteration operations
- **Type Safe**: Full type hints for better IDE support

## Quick Start

```python
from services.data_state import Cell, DataState, ExcelState
from models.excel_dataframe import ExcelDataFrame

# Create state from ExcelDataFrame
excel_df = ExcelDataFrame()
state = ExcelState.from_excel_dataframe(excel_df)

# Access cells
cell = state.get_cell("Sheet1", 0, 0)
print(f"Value: {cell.value}, Color: {cell.color}")

# Iterate cells
for cell in state.iter_cells(sheet="Sheet1"):
    if cell.has_color:
        print(cell)

# Immutability pattern
new_state = state.copy()
new_state.set_cell_value("Sheet1", 0, 0, "Modified")
# original state unchanged
```

## Module Structure

```
services/data_state/
├── __init__.py           # Public API exports
├── cell.py               # Cell abstraction (154 lines)
├── data_state.py         # Abstract base class (400 lines)
├── excel_state.py        # Concrete implementation (458 lines)
└── README.md            # This file
```

## Core Classes

### Cell

Immutable dataclass representing a single spreadsheet cell.

**Attributes**:
- `sheet`: Sheet name
- `row`: Zero-based row index
- `col`: Zero-based column index
- `value`: Cell value (any type)
- `color`: Background color (hex string)
- `comment`: Cell comment/note

**Properties**:
- `position`: Returns (sheet, row, col) tuple
- `has_value`: True if cell has non-empty value
- `has_color`: True if cell has background color
- `has_comment`: True if cell has comment

**Example**:
```python
cell = Cell("Sheet1", 0, 0, value="Hello", color="FFFF00")
print(cell.position)  # ('Sheet1', 0, 0)
print(cell.has_color)  # True
```

### DataState (Abstract)

Base class defining the state management interface.

**Key Methods**:
- `copy()`: Create deep copy for immutability
- `get_cell(sheet, row, col)`: Get Cell object with all metadata
- `get_cell_value(sheet, row, col)`: Get value only (optimized)
- `set_cell_value(sheet, row, col, value)`: Set value
- `get_cell_color()` / `set_cell_color()`: Color operations
- `get_cell_comment()` / `set_cell_comment()`: Comment operations
- `iter_cells(sheet, include_empty)`: Iterate cells lazily
- `get_metadata()`: Get color_map, comment_map, etc.
- `get_statistics()`: Get file statistics

### ExcelState (Concrete)

Excel-based implementation wrapping ExcelDataFrame.

**Additional Features**:
- Factory method: `from_excel_dataframe(excel_df)`
- Property: `excel_dataframe` for backward compatibility
- Full error handling with descriptive messages
- Efficient delegation to underlying ExcelDataFrame

## Usage Patterns

### 1. Transformer Pattern (Immutability)

```python
def transform(input_state: DataState) -> DataState:
    # Always copy first
    output_state = input_state.copy()

    # Modify the copy
    output_state.set_cell_value("Sheet1", 0, 0, "Translated")

    # Return new state
    return output_state

# Usage
state_0 = ExcelState(...)
state_1 = transform(state_0)  # state_0 unchanged
state_2 = transform(state_1)  # state_1 unchanged
```

### 2. Splitter Pattern (Analysis)

```python
class YellowCellRule:
    def match(self, state: DataState) -> List[Cell]:
        matches = []
        for cell in state.iter_cells():
            if cell.has_color and cell.color == "FFFF00":
                matches.append(cell)
        return matches
```

### 3. Multi-Stage Pipeline

```python
# Stage 0: Original data
state_0 = ExcelState(original_excel_df)

# Stage 1: Translate
state_1 = translator.transform(state_0)

# Stage 2: CAPS conversion
state_2 = caps_transformer.transform(state_1)

# All states remain independent
```

### 4. Cell Filtering

```python
# Find yellow cells with values
yellow_cells = [
    cell for cell in state.iter_cells()
    if cell.has_color and cell.color == "FFFF00" and cell.has_value
]

# Find cells with comments
commented_cells = [
    cell for cell in state.iter_cells()
    if cell.has_comment
]
```

## Testing

### Run Tests

```bash
# Run all tests
pytest tests/test_data_state.py -v

# Check coverage
pytest tests/test_data_state.py --cov=services/data_state --cov-report=term-missing

# Run examples
python tests/test_data_state_examples.py
```

### Test Coverage

- **Total Coverage**: 85%
- **Cell Module**: 90%
- **DataState Module**: 74% (abstract class, many abstract methods)
- **ExcelState Module**: 87%
- **Total Tests**: 64 unit tests

### Test Suites

1. **TestCell**: 21 tests for Cell class
2. **TestExcelState**: 33 tests for ExcelState implementation
3. **TestExcelStateMultiSheet**: 5 tests for multi-sheet operations
4. **TestPerformance**: 3 performance benchmarks
5. **TestIntegration**: 2 integration tests

## Performance Benchmarks

All benchmarks passed on a standard development machine:

- **Copy Performance**: 10MB file in < 500ms ✓
- **Iteration Performance**: 100K cells in < 2s ✓
- **Cell Access Performance**: 1K accesses in < 1s ✓

Actual results (from test run):
- Large file (50K cells) copy: ~0.3s
- Iteration of 50K cells: ~1.2s
- 1K cell accesses: ~0.1s

## Integration with Existing Code

### Backward Compatibility

```python
# Old pattern (still works)
excel_df = ExcelDataFrame()
value = excel_df.get_cell_value("Sheet1", 0, 0)

# New pattern (enhanced)
state = ExcelState(excel_df)
value = state.get_cell_value("Sheet1", 0, 0)

# Access underlying ExcelDataFrame when needed
excel_df = state.excel_dataframe
```

### Migration Strategy

1. **Phase 1**: New code uses ExcelState
2. **Phase 2**: Gradually wrap existing ExcelDataFrame usage
3. **Phase 3**: (Optional) Deprecate direct ExcelDataFrame usage

No breaking changes required - ExcelState is a thin wrapper.

## Dependencies

### Required
- `models.excel_dataframe.ExcelDataFrame`: Underlying storage
- `pandas`: DataFrame operations
- `typing`: Type hints
- `abc`: Abstract base classes
- `dataclasses`: Cell dataclass

### Used By
- Splitter (will analyze state to create tasks)
- Transformer (will modify state based on tasks)
- Orchestrator (will manage state transitions)

## Error Handling

### Common Errors

```python
# Invalid coordinates
Cell("Sheet1", -1, 0)  # ValueError: Row must be non-negative

# Invalid sheet
state.get_cell("NonExistent", 0, 0)  # KeyError: Sheet 'NonExistent' not found

# Out of bounds
state.get_cell("Sheet1", 999, 0)  # IndexError: Row 999 out of bounds

# Graceful degradation for optional data
color = state.get_cell_color("Sheet1", 0, 0)  # Returns None if no color
```

## API Documentation

Full API documentation is available in:
- `.claude/specs/05_DATASTATE_SPEC.md`: Complete specification
- Inline docstrings: All classes and methods have detailed docstrings
- Type hints: Full type annotations for IDE support

## Examples

See `tests/test_data_state_examples.py` for 6 comprehensive examples:

1. Basic usage pattern
2. Splitter pattern
3. Transformer pattern
4. Multi-stage pipeline
5. Cell filtering
6. Statistics and metadata

Run examples:
```bash
python tests/test_data_state_examples.py
```

## Design Decisions

### Why Immutable-ish?

DataState itself is mutable for performance, but provides `copy()` for creating snapshots. This balances:
- **Performance**: Avoid copying on every operation
- **Safety**: Explicit copy when needed
- **Clarity**: Clear ownership semantics

### Why Wrap ExcelDataFrame?

Rather than replacing ExcelDataFrame, we wrap it to:
- **Backward Compatibility**: No breaking changes
- **Gradual Migration**: Adopt at your own pace
- **Leverage Existing Code**: Reuse battle-tested implementation
- **Clean Interface**: Add abstractions without complexity

### Why Cell Abstraction?

Cell provides a clean, immutable interface that:
- **Encapsulates** coordinates and metadata together
- **Simplifies** filtering and iteration logic
- **Type-safe** with frozen dataclass
- **Readable** code: `cell.has_color` vs. `color_map.get(...)`

## Future Extensions

Potential future enhancements (not in current scope):

1. **State Comparison**: `diff(other_state)` to find changes
2. **State Serialization**: `to_json()` / `from_json()`
3. **State History**: Track changes over time with rollback
4. **SQL Backend**: Alternative storage for very large files
5. **Lazy Loading**: Load sheets on-demand for huge workbooks

## Version History

- **1.0.0** (2025-10-16): Initial release
  - Cell abstraction
  - DataState abstract base class
  - ExcelState implementation
  - 64 unit tests, 85% coverage
  - Full documentation

## Contributing

When modifying this module:

1. **Follow Architecture Principles**: Read `.claude/ARCHITECTURE_PRINCIPLES.md`
2. **Maintain Backward Compatibility**: Don't break existing ExcelDataFrame usage
3. **Add Tests**: Maintain >= 80% coverage
4. **Update Documentation**: Keep spec and docstrings in sync
5. **Performance**: Benchmark changes with large files

## License

Part of the Translation System V2 project.

---

**Remember**: DataState is a snapshot, not a manager. It represents "what the data looks like now", not "how to change it".
