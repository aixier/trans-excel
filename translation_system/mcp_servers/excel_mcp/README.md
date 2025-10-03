# Excel MCP Server

A universal Excel processing MCP server that provides comprehensive Excel file analysis, parsing, conversion, and **translation task splitting** capabilities.

> **Note**: This server integrates functionality from the deprecated `task_mcp` server, providing a unified solution for Excel analysis and translation task management.

## Features

### Analysis & Processing
- **Async Processing**: Excel analysis runs asynchronously with session-based tracking
- **Flexible Input**: Supports both HTTP URL download and direct file upload
- **Comprehensive Analysis**:
  - File structure analysis (sheets, rows, columns)
  - Language detection (source and target languages)
  - Format detection (colors, comments, formulas)
  - Task estimation for translation projects
- **Multiple Output Formats**: JSON, CSV conversion

### Translation Task Management (NEW)
- **Task Splitting**: Intelligently split Excel into translation tasks
- **Color-based Task Types**:
  - Yellow cells → Re-translation tasks
  - Blue cells → Shortening tasks
  - Empty cells → Normal translation tasks
- **Batch Allocation**: Group tasks by target language (~50,000 chars/batch)
- **Context Extraction**: Extract game info, neighbors, comments for better translation
- **Task Export**: Export tasks to Excel/JSON/CSV formats

### Infrastructure
- **Session Management**: Memory-based session storage with automatic expiration (8 hours)
- **Configurable Color Detection**: YAML-based color range configuration
- **JWT Authentication**: Secure token-based access control

## Architecture

```
excel_mcp/
├── server.py                        # MCP stdio entry point
├── mcp_tools.py                     # 10 tool definitions
├── mcp_handler.py                   # Tool execution handlers
│
├── config/
│   └── color_config.yaml            # Color detection configuration
│
├── utils/
│   ├── http_client.py               # HTTP file downloads
│   ├── token_validator.py           # JWT validation
│   ├── session_manager.py           # Session management
│   ├── color_detector.py            # Configurable color detection
│   ├── language_mapper.py           # Language code mapping
│   └── excel_loader.py              # Excel loading with openpyxl
│
├── services/
│   ├── excel_analyzer.py            # Comprehensive analysis
│   ├── task_splitter_service.py     # Translation task splitting
│   ├── task_exporter.py             # Task export (Excel/JSON/CSV)
│   └── task_queue.py                # Async task processing
│
└── models/
    ├── excel_dataframe.py           # Excel data structure
    ├── session_data.py              # Session data model
    ├── analysis_result.py           # Analysis result model
    └── task_models.py               # Task models (TaskType, TaskSummary)
```

## MCP Tools (10 Total)

### Analysis Tools

### 1. excel_analyze

Submit Excel file for analysis (async). Returns `session_id` for tracking.

**Input Methods**:
- Method A: HTTP URL download
- Method B: Direct file upload (base64)

**Parameters**:
```json
{
  "token": "Bearer xxx",
  "file_url": "http://example.com/file.xlsx",  // OR
  "file": "base64_encoded_data",
  "filename": "myfile.xlsx",
  "options": {
    "detect_language": true,
    "detect_formats": true,
    "analyze_colors": true
  }
}
```

**Response**:
```json
{
  "session_id": "excel_abc123",
  "status": "queued",
  "message": "Analysis task submitted to queue",
  "estimated_time": 30
}
```

### 2. excel_get_status

Query analysis status and retrieve results.

**Parameters**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123"
}
```

**Response (Processing)**:
```json
{
  "session_id": "excel_abc123",
  "status": "processing",
  "progress": 45,
  "message": "Processing... 45%"
}
```

**Response (Completed)**:
```json
{
  "session_id": "excel_abc123",
  "status": "completed",
  "progress": 100,
  "result": {
    "file_info": {
      "filename": "data.xlsx",
      "sheets": ["Sheet1", "Sheet2"],
      "sheet_count": 2,
      "total_rows": 1000,
      "total_cols": 10
    },
    "language_detection": {
      "source_langs": ["EN", "CH"],
      "target_langs": ["TR", "TH", "PT"],
      "sheet_details": [...]
    },
    "statistics": {
      "estimated_tasks": 800,
      "task_breakdown": {
        "normal_tasks": 700,
        "yellow_tasks": 80,
        "blue_tasks": 20
      },
      "char_distribution": {
        "min": 5,
        "max": 200,
        "avg": 45.5,
        "total": 36400
      }
    },
    "format_analysis": {
      "colored_cells": 150,
      "color_distribution": {
        "yellow": 80,
        "blue": 50,
        "other": 20
      },
      "cells_with_comments": 30
    }
  }
}
```

### 3. excel_get_sheets

Get list of sheets in the analyzed Excel.

**Parameters**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123"
}
```

