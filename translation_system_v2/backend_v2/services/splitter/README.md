# Splitter Module

The Splitter module is responsible for analyzing data state and generating tasks based on configurable rules. It follows the architecture principle: **"Splitter identifies tasks, but never executes transformations."**

## Module Structure

```
services/splitter/
├── __init__.py              # Module exports
├── split_rule.py            # Base class for split rules
├── task_splitter.py         # Main splitter implementation
├── mock_data_state.py       # Mock data state for testing
├── README.md               # This file
└── rules/                  # Predefined split rules
    ├── __init__.py
    ├── empty_cell.py       # EmptyCellRule
    ├── yellow_cell.py      # YellowCellRule
    ├── blue_cell.py        # BlueCellRule
    └── caps_sheet.py       # CapsSheetRule
```

## Quick Start

```python
from services.splitter import TaskSplitter, EmptyCellRule, YellowCellRule

# Create splitter
splitter = TaskSplitter()

# Define rules
rules = [
    YellowCellRule(),   # Priority 9 - highest
    EmptyCellRule(),    # Priority 5 - normal
]

# Split data state into tasks
task_df = splitter.split(data_state, rules)

# Get statistics
stats = splitter.get_statistics()
print(f"Created {stats['total']} tasks")
```

## Core Components

### 1. TaskSplitter

Main class that applies rules to data state and generates task DataFrame.

**Key Features:**
- Iterates through all cells in data state
- Applies rules in priority order
- Prevents duplicate tasks (one task per cell)
- Returns sorted TaskDataFrame by priority
- Validates data state and tasks

### 2. SplitRule (Base Class)

Abstract base class for creating custom split rules.

**Required Methods:**
- `match(cell, context) -> bool`: Check if cell matches this rule
- `create_task(cell, context) -> Dict`: Create task for matched cell
- `get_priority() -> int`: Return rule priority (1-10)
- `get_operation_type() -> str`: Return operation type

## Predefined Rules

### EmptyCellRule (Priority: 5)

Identifies empty cells in target language columns that need translation.

**Matches:**
- Empty cells in target columns (TH, TW, PT, EN, etc.)
- Has source text in CH or EN columns

**Task Operation:** `translate`

### YellowCellRule (Priority: 9)

Identifies yellow-highlighted cells that need retranslation.

**Matches:**
- Cells with yellow background color
- In target language columns

**Task Operation:** `translate`

**Special Features:**
- High priority (processed first)
- Includes `reference_en` field for context
- Marks as retranslation in metadata

### BlueCellRule (Priority: 7)

Identifies blue-highlighted cells requiring special handling.

**Matches:**
- Cells with blue background color
- In target language columns

**Task Operation:** `translate`

**Special Features:**
- Medium priority
- Marks as requiring context
- Preserves original value

### CapsSheetRule (Priority: 3)

Identifies cells in CAPS sheets that need uppercase conversion.

**Matches:**
- Cells in sheets with 'CAPS' in name
- In target language columns (excludes KEY, CH, CN)

**Task Operation:** `uppercase` (**NOT** `translate`)

**Special Features:**
- Low priority (processed after translation)
- Operation type is `uppercase`
- Designed for post-translation processing

## Rule Priority System

Rules are applied in priority order (highest first):

| Priority | Rule | Purpose |
|----------|------|---------|
| 9 | YellowCellRule | Urgent retranslations |
| 7 | BlueCellRule | Special handling |
| 5 | EmptyCellRule | Normal translations |
| 3 | CapsSheetRule | Post-processing |

**Important:** Only ONE rule matches per cell. Higher priority rules take precedence.

## Task DataFrame Schema

The splitter generates tasks with the following columns:

```python
{
    'task_id': str,           # Unique identifier (e.g., 'EMPTY_Sheet1_0_2')
    'operation': str,         # 'translate' or 'uppercase'
    'priority': int,          # 1-10 (higher = more urgent)
    'sheet_name': str,        # Sheet name
    'row_idx': int,           # Row index (0-based)
    'col_idx': int,           # Column index (0-based)
    'cell_ref': str,          # Excel reference (e.g., 'A1')
    'source_text': str,       # Source text for translation
    'source_lang': str,       # Source language ('CH' or 'EN')
    'target_lang': str,       # Target language ('TH', 'TW', etc.)
    'status': str,            # Always 'pending' initially
    'result': str,            # Empty initially
    'reference_en': str,      # EN reference (yellow cells only)
    'metadata': Dict,         # Additional metadata
}
```

