"""
MCP Tool Definitions for LLM Translation Server
"""

from typing import List, Dict, Any


def get_llm_tools() -> List[Dict[str, Any]]:
    """Return list of available LLM MCP tools."""
    return [
        {
            "name": "llm_translate_tasks",
            "description": "Upload and translate tasks file from Excel MCP export",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Authentication token"
                    },
                    "file": {
                        "type": "string",
                        "description": "Base64 encoded tasks file (Excel/JSON)"
                    },
                    "file_url": {
                        "type": "string",
                        "description": "URL to download tasks file"
                    },
                    "provider": {
                        "type": "string",
                        "enum": ["openai", "qwen", "anthropic", "deepseek"],
                        "description": "LLM provider to use"
                    },
                    "model": {
                        "type": "string",
                        "description": "Specific model name (optional)"
                    },
                    "max_workers": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "default": 5,
                        "description": "Maximum concurrent workers"
                    },
                    "temperature": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 2,
                        "default": 0.3,
                        "description": "Model temperature"
                    }
                },
                "required": ["token", "provider"],
                "oneOf": [
                    {"required": ["file"]},
                    {"required": ["file_url"]}
                ]
            }
        },
        {
            "name": "llm_get_status",
            "description": "Get translation execution status and progress",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Authentication token"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Translation session ID"
                    }
                },
                "required": ["token", "session_id"]
            }
        },
        {
            "name": "llm_pause_resume",
            "description": "Pause or resume translation execution",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Authentication token"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Translation session ID"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["pause", "resume"],
                        "description": "Action to perform"
                    }
                },
                "required": ["token", "session_id", "action"]
            }
        },
        {
            "name": "llm_stop_translation",
            "description": "Stop translation execution",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Authentication token"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Translation session ID"
                    }
                },
                "required": ["token", "session_id"]
            }
        },
        {
            "name": "llm_get_results",
            "description": "Get translation results",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Authentication token"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Translation session ID"
                    },
                    "filter": {
                        "type": "string",
                        "enum": ["all", "completed", "failed", "pending"],
                        "default": "all",
                        "description": "Filter results by status"
                    },
                    "preview_limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10,
                        "description": "Number of results to preview"
                    }
                },
                "required": ["token", "session_id"]
            }
        },
        {
            "name": "llm_export_results",
            "description": "Export translation results to file",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Authentication token"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Translation session ID"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["excel", "json", "csv"],
                        "default": "excel",
                        "description": "Export format"
                    },
                    "merge_source": {
                        "type": "boolean",
                        "default": True,
                        "description": "Merge translations with source file"
                    }
                },
                "required": ["token", "session_id"]
            }
        },
        {
            "name": "llm_retry_failed",
            "description": "Retry failed translation tasks",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Authentication token"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Translation session ID"
                    },
                    "task_ids": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Specific task IDs to retry (optional)"
                    },
                    "max_retries": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "default": 3,
                        "description": "Maximum retry attempts"
                    }
                },
                "required": ["token", "session_id"]
            }
        },
        {
            "name": "llm_get_statistics",
            "description": "Get detailed translation statistics",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Authentication token"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Translation session ID"
                    }
                },
                "required": ["token", "session_id"]
            }
        },
        {
            "name": "llm_list_sessions",
            "description": "List all translation sessions",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Authentication token"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["all", "running", "completed", "failed"],
                        "default": "all",
                        "description": "Filter sessions by status"
                    }
                },
                "required": ["token"]
            }
        },
        {
            "name": "llm_validate_provider",
            "description": "Validate LLM provider configuration and API key",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Authentication token"
                    },
                    "provider": {
                        "type": "string",
                        "enum": ["openai", "qwen", "anthropic", "deepseek"],
                        "description": "LLM provider to validate"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "API key to validate"
                    },
                    "test_translation": {
                        "type": "boolean",
                        "default": True,
                        "description": "Perform test translation"
                    }
                },
                "required": ["token", "provider", "api_key"]
            }
        }
    ]