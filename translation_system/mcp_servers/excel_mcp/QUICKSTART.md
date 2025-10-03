# Excel MCP Server - Quick Start Guide

Get started with Excel MCP Server in 5 minutes.

## Prerequisites

- Python 3.8+
- pip

## Installation

```bash
# Navigate to excel_mcp directory
cd /path/to/excel_mcp

# Install dependencies
pip install -r requirements.txt
```

## Running the Server

### Method 1: Direct Execution

```bash
python server.py
```

The server will start and listen on stdio for MCP protocol messages.

### Method 2: With Claude Desktop

1. Edit your Claude Desktop config file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%/Claude/claude_desktop_config.json`

2. Add the excel-mcp server:

```json
{
  "mcpServers": {
    "excel-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/excel_mcp/server.py"]
    }
  }
}
```

3. Restart Claude Desktop

## Basic Usage Example

### Scenario 1: Analyze Excel from URL

```json
// Call excel_analyze tool
{
  "tool": "excel_analyze",
  "arguments": {
    "token": "Bearer dev-token",
    "file_url": "https://example.com/data.xlsx",
    "options": {
      "detect_language": true,
      "detect_formats": true,
      "analyze_colors": true
    }
  }
}

// Response
{
  "session_id": "excel_abc123",
  "status": "queued",
  "message": "Analysis task submitted to queue",
  "estimated_time": 30
}

// Query status (after a few seconds)
{
  "tool": "excel_get_status",
  "arguments": {
    "token": "Bearer dev-token",
    "session_id": "excel_abc123"
  }
}

// Response (when completed)
{
  "session_id": "excel_abc123",
  "status": "completed",
  "progress": 100,
  "result": {
    "file_info": {...},
    "language_detection": {...},
    "statistics": {...},
    "format_analysis": {...}
  }
}
```

### Scenario 2: Analyze Uploaded File

```json
// Upload file (base64 encoded)
{
  "tool": "excel_analyze",
  "arguments": {
    "token": "Bearer dev-token",
    "file": "UEsDBBQABgAIAAAAIQ...",  // base64-encoded Excel file
    "filename": "mydata.xlsx",
    "options": {
      "detect_language": true
    }
  }
}
```

### Scenario 3: Get Sheet List

```json
{
  "tool": "excel_get_sheets",
  "arguments": {
    "token": "Bearer dev-token",
    "session_id": "excel_abc123"
  }
}

// Response
{
  "session_id": "excel_abc123",
  "sheets": [
    {"name": "Sheet1", "rows": 500, "cols": 8},
    {"name": "Sheet2", "rows": 300, "cols": 6}
  ]
}
```

### Scenario 4: Parse Sheet Data

```json
{
  "tool": "excel_parse_sheet",
  "arguments": {
    "token": "Bearer dev-token",
    "session_id": "excel_abc123",
    "sheet_name": "Sheet1",
    "limit": 10,
    "offset": 0
  }
}

// Response
{
  "session_id": "excel_abc123",
  "sheet_name": "Sheet1",
  "data": [
    {"Column1": "Value1", "Column2": "Value2"},
    {"Column1": "Value3", "Column2": "Value4"}
  ],
  "total_rows": 500,
  "returned_rows": 10,
  "offset": 0
}
```

### Scenario 5: Convert to JSON

```json
{
  "tool": "excel_convert_to_json",
  "arguments": {
    "token": "Bearer dev-token",
    "session_id": "excel_abc123",
    "sheet_name": "Sheet1"
  }
}

// Response
{
  "session_id": "excel_abc123",
  "data": {
    "Sheet1": [
      {"Column1": "Value1", "Column2": "Value2"},
      ...
    ]
  }
}
```

## Testing with Mock Token

For development/testing, the server uses a simple JWT validator with a default secret key.

Generate a test token (Python):

```python
import jwt
from datetime import datetime, timedelta

payload = {
    "user_id": "test_user",
    "tenant_id": "test_tenant",
    "username": "test@example.com",
    "permissions": {
        "excel:analyze": True
    },
    "exp": (datetime.utcnow() + timedelta(days=1)).timestamp()
}

token = jwt.encode(payload, "dev-secret-key-change-in-production", algorithm="HS256")
print(f"Bearer {token}")
```

## Common Workflows

### Workflow 1: Translation Project Analysis

```bash
# 1. Analyze Excel
excel_analyze(token, file_url="https://example.com/translation.xlsx")
# Returns: session_id

# 2. Check status
excel_get_status(token, session_id)
# Wait until status is "completed"

# 3. Review analysis
# Check result.statistics.estimated_tasks
# Check result.language_detection.source_langs and target_langs
# Check result.format_analysis.colored_cells

# 4. Get sheet list
excel_get_sheets(token, session_id)

# 5. Parse specific sheet
excel_parse_sheet(token, session_id, sheet_name="Sheet1", limit=100)
```

### Workflow 2: Data Extraction

```bash
# 1. Analyze Excel
excel_analyze(token, file_url="https://example.com/data.xlsx")

# 2. Wait for completion
excel_get_status(token, session_id)

# 3. Convert to JSON
excel_convert_to_json(token, session_id)

# 4. Or convert to CSV
excel_convert_to_csv(token, session_id, sheet_name="Sheet1")
```

## Troubleshooting

### Server doesn't start

**Check Python version**:
```bash
python --version  # Should be 3.8+
```

**Check dependencies**:
```bash
pip install -r requirements.txt
```

### Token validation fails

**Error**: "Token validation failed"

**Solution**: Use the mock token generator or ensure your token includes required fields:
- `user_id`
- `permissions.excel:analyze`
- `exp` (not expired)

### Session not found

**Error**: "Session not found"

**Cause**: Session expired (8 hours) or server restarted

**Solution**: Re-run `excel_analyze` to create a new session

### Analysis takes too long

**Cause**: Large Excel file or slow network

**Solution**:
- Use smaller files for testing
- If using URL, ensure fast network access
- Check server logs: `/tmp/excel_mcp.log`

## Logs

Server logs are written to:
- File: `/tmp/excel_mcp.log`
- stderr (console)

View logs:
```bash
tail -f /tmp/excel_mcp.log
```

## Next Steps

1. Read [README.md](./README.md) for detailed documentation
2. Check [examples/](./examples/) for more usage examples
3. Review [MCP_SERVERS_DESIGN.md](../MCP_SERVERS_DESIGN.md) for architecture details

## Support

For issues or questions:
- Check logs in `/tmp/excel_mcp.log`
- Review error response `error.code` and `error.message`
- Ensure all required parameters are provided

## Quick Reference

| Tool | Purpose | Required Params |
|------|---------|----------------|
| `excel_analyze` | Submit analysis task | `token`, (`file_url` OR `file`) |
| `excel_get_status` | Query status/results | `token`, `session_id` |
| `excel_get_sheets` | Get sheet list | `token`, `session_id` |
| `excel_parse_sheet` | Parse sheet data | `token`, `session_id`, `sheet_name` |
| `excel_convert_to_json` | Convert to JSON | `token`, `session_id` |
| `excel_convert_to_csv` | Convert to CSV | `token`, `session_id`, `sheet_name` |

## Status Values

- `queued`: Task submitted, waiting to process
- `processing`: Currently analyzing
- `completed`: Analysis finished, results available
- `failed`: Analysis failed, check `error` field