**Response**:
```json
{
  "session_id": "excel_abc123",
  "sheets": [
    {"name": "Sheet1", "rows": 500, "cols": 8},
    {"name": "Sheet2", "rows": 500, "cols": 8}
  ]
}
```

### 4. excel_parse_sheet

Parse and return data from a specific sheet.

**Parameters**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123",
  "sheet_name": "Sheet1",
  "limit": 100,
  "offset": 0
}
```

**Response**:
```json
{
  "session_id": "excel_abc123",
  "sheet_name": "Sheet1",
  "data": [
    {"A": "ID", "B": "Source", "C": "Target"},
    {"A": "1", "B": "Hello", "C": "你好"}
  ],
  "total_rows": 500,
  "returned_rows": 100,
  "offset": 0
}
```

### 5. excel_convert_to_json

Convert Excel to JSON format.

**Parameters**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123",
  "sheet_name": "Sheet1"  // Optional, converts all if not specified
}
```

### 6. excel_convert_to_csv

Convert Excel sheet to CSV format.

**Parameters**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123",
  "sheet_name": "Sheet1"
}
```

### Translation Task Tools

### 7. excel_split_tasks

Split Excel into translation tasks based on analysis. Detects yellow (re-translation), blue (shortening), and normal tasks.

**Parameters**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123",
  "source_lang": "CH",           // Optional, auto-detect if not specified
  "target_langs": ["PT", "TH", "VN"],
  "extract_context": true,       // Optional, default: true
  "context_options": {           // Optional
    "game_info": true,
    "neighbors": true,
    "comments": true,
    "content_analysis": true,
    "sheet_type": true
  }
}
```

**Response**:
```json
{
  "session_id": "excel_abc123",
  "status": "splitting",
  "message": "Task splitting submitted to queue",
  "target_langs": ["PT", "TH", "VN"]
}
```

### 8. excel_get_tasks

Get task splitting results including summary, batch distribution, and task preview.

**Parameters**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123",
  "preview_limit": 10  // Optional, default: 10
}
```

**Response**:
```json
{
  "session_id": "excel_abc123",
  "status": "completed",
  "result": {
    "summary": {
      "total_tasks": 1500,
      "task_breakdown": {
        "normal": 1200,
        "yellow": 200,
        "blue": 100
      },
      "language_distribution": {
        "PT": 500,
        "TH": 500,
        "VN": 500
      },
      "batch_distribution": {
        "PT": 3,
        "TH": 3,
        "VN": 3
      },
      "type_batch_distribution": {
        "normal": 7,
        "yellow": 1,
        "blue": 1
      },
      "total_chars": 75000
    },
    "preview_tasks": [
      {
        "task_id": "task_001",
        "source_text": "Hello World",
        "target_lang": "PT",
        "task_type": "normal",
        "batch_id": "PT_batch_001",
        "row_index": 2,
        "sheet_name": "Sheet1"
      }
    ],
    "total_tasks": 1500
  }
}
```

### 9. excel_get_batches

Get detailed batch information from task splitting.

**Parameters**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123"
}
```

**Response**:
```json
{
  "session_id": "excel_abc123",
  "batches": [
    {
      "batch_id": "PT_batch_001",
      "target_lang": "PT",
      "task_count": 500,
      "char_count": 48523,
      "task_types": {
        "normal": 400,
        "yellow": 70,
        "blue": 30
      }
    }
  ]
}
```

### 10. excel_export_tasks

Export tasks to Excel/JSON/CSV format for download.

**Parameters**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123",
  "format": "excel",          // "excel", "json", or "csv"
  "include_context": true     // Optional, default: true
}
```

**Response**:
```json
{
  "session_id": "excel_abc123",
  "status": "completed",
  "download_url": "http://localhost:9100/downloads/tasks_abc123.xlsx",
  "export_path": "/path/to/tasks_abc123.xlsx",
  "format": "excel"
}
```

## Installation

```bash
cd excel_mcp
pip install -r requirements.txt
```

## Usage

### Standalone Mode

```bash
python server.py
```

### With Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "excel-mcp": {
      "command": "python",
      "args": ["/path/to/excel_mcp/server.py"]
    }
  }
}
```

## Workflows

### Workflow 1: Analysis Only

```bash
# 1. Analyze Excel
excel_analyze(token, file_url) → {session_id: "excel_abc123"}

# 2. Get analysis results
excel_get_status(token, session_id) → {status: "completed", analysis: {...}}

# 3. Get sheets and data
excel_get_sheets(token, session_id)
excel_parse_sheet(token, session_id, sheet_name)
```

