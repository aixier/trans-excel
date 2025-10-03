"""MCP tool definitions for excel_mcp."""

from typing import Dict, Any, List
import json

# MCP Tool Definitions
TOOLS = [
    {
        "name": "excel_analyze",
        "description": "Analyze Excel file comprehensively (async). Returns session_id for tracking. Supports both HTTP URL and direct file upload.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "JWT authentication token (with 'Bearer ' prefix)"
                },
                "file_url": {
                    "type": "string",
                    "description": "HTTP URL to download Excel file from (optional if file is provided)"
                },
                "file": {
                    "type": "string",
                    "description": "Base64-encoded file data for direct upload (optional if file_url is provided)"
                },
                "filename": {
                    "type": "string",
                    "description": "Original filename (optional, used with file upload)"
                },
                "options": {
                    "type": "object",
                    "description": "Analysis options",
                    "properties": {
                        "detect_language": {
                            "type": "boolean",
                            "description": "Enable language detection (default: true)"
                        },
                        "detect_formats": {
                            "type": "boolean",
                            "description": "Enable format detection (default: true)"
                        },
                        "analyze_colors": {
                            "type": "boolean",
                            "description": "Enable color analysis (default: true)"
                        }
                    }
                }
            },
            "required": ["token"]
        }
    },
    {
        "name": "excel_get_status",
        "description": "Query analysis status and retrieve results using session_id",
        "inputSchema": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "JWT authentication token"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID returned from excel_analyze"
                }
            },
            "required": ["token", "session_id"]
        }
    },
    {
        "name": "excel_get_sheets",
        "description": "Get list of sheets in the analyzed Excel file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "JWT authentication token"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID from analysis"
                }
            },
            "required": ["token", "session_id"]
        }
    },
    {
        "name": "excel_parse_sheet",
        "description": "Parse and return data from a specific sheet",
        "inputSchema": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "JWT authentication token"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID from analysis"
                },
                "sheet_name": {
                    "type": "string",
                    "description": "Name of the sheet to parse"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of rows to return (optional)"
                },
                "offset": {
                    "type": "integer",
                    "description": "Starting row offset (optional, default: 0)"
                }
            },
            "required": ["token", "session_id", "sheet_name"]
        }
    },
    {
        "name": "excel_convert_to_json",
        "description": "Convert Excel sheet to JSON format",
        "inputSchema": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "JWT authentication token"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID from analysis"
                },
                "sheet_name": {
                    "type": "string",
                    "description": "Name of the sheet to convert (optional, converts all if not specified)"
                }
            },
            "required": ["token", "session_id"]
        }
    },
    {
        "name": "excel_convert_to_csv",
        "description": "Convert Excel sheet to CSV format",
        "inputSchema": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "JWT authentication token"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID from analysis"
                },
                "sheet_name": {
                    "type": "string",
                    "description": "Name of the sheet to convert"
                }
            },
            "required": ["token", "session_id", "sheet_name"]
        }
    },
    {
        "name": "excel_split_tasks",
        "description": "Split Excel into translation tasks based on analysis. Requires prior excel_analyze call. Detects yellow (re-translation), blue (shortening), and normal tasks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "JWT authentication token"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID from excel_analyze"
                },
                "source_lang": {
                    "type": "string",
                    "description": "Source language code (CH/EN, optional - auto-detect if not specified)"
                },
                "target_langs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Target language codes (e.g., ['PT', 'TH', 'VN'])"
                },
                "extract_context": {
                    "type": "boolean",
                    "description": "Extract context information (default: true)"
                },
                "context_options": {
                    "type": "object",
                    "description": "Context extraction options",
                    "properties": {
                        "game_info": {"type": "boolean"},
                        "neighbors": {"type": "boolean"},
                        "comments": {"type": "boolean"},
                        "content_analysis": {"type": "boolean"},
                        "sheet_type": {"type": "boolean"}
                    }
                }
            },
            "required": ["token", "session_id", "target_langs"]
        }
    },
    {
        "name": "excel_get_tasks",
        "description": "Get task splitting results including summary, batch distribution, and task preview",
        "inputSchema": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "JWT authentication token"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID from excel_split_tasks"
                },
                "preview_limit": {
                    "type": "integer",
                    "description": "Number of tasks to preview (default: 10)"
                }
            },
            "required": ["token", "session_id"]
        }
    },
    {
        "name": "excel_get_batches",
        "description": "Get detailed batch information from task splitting",
        "inputSchema": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "JWT authentication token"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID from excel_split_tasks"
                }
            },
            "required": ["token", "session_id"]
        }
    },
    {
        "name": "excel_export_tasks",
        "description": "Export tasks to Excel/JSON/CSV format for download",
        "inputSchema": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "JWT authentication token"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID from excel_split_tasks"
                },
                "format": {
                    "type": "string",
                    "enum": ["excel", "json", "csv"],
                    "description": "Export format (default: excel)"
                },
                "include_context": {
                    "type": "boolean",
                    "description": "Include context information in export (default: true)"
                }
            },
            "required": ["token", "session_id"]
        }
    }
]


def get_tool_list() -> List[Dict[str, Any]]:
    """Get list of all available tools."""
    return TOOLS


def get_tool_by_name(name: str) -> Dict[str, Any]:
    """Get tool definition by name."""
    for tool in TOOLS:
        if tool["name"] == name:
            return tool
    return None
