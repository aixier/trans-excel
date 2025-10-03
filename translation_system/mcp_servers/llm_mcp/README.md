# LLM MCP Server

## Overview
The LLM MCP Server is a translation execution engine that processes translation tasks using various LLM providers (OpenAI, Qwen, Anthropic, DeepSeek).

## Features
- ✅ Multiple LLM provider support
- ✅ Async batch translation processing
- ✅ Real-time progress tracking via SSE
- ✅ Session-based task management
- ✅ Cost tracking and statistics
- ✅ Export results to Excel/JSON/CSV
- ✅ Retry failed tasks
- ✅ Pause/Resume/Stop controls

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Server

**HTTP Mode (for testing):**
```bash
python3 server.py --http --port 8023
```

**MCP Mode (for production):**
```bash
python3 server.py
```

### 3. Access Test Page
Open browser: http://localhost:8023/

## MCP Tools

### Core Tools
1. **llm_translate_tasks** - Upload and start translation
2. **llm_get_status** - Get translation progress
3. **llm_pause_resume** - Pause/Resume translation
4. **llm_stop_translation** - Stop translation
5. **llm_get_results** - Get translation results
6. **llm_export_results** - Export to file
7. **llm_retry_failed** - Retry failed tasks
8. **llm_get_statistics** - Get detailed statistics
9. **llm_list_sessions** - List all sessions
10. **llm_validate_provider** - Validate LLM provider

## Architecture

```
llm_mcp/
├── server.py              # Main server (HTTP + MCP)
├── mcp_tools.py          # Tool definitions
├── mcp_handler.py        # Tool handlers
├── models/
│   └── session_data.py   # Data models
├── services/
│   ├── task_loader.py    # Load tasks from files
│   ├── translation_executor.py  # Execute translations
│   ├── result_exporter.py       # Export results
│   └── llm/
│       ├── base_provider.py     # Base LLM interface
│       ├── openai_provider.py   # OpenAI implementation
│       └── qwen_provider.py     # Qwen implementation
├── utils/
│   ├── session_manager.py       # Session management
│   ├── token_validator.py       # JWT validation
│   └── http_client.py          # HTTP utilities
├── static/
│   └── index.html               # Test UI
└── exports/                     # Exported files

```

## Workflow

1. **Upload Tasks**: Upload Excel file from Excel MCP
2. **Configure**: Select LLM provider and parameters
3. **Execute**: Start translation with concurrent workers
4. **Monitor**: Real-time progress via SSE
5. **Export**: Download translated results

## Environment Variables

```bash
# LLM API Keys
export OPENAI_API_KEY=your_key
export QWEN_API_KEY=your_key

# JWT Secret
export JWT_SECRET=your_secret
```

## Testing

1. Export tasks from Excel MCP
2. Upload to LLM MCP via test page
3. Select provider and start translation
4. Monitor progress
5. Export results

## API Endpoints

- **POST /mcp/tool** - MCP tool execution
- **GET /health** - Health check
- **GET /sse/progress/{session_id}** - Progress SSE stream
- **GET /exports/{filename}** - Download exported files

## Notes

- No WebSocket needed - uses MCP's built-in SSE for progress
- Session-based architecture for scalability
- Supports pause/resume for long-running tasks
- Automatic retry with exponential backoff
- Cost tracking per provider

## Version
v1.0.0 - Initial implementation