# LLM MCP API Specification

## API Overview

### Base URLs
- **MCP stdio**: `stdio://llm_mcp`
- **HTTP API**: `http://localhost:8023`
- **WebSocket**: `ws://localhost:8024`

### Authentication
All API calls require a JWT token with appropriate permissions:
- `llm:upload` - Upload task files
- `llm:translate` - Execute translations
- `llm:export` - Export results
- `llm:admin` - Administrative operations

## MCP Tools API

### 1. llm_upload_tasks

#### Description
Upload translation tasks from Excel MCP export or custom format.

#### Request
```json
{
  "tool": "llm_upload_tasks",
  "arguments": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "file": "base64_encoded_file_content",
    "file_url": "https://example.com/tasks.xlsx",
    "format": "excel",
    "validate": true
  }
}
```

#### Response
```json
{
  "session_id": "llm_abc123def456",
  "status": "uploaded",
  "stats": {
    "total_tasks": 500,
    "total_batches": 10,
    "languages": ["EN->TR", "EN->TH", "EN->PT"],
    "task_types": {
      "normal": 300,
      "yellow": 150,
      "blue": 50
    },
    "estimated_tokens": 50000,
    "estimated_cost": 2.50
  },
  "validation": {
    "valid": true,
    "warnings": [],
    "errors": []
  }
}
```

### 2. llm_configure_translation

#### Description
Configure translation parameters and LLM settings.

#### Request
```json
{
  "tool": "llm_configure_translation",
  "arguments": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "session_id": "llm_abc123def456",
    "provider": "openai",
    "model": "gpt-4-turbo",
    "settings": {
      "temperature": 0.3,
      "max_tokens": 2000,
      "top_p": 0.9,
      "frequency_penalty": 0.0,
      "presence_penalty": 0.0
    },
    "execution": {
      "max_workers": 5,
      "max_retries": 3,
      "retry_delay": 5,
      "timeout": 30
    },
    "cost": {
      "budget_limit": 10.00,
      "alert_threshold": 8.00,
      "stop_on_budget": true
    }
  }
}
```

#### Response
```json
{
  "session_id": "llm_abc123def456",
  "status": "configured",
  "configuration": {
    "provider": "openai",
    "model": "gpt-4-turbo",
    "estimated_cost": 2.50,
    "estimated_time": 300,
    "warnings": []
  }
}
```

### 3. llm_start_translation

#### Description
Start or resume translation execution.

#### Request
```json
{
  "tool": "llm_start_translation",
  "arguments": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "session_id": "llm_abc123def456",
    "mode": "all",
    "options": {
      "skip_completed": true,
      "priority_batches": ["batch_001", "batch_002"],
      "test_mode": false,
      "test_count": 5
    }
  }
}
```

#### Response
```json
{
  "session_id": "llm_abc123def456",
  "execution_id": "exec_789xyz",
  "status": "running",
  "message": "Translation started",
  "websocket_url": "ws://localhost:8024/ws/progress/llm_abc123def456"
}
```

### 4. llm_get_progress

#### Description
Get current translation progress and statistics.

#### Request
```json
{
  "tool": "llm_get_progress",
  "arguments": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "session_id": "llm_abc123def456",
    "include_details": true
  }
}
```

#### Response
```json
{
  "session_id": "llm_abc123def456",
  "status": "running",
  "progress": {
    "percentage": 45.5,
    "completed_tasks": 228,
    "total_tasks": 500,
    "completed_batches": 4,
    "total_batches": 10,
    "current_batch": "batch_005",
    "failed_tasks": 3,
    "skipped_tasks": 0
  },
  "performance": {
    "elapsed_time": 120,
    "estimated_remaining": 145,
    "average_time_per_task": 0.53,
    "tasks_per_minute": 114
  },
  "cost": {
    "tokens_used": 22750,
    "current_cost": 1.14,
    "estimated_total_cost": 2.50,
    "budget_remaining": 8.86
  },
  "current_tasks": [
    {
      "task_id": "task_000234",
      "status": "processing",
      "batch_id": "batch_005",
      "started_at": "2025-10-03T10:15:30Z"
    }
  ],
  "errors": [
    {
      "task_id": "task_000105",
      "error": "API rate limit exceeded",
      "retry_count": 2,
      "will_retry": true
    }
  ]
}
```