## Creating Custom Rules

To create a custom rule, inherit from `SplitRule`:

```python
from services.splitter import SplitRule

class MyCustomRule(SplitRule):
    def match(self, cell, context):
        """Check if cell matches your criteria"""
        # Your matching logic here
        return True  # or False

    def create_task(self, cell, context):
        """Create task for matched cell"""
        return {
            'task_id': f"CUSTOM_{context['sheet_name']}_{context['row_idx']}_{context['col_idx']}",
            'operation': 'my_operation',
            'priority': 6,
            'sheet_name': context['sheet_name'],
            'row_idx': context['row_idx'],
            'col_idx': context['col_idx'],
            'cell_ref': self._generate_cell_ref(context['row_idx'], context['col_idx']),
            'source_text': str(cell),
            'target_lang': context['column_name'],
            'status': 'pending',
            'metadata': {'rule': 'MyCustomRule'}
        }

    def get_priority(self):
        return 6

    def get_operation_type(self):
        return 'my_operation'
```

## Testing

The module includes comprehensive tests:

- **Unit Tests:** `tests/splitter/test_rules.py`
  - Tests for each rule individually
  - 25 test cases

- **Integration Tests:** `tests/splitter/test_task_splitter.py`
  - Tests for TaskSplitter
  - 17 test cases
  - Edge cases and performance tests

**Run Tests:**
```bash
# Run all splitter tests
python3 -m pytest tests/splitter/ -v

# Run with coverage
python3 -m pytest tests/splitter/ --cov=services/splitter --cov-report=term-missing
```

**Test Coverage:** 87% (exceeds 80% requirement)

## Architecture Compliance

This module strictly follows the architecture principles:

✅ **Does:**
- Identifies cells that need processing
- Creates task descriptions
- Validates data state
- Returns task DataFrame

❌ **Does NOT:**
- Execute translations
- Modify data state
- Call LLM APIs
- Store task results

## Performance

- **Large Dataset:** Handles 1000+ rows in < 5 seconds
- **Rule Matching:** Optimized with priority-based early exit
- **Memory:** Efficient batch task creation

## Error Handling

```python
from services.splitter import (
    SplitterError,
    InvalidDataStateError,
    RuleConflictError
)

try:
    task_df = splitter.split(data_state, rules)
except InvalidDataStateError as e:
    print(f"Invalid data state: {e}")
except RuleConflictError as e:
    print(f"Rule conflict: {e}")
```

## Dependencies

- `pandas`: DataFrame operations
- `models.task_dataframe`: TaskDataFrame schema
- Data state object with:
  - `sheets`: Dict[str, pd.DataFrame]
  - `metadata`: Dict with optional `color_map`

## Integration Example

```python
from services.splitter import (
    TaskSplitter,
    EmptyCellRule,
    YellowCellRule,
    BlueCellRule,
    CapsSheetRule
)

# Phase 1: Translation tasks
splitter = TaskSplitter()
translation_rules = [
    YellowCellRule(),   # Retranslations first
    BlueCellRule(),     # Special handling
    EmptyCellRule(),    # Normal translations
]

translation_tasks = splitter.split(data_state, translation_rules)

# Phase 2: CAPS conversion (after translation)
caps_rules = [CapsSheetRule()]
caps_tasks = splitter.split(data_state, caps_rules)
```

## Next Steps

After the Splitter generates tasks:
1. **Transformer** module will execute the tasks
2. **Processor** modules (LLM, Uppercase) will perform operations
3. **Orchestrator** will coordinate the workflow

## Notes

- Task IDs follow format: `{RULE_TYPE}_{SHEET}_{ROW}_{COL}`
- Cell references use Excel notation (A1, B2, etc.)
- Empty sheets are handled gracefully (no tasks generated)
- CAPS tasks have `operation='uppercase'`, not `'translate'`

---

**Remember:** The Splitter identifies WHAT needs to be done, not HOW to do it!