### Workflow 2: Analysis + Task Splitting

```bash
# 1. Analyze Excel
excel_analyze(token, file_url) → {session_id: "excel_abc123"}

# 2. Wait for analysis to complete
excel_get_status(token, session_id) → {status: "completed", has_analysis: true}

# 3. Split into translation tasks
excel_split_tasks(token, session_id, target_langs=["PT", "TH", "VN"])
→ {session_id: "excel_abc123", status: "splitting"}

# 4. Get task results
excel_get_tasks(token, session_id)
→ {
    status: "completed",
    result: {
      summary: {total_tasks: 1500, task_breakdown: {...}},
      preview_tasks: [...]
    }
  }

# 5. Get batch details
excel_get_batches(token, session_id)
→ {batches: [{batch_id: "PT_batch_001", task_count: 500, ...}]}

# 6. Export tasks
excel_export_tasks(token, session_id, format="excel")
→ {download_url: "http://...", export_path: "/path/to/tasks.xlsx"}
```

## Configuration

### Environment Variables
- `JWT_SECRET_KEY`: Secret key for JWT validation (default: "dev-secret-key-change-in-production")
- `SESSION_TIMEOUT_HOURS`: Session expiration timeout (default: 8)

### Color Configuration

Edit `config/color_config.yaml` to customize color detection:

```yaml
yellow_colors:
  - name: "Pure Yellow"
    pattern: "FFFF"        # Pattern matching
    hex_values:            # Exact hex matching
      - "FFFFFF00"
    rgb_range:             # RGB range matching
      r: [200, 255]
      g: [200, 255]
      b: [0, 100]

blue_colors:
  - name: "Sky Blue"
    hex_values:
      - "00B0F0"
    rgb_range:
      r: [0, 50]
      g: [150, 200]
      b: [230, 255]
```

## Session Management

- **Storage**: In-memory (no MySQL/Redis dependency)
- **Pattern**: Singleton
- **Expiration**: 8 hours (configurable)
- **Cleanup**: Automatic hourly cleanup
- **Isolation**: Each session is independent

## Color Detection

The analyzer detects three types of colored cells for task classification:

1. **Yellow Cells**: Re-translation tasks
   - Configured via `color_config.yaml`
   - Default: #FFFFFF00 and similar yellow ranges
   - Maps to `TaskType.YELLOW`

2. **Blue Cells**: Shortening tasks
   - Configured via `color_config.yaml`
   - Default: #00B0F0 and similar blue ranges
   - Maps to `TaskType.BLUE`

3. **Other/No Color**: Normal translation tasks
   - Empty target cells without special colors
   - Maps to `TaskType.NORMAL`

**Detection Priority** (in task splitting):
1. Target cell has yellow/blue color → Use that type
2. Source cell has yellow color → Re-translation (yellow)
3. Target cell is empty → Normal translation

## Language Detection

Supports detection of:
- Source Languages: Chinese (CH), English (EN)
- Target Languages: Turkish (TR), Thai (TH), Portuguese (PT), Vietnamese (VN), Indonesian (IND), Spanish (ES)

Detection methods:
1. Column name matching (e.g., "TR", "Turkish", ":tr:")
2. Content pattern matching (Unicode ranges, keyword patterns)

## Error Handling

All errors return structured error responses:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description"
  }
}
```

Common error codes:
- `INVALID_TOKEN`: Token validation failed
- `SESSION_NOT_FOUND`: Session ID not found
- `ANALYSIS_FAILED`: Analysis processing failed
- `MISSING_PARAMETER`: Required parameter missing

## Limitations

- **File Size**: Large files (>50MB) may cause memory issues
- **Session Storage**: In-memory storage is lost on server restart
- **No Persistence**: Results not saved to disk/database
- **Single Instance**: Not designed for horizontal scaling

## Use Cases

1. **Translation Project Management**:
   - Analyze Excel translation files
   - Split into manageable translation tasks
   - Allocate tasks into batches by language
   - Export tasks for translation workflow

2. **Game Localization**:
   - Detect re-translation needs (yellow cells)
   - Identify text shortening requirements (blue cells)
   - Extract context from game data structure

3. **Data Analysis**: Extract and analyze Excel data
4. **Format Conversion**: Convert Excel to JSON/CSV
5. **Document Processing**: Automated Excel document workflows

## Contributing

This is a standalone MCP server. See [MCP_DESIGN_PRINCIPLES.md](../MCP_DESIGN_PRINCIPLES.md) for design guidelines.

## License

MIT License

## Version

v1.0.0