### 5. llm_pause_translation

#### Description
Pause the running translation execution.

#### Request
```json
{
  "tool": "llm_pause_translation",
  "arguments": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "session_id": "llm_abc123def456",
    "reason": "Manual pause by user"
  }
}
```

#### Response
```json
{
  "session_id": "llm_abc123def456",
  "status": "paused",
  "message": "Translation paused successfully",
  "checkpoint": {
    "completed_tasks": 228,
    "last_batch": "batch_004",
    "last_task": "task_000228",
    "can_resume": true
  }
}
```

### 6. llm_resume_translation

#### Description
Resume a paused translation execution.

#### Request
```json
{
  "tool": "llm_resume_translation",
  "arguments": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "session_id": "llm_abc123def456",
    "from_checkpoint": true
  }
}
```

#### Response
```json
{
  "session_id": "llm_abc123def456",
  "status": "resumed",
  "message": "Translation resumed from checkpoint",
  "resume_point": {
    "batch_id": "batch_005",
    "task_id": "task_000229",
    "remaining_tasks": 272
  }
}
```

### 7. llm_get_results

#### Description
Get translation results with filtering options.

#### Request
```json
{
  "tool": "llm_get_results",
  "arguments": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "session_id": "llm_abc123def456",
    "filter": {
      "status": ["completed", "failed"],
      "batch_ids": ["batch_001", "batch_002"],
      "task_type": ["yellow", "blue"],
      "language": "TR"
    },
    "pagination": {
      "page": 1,
      "page_size": 100
    },
    "include_source": true
  }
}
```

#### Response
```json
{
  "session_id": "llm_abc123def456",
  "results": [
    {
      "task_id": "task_000001",
      "batch_id": "batch_001",
      "status": "completed",
      "source_lang": "EN",
      "source_text": "Hello World",
      "target_lang": "TR",
      "target_text": "Merhaba Dünya",
      "task_type": "normal",
      "tokens_used": 15,
      "cost": 0.0008,
      "completed_at": "2025-10-03T10:12:30Z"
    }
  ],
  "pagination": {
    "total_results": 228,
    "total_pages": 3,
    "current_page": 1,
    "page_size": 100
  },
  "summary": {
    "completed": 225,
    "failed": 3,
    "pending": 272,
    "success_rate": 98.7
  }
}
```

### 8. llm_export_results

#### Description
Export translation results to file.

#### Request
```json
{
  "tool": "llm_export_results",
  "arguments": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "session_id": "llm_abc123def456",
    "format": "excel",
    "options": {
      "merge_with_source": true,
      "include_failed": false,
      "include_metadata": true,
      "group_by_batch": false
    },
    "filename": "translated_results_20251003.xlsx"
  }
}
```

#### Response
```json
{
  "session_id": "llm_abc123def456",
  "status": "exported",
  "file_info": {
    "filename": "translated_results_20251003.xlsx",
    "format": "excel",
    "size": 524288,
    "rows": 500,
    "download_url": "/exports/llm_abc123def456/translated_results_20251003.xlsx",
    "expires_at": "2025-10-04T10:00:00Z"
  }
}
```

### 9. llm_get_statistics

#### Description
Get detailed translation statistics and analytics.

#### Request
```json
{
  "tool": "llm_get_statistics",
  "arguments": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "session_id": "llm_abc123def456"
  }
}
```

#### Response
```json
{
  "session_id": "llm_abc123def456",
  "statistics": {
    "overview": {
      "total_tasks": 500,
      "completed_tasks": 500,
      "failed_tasks": 5,
      "success_rate": 99.0,
      "total_duration": 300,
      "average_time_per_task": 0.6
    },
    "by_language": {
      "TR": {
        "tasks": 200,
        "completed": 198,
        "failed": 2,
        "average_time": 0.5,
        "tokens_used": 20000,
        "cost": 1.00
      },
      "TH": {
        "tasks": 150,
        "completed": 149,
        "failed": 1,
        "average_time": 0.6,
        "tokens_used": 15000,
        "cost": 0.75
      },
      "PT": {
        "tasks": 150,
        "completed": 148,
        "failed": 2,
        "average_time": 0.7,
        "tokens_used": 15000,
        "cost": 0.75
      }
    },
    "by_task_type": {
      "normal": {
        "count": 300,
        "success_rate": 99.3,
        "average_tokens": 100
      },
      "yellow": {
        "count": 150,
        "success_rate": 98.7,
        "average_tokens": 110
      },
      "blue": {
        "count": 50,
        "success_rate": 98.0,
        "average_tokens": 80
      }
    },
    "token_usage": {
      "total_input_tokens": 25000,
      "total_output_tokens": 25000,
      "total_tokens": 50000,
      "average_per_task": 100
    },
    "cost_breakdown": {
      "total_cost": 2.50,
      "input_token_cost": 1.25,
      "output_token_cost": 1.25,
      "average_per_task": 0.005,
      "cost_by_provider": {
        "openai": 2.50
      }
    },
    "performance": {
      "tasks_per_minute": 100,
      "peak_concurrency": 5,
      "average_concurrency": 4.2,
      "api_calls": 510,
      "retry_count": 10,
      "retry_success_rate": 50.0
    },
    "errors": {
      "total": 5,
      "by_type": {
        "rate_limit": 2,
        "api_error": 1,
        "timeout": 1,
        "invalid_response": 1
      }
    }
  }
}
```

### 10. llm_validate_api_key

#### Description
Validate and test LLM provider API key.

#### Request
```json
{
  "tool": "llm_validate_api_key",
  "arguments": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "provider": "openai",
    "api_key": "sk-...",
    "test_translation": true
  }
}
```

#### Response
```json
{
  "valid": true,
  "provider": "openai",
  "details": {
    "organization": "org-abc123",
    "available_models": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
    "rate_limits": {
      "rpm": 10000,
      "tpm": 2000000
    },
    "test_result": {
      "success": true,
      "response_time": 1.2,
      "test_text": "Hello",
      "translation": "你好",
      "tokens_used": 10
    }
  }
}
```

## WebSocket API

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8024/ws/progress/{session_id}');
```

### Message Types

#### Progress Update
```json
{
  "type": "progress",
  "data": {
    "session_id": "llm_abc123def456",
    "percentage": 45.5,
    "completed_tasks": 228,
    "total_tasks": 500,
    "current_batch": "batch_005",
    "current_task": "task_000234",
    "tokens_used": 22750,
    "current_cost": 1.14
  },
  "timestamp": "2025-10-03T10:15:30Z"
}
```

#### Task Complete
```json
{
  "type": "task_complete",
  "data": {
    "task_id": "task_000234",
    "batch_id": "batch_005",
    "status": "success",
    "result": "Translation result...",
    "tokens_used": 105,
    "cost": 0.005
  },
  "timestamp": "2025-10-03T10:15:35Z"
}
```

#### Batch Complete
```json
{
  "type": "batch_complete",
  "data": {
    "batch_id": "batch_005",
    "completed_tasks": 50,
    "failed_tasks": 0,
    "total_tokens": 5250,
    "batch_cost": 0.26,
    "duration": 30
  },
  "timestamp": "2025-10-03T10:16:00Z"
}
```

#### Error
```json
{
  "type": "error",
  "data": {
    "task_id": "task_000235",
    "batch_id": "batch_005",
    "error_type": "rate_limit",
    "message": "Rate limit exceeded",
    "will_retry": true,
    "retry_after": 5
  },
  "timestamp": "2025-10-03T10:15:40Z"
}
```

#### Execution Complete
```json
{
  "type": "execution_complete",
  "data": {
    "session_id": "llm_abc123def456",
    "total_tasks": 500,
    "completed_tasks": 495,
    "failed_tasks": 5,
    "total_duration": 300,
    "total_cost": 2.47,
    "success_rate": 99.0
  },
  "timestamp": "2025-10-03T10:20:00Z"
}
```

## HTTP REST API

### Upload Tasks File
```http
POST /api/upload
Content-Type: multipart/form-data

file: (binary)
format: excel
validate: true
```

### Get Session Info
```http
GET /api/session/{session_id}
Authorization: Bearer {token}
```

### Download Results
```http
GET /api/download/{session_id}/{filename}
Authorization: Bearer {token}
```

### Health Check
```http
GET /health

Response:
{
  "status": "healthy",
  "version": "1.0.0",
  "providers": ["openai", "qwen"],
  "active_sessions": 5,
  "queue_length": 10
}
```

## Error Codes

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limited
- `500` - Internal Server Error
- `503` - Service Unavailable

### Application Error Codes
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  }
}
```

| Code | Description |
|------|-------------|
| `INVALID_TOKEN` | Invalid or expired authentication token |
| `SESSION_NOT_FOUND` | Session ID does not exist |
| `INVALID_FILE_FORMAT` | Uploaded file format is not supported |
| `TASK_VALIDATION_FAILED` | Task validation failed |
| `PROVIDER_NOT_CONFIGURED` | LLM provider not configured |
| `API_KEY_INVALID` | Invalid API key for provider |
| `BUDGET_EXCEEDED` | Translation budget exceeded |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded |
| `TRANSLATION_FAILED` | Translation execution failed |
| `EXPORT_FAILED` | Result export failed |

## Rate Limiting

### Default Limits
- **Upload**: 10 requests per minute
- **Translation**: Based on LLM provider limits
- **Export**: 5 requests per minute
- **Progress**: 60 requests per minute

### Headers
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1696330000
```

## Pagination

### Request
```json
{
  "pagination": {
    "page": 1,
    "page_size": 100,
    "sort_by": "task_id",
    "sort_order": "asc"
  }
}
```

### Response
```json
{
  "data": [...],
  "pagination": {
    "total_items": 500,
    "total_pages": 5,
    "current_page": 1,
    "page_size": 100,
    "has_next": true,
    "has_previous": false
  }
}
```

## Data Formats

### Task Format
```json
{
  "task_id": "task_000001",
  "batch_id": "batch_001",
  "source_lang": "EN",
  "source_text": "Hello World",
  "target_lang": "TR",
  "target_text": "",
  "task_type": "normal",
  "context": {
    "sheet_name": "UI",
    "row_idx": 10,
    "neighbors": {
      "prev": "Welcome",
      "next": "Goodbye"
    }
  },
  "status": "pending",
  "result": null,
  "error": null,
  "tokens_used": null,
  "cost": null,
  "attempts": 0,
  "created_at": "2025-10-03T10:00:00Z",
  "updated_at": "2025-10-03T10:00:00Z"
}
```

### Batch Format
```json
{
  "batch_id": "batch_001",
  "session_id": "llm_abc123def456",
  "target_lang": "TR",
  "task_count": 50,
  "total_chars": 25000,
  "status": "pending",
  "started_at": null,
  "completed_at": null,
  "duration": null,
  "tokens_used": null,
  "cost": null,
  "error_count": 0
}
```

### Configuration Format
```json
{
  "provider": {
    "name": "openai",
    "api_key": "encrypted_key",
    "endpoint": "https://api.openai.com/v1",
    "organization": "org-abc123"
  },
  "model": {
    "name": "gpt-4-turbo",
    "temperature": 0.3,
    "max_tokens": 2000,
    "top_p": 0.9
  },
  "execution": {
    "max_workers": 5,
    "batch_size": 10,
    "timeout": 30,
    "retry_policy": {
      "max_retries": 3,
      "retry_delay": 5,
      "backoff_multiplier": 2
    }
  },
  "prompt": {
    "system_prompt": "You are a professional translator...",
    "few_shot_examples": [],
    "custom_instructions": {}
  }
}
```

---

**Version**: 1.0.0
**Last Updated**: 2025-10-03
**Status**: Draft