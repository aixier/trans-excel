# Translation System API Documentation
## 测试页面API接口文档

本文档记录了 test_pages 中使用的所有后端API接口。

---

## 目录

1. [上传分析 API](#1-上传分析-api)
2. [任务拆分 API](#2-任务拆分-api)
3. [翻译执行 API](#3-翻译执行-api)
4. [下载导出 API](#4-下载导出-api)
5. [WebSocket API](#5-websocket-api)
6. [数据结构说明](#6-数据结构说明)

---

## 1. 上传分析 API

### 1.1 上传Excel文件

**接口**: `POST /api/analyze/upload`

**功能**: 上传Excel文件并进行分析

**请求格式**: `multipart/form-data`

**请求参数**:
- `file` (FormData) - Excel文件 (.xlsx, .xls)
- `game_info` (可选, string) - 游戏信息JSON字符串

**请求示例**:
```javascript
const formData = new FormData();
formData.append('file', fileObject);
formData.append('game_info', '{"game_name": "MyGame", "version": "1.0"}');

const response = await fetch('/api/analyze/upload', {
    method: 'POST',
    body: formData
});
```

**响应示例**:
```json
{
    "session_id": "abc123def456",
    "stage": "analyzed",
    "analysis": {
        "statistics": {
            "sheet_count": 3,
            "total_cells": 1500,
            "estimated_tasks": 450,
            "task_breakdown": {
                "normal_tasks": 300,
                "yellow_tasks": 100,
                "blue_tasks": 50
            }
        }
    }
}
```

**✨ 新增字段说明**:
- `stage` - 会话全局阶段，可能值：`created`, `analyzed`, `split_complete`, `executing`, `completed`

**测试页面**: `1_upload_analyze.html`

---

### 1.2 获取分析状态

**接口**: `GET /api/analyze/status/{sessionId}`

**功能**: 查询上传文件的分析状态

**路径参数**:
- `sessionId` - 会话ID（从上传接口获取）

**请求示例**:
```javascript
const response = await fetch(`/api/analyze/status/${sessionId}`);
const data = await response.json();
```

**响应示例**:
```json
{
    "session_id": "abc123def456",
    "status": "completed",
    "analysis": {
        "statistics": {
            "sheet_count": 3,
            "total_cells": 1500,
            "estimated_tasks": 450,
            "task_breakdown": {
                "normal_tasks": 300,
                "yellow_tasks": 100,
                "blue_tasks": 50
            }
        }
    }
}
```

**测试页面**: `1_upload_analyze.html`

---

## 2. 任务拆分 API

### 2.1 拆分翻译任务

**接口**: `POST /api/tasks/split`

**功能**: 将Excel中的内容拆分为翻译任务

**请求格式**: `application/json`

**请求体**:
```json
{
    "session_id": "abc123def456",
    "source_lang": "EN",
    "target_langs": ["CH", "TR", "TH"],
    "extract_context": true,
    "context_options": {
        "game_info": true,
        "comments": true,
        "neighbors": true,
        "content_analysis": true,
        "sheet_type": true
    }
}
```

**参数说明**:
- `session_id` (必须) - 会话ID
- `source_lang` (可选) - 源语言代码，留空自动检测
- `target_langs` (必须) - 目标语言数组
- `extract_context` (可选, 默认true) - 是否提取上下文
- `context_options` (可选) - 上下文提取选项
  - `game_info` - 游戏信息
  - `comments` - 单元格注释
  - `neighbors` - 相邻单元格
  - `content_analysis` - 内容特征
  - `sheet_type` - 表格类型

**请求示例**:
```javascript
const response = await fetch('/api/tasks/split', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        session_id: sessionId,
        source_lang: "EN",
        target_langs: ["TR"],
        extract_context: true
    })
});
```

**响应示例（启动拆分）**:
```json
{
    "session_id": "abc123def456",
    "status": "processing",
    "stage": "analyzing",
    "progress": 0,
    "message": "开始拆分任务...",
    "ready_for_next_stage": false
}
```

**✨ 新增字段说明**:
- `status` - 拆分状态：`not_started`, `processing`, `saving`, `completed`, `failed`
- `stage` - 内部阶段：`analyzing`, `allocating`, `creating_df`, `saving`, `verifying`, `done`
- `ready_for_next_stage` - ⭐ **关键字段**，为`true`时才能执行翻译

**测试页面**: `2_task_split.html`

---

### 2.2 获取拆分状态

**接口**: `GET /api/tasks/split/status/{sessionId}`

**功能**: 轮询拆分任务进度

**路径参数**:
- `sessionId` - 会话ID

**请求示例**:
```javascript
const response = await fetch(`/api/tasks/split/status/${sessionId}`);
const data = await response.json();
```

**响应示例（分析中）**:
```json
{
    "session_id": "abc123def456",
    "status": "processing",
    "stage": "analyzing",
    "progress": 45,
    "message": "正在处理表格: Sheet1 (2/5)",
    "ready_for_next_stage": false
}
```

**响应示例（保存中 - ✨ 新增状态）**:
```json
{
    "session_id": "abc123def456",
    "status": "saving",
    "stage": "saving",
    "progress": 95,
    "message": "保存任务管理器...",
    "ready_for_next_stage": false
}
```

**响应示例（完成）**:
```json
{
    "session_id": "abc123def456",
    "status": "completed",
    "stage": "done",
    "progress": 100,
    "message": "拆分完成!",
    "ready_for_next_stage": true,
    "metadata": {
        "task_count": 450,
        "batch_count": 23,
        "batch_distribution": {"TR": 23},
        "type_batch_distribution": {
            "normal": 15,
            "yellow": 5,
            "blue": 3
        },
        "statistics": {"total": 450, "by_lang": {"TR": 450}}
    }
}
```

**⚠️ 重要说明**:
1. **saving状态**: 表示正在保存数据，可能持续0-42秒，此时`ready_for_next_stage`为`false`
2. **ready_for_next_stage**: 只有为`true`时才能安全地进入执行阶段
3. **轮询建议**: 在`processing`和`saving`状态时继续轮询，间隔2秒

**测试页面**: `2_task_split.html`

---

### 2.3 查看任务状态

**接口**: `GET /api/tasks/status/{sessionId}`

**功能**: 查看任务管理器状态

**路径参数**:
- `sessionId` - 会话ID

**请求示例**:
```javascript
const response = await fetch(`/api/tasks/status/${sessionId}`);
const data = await response.json();
```

**响应示例（任务就绪）**:
```json
{
    "status": "ready",
    "has_tasks": true,
    "statistics": {
        "total": 450,
        "pending": 450,
        "completed": 0,
        "failed": 0
    },
    "session_id": "abc123def456"
}
```

**响应示例（拆分进行中）**:
```json
{
    "session_id": "abc123def456",
    "status": "splitting_in_progress",
    "message": "任务正在拆分中，请使用 /api/tasks/split/status/{session_id} 查询拆分进度",
    "split_progress": 45,
    "split_status": "processing",
    "split_message": "正在处理表格..."
}
```

**响应示例（保存进行中 - ✨ 新增）**:
```json
{
    "session_id": "abc123def456",
    "status": "saving_in_progress",
    "message": "任务正在保存中，请稍候...",
    "split_progress": 95,
    "split_status": "saving",
    "split_message": "正在保存任务数据..."
}
```

**响应示例（拆分完成，加载中 - ✨ 新增）**:
```json
{
    "session_id": "abc123def456",
    "status": "split_completed_loading",
    "message": "任务拆分已完成，正在加载任务管理器...",
    "split_progress": 100,
    "ready_for_next_stage": true
}
```

**响应示例（拆分失败）**:
```json
{
    "session_id": "abc123def456",
    "status": "split_failed",
    "message": "任务拆分失败: 错误详情...",
    "has_tasks": false
}
```

**可能的状态值**:
- `ready` - 任务就绪，可以开始翻译
- `splitting_in_progress` - 拆分进行中（processing或not_started阶段）
- `saving_in_progress` - ⏳ **保存进行中**（0-42秒，不能执行）
- `split_completed_loading` - 拆分完成，任务管理器加载中
- `split_failed` - 拆分失败

**⚠️ 重要说明**:
1. **saving_in_progress状态**: 表示正在保存任务数据，可能持续0-42秒。此时**不应尝试执行翻译**，否则会出现404错误。
2. **轮询建议**: 在非`ready`状态时，建议每2秒轮询一次，直到状态变为`ready`。
3. **错误处理**: 收到404错误时，说明session不存在或未开始任务拆分。

**测试页面**: `2_task_split.html`

---

### 2.4 获取任务DataFrame

**接口**: `GET /api/tasks/dataframe/{sessionId}`

**功能**: 获取任务详情列表（DataFrame格式）

**路径参数**:
- `sessionId` - 会话ID

**查询参数**:
- `limit` (可选) - 限制返回数量，如 `?limit=10`

**请求示例**:
```javascript
const response = await fetch(`/api/tasks/dataframe/${sessionId}?limit=10`);
const data = await response.json();
```

**响应示例**:
```json
{
    "session_id": "abc123def456",
    "total_tasks": 450,
    "tasks": [
        {
            "task_id": "task_001",
            "batch_id": "batch_TR_normal_001",
            "source_lang": "EN",
            "target_lang": "TR",
            "source_text": "Hello World",
            "status": "pending",
            "char_count": 11
        }
    ]
}
```

**测试页面**: `2_task_split.html`

---

### 2.5 导出任务Excel

**接口**: `GET /api/tasks/export/{sessionId}`

**功能**: 将任务DataFrame导出为Excel文件

**路径参数**:
- `sessionId` - 会话ID

**请求示例**:
```javascript
const response = await fetch(`/api/tasks/export/${sessionId}`);
const blob = await response.blob();

// 下载文件
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = `tasks_${sessionId}.xlsx`;
a.click();
```

**响应**:
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="tasks_excel_{sessionId}_{timestamp}.xlsx"`

**测试页面**: `2_task_split.html`

---

## 3. 翻译执行 API

### 3.1 开始翻译

**接口**: `POST /api/execute/start`

**功能**: 启动翻译任务

**请求格式**: `application/json`

**请求体**:
```json
{
    "session_id": "abc123def456",
    "provider": "qwen",
    "max_workers": 5
}
```

**参数说明**:
- `session_id` (必须) - 会话ID
- `provider` (可选) - LLM提供商（openai, qwen, gpt-5-nano等）
- `max_workers` (可选, 默认5) - 最大并发数 (1-20)

**请求示例**:
```javascript
const response = await fetch('/api/execute/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        session_id: sessionId,
        provider: "qwen",
        max_workers: 5
    })
});
```

**响应示例（成功）**:
```json
{
    "status": "started",
    "message": "翻译任务已启动",
    "session_id": "abc123def456",
    "total_tasks": 450,
    "ready_for_monitoring": true
}
```

**✨ 新增字段说明**:
- `ready_for_monitoring` - 为`true`时可以立即开始监控进度（无需延迟）

**错误响应示例**:

**1. Session未就绪（拆分未完成）**:
```json
{
    "detail": "Session not ready: split status is processing"
}
```
HTTP状态码: 400

**2. Session未就绪（正在保存）**:
```json
{
    "detail": "Session not ready: split status is saving"
}
```
HTTP状态码: 400

**3. Session未就绪（ready标志为false）**:
```json
{
    "detail": "Session not ready: split not verified (ready_for_next_stage=False)"
}
```
HTTP状态码: 400

**4. TaskManager不存在**:
```json
{
    "detail": "Task manager not found. Please split tasks first."
}
```
HTTP状态码: 404

**⚠️ 重要说明**:
1. 执行前会进行4层验证：Session存在、TaskManager存在、拆分完成且就绪、阶段正确
2. 只有`ready_for_next_stage=true`时才能执行翻译
3. 收到400错误时，建议跳转回拆分页面查看状态

**测试页面**: `3_execute_translation.html`

---

### 3.2 获取执行状态

**接口**: `GET /api/execute/status/{sessionId}`

**功能**: 查询翻译执行状态（用于轮询）

**路径参数**:
- `sessionId` - 会话ID

**请求示例**:
```javascript
const response = await fetch(`/api/execute/status/${sessionId}`);
const data = await response.json();
```

**响应示例（正在执行）**:
```json
{
    "status": "running",
    "session_id": "abc123def456",
    "ready_for_monitoring": true,
    "ready_for_download": false,
    "statistics": {
        "total": 450,
        "completed": 120,
        "processing": 5,
        "pending": 325,
        "failed": 0
    },
    "completion_rate": 26.7,
    "updated_at": "2025-10-08T12:34:56"
}
```

**响应示例（初始化中 - ✨ 新增）**:
```json
{
    "status": "initializing",
    "session_id": "abc123def456",
    "message": "执行初始化中，请稍候...",
    "ready_for_monitoring": false,
    "ready_for_download": false
}
```

**响应示例（已完成）**:
```json
{
    "status": "completed",
    "session_id": "abc123def456",
    "message": "翻译已完成",
    "ready_for_monitoring": true,
    "ready_for_download": true,
    "statistics": {
        "total": 450,
        "completed": 450,
        "processing": 0,
        "pending": 0,
        "failed": 0
    },
    "completion_rate": 100.0
}
```

**响应示例（失败）**:
```json
{
    "status": "failed",
    "session_id": "abc123def456",
    "message": "翻译失败: LLM连接超时",
    "error": "LLM连接超时",
    "ready_for_monitoring": false,
    "ready_for_download": false
}
```

**响应示例（空闲 - 未开始执行）**:
```json
{
    "status": "idle",
    "session_id": "abc123def456",
    "message": "No execution started for this session",
    "ready_for_monitoring": false,
    "ready_for_download": false
}
```

**可能的状态值**:
- `initializing` - ⏳ 初始化中（刚启动，尚不可监控）
- `running` - ⚡ 执行中（可监控进度）
- `paused` - ⏸️ 已暂停
- `stopped` - ⏹️ 已停止
- `completed` - ✅ 已完成（可下载结果）
- `failed` - ❌ 失败
- `idle` - ⏸️ 空闲（未开始执行）

**错误响应（Session不存在）**:
```json
{
    "detail": "Session not found"
}
```
HTTP状态码: 404

**错误响应（任务管理器不存在）**:
```json
{
    "detail": "Task manager not found. Please split tasks first before checking execution status."
}
```
HTTP状态码: 404

**⚠️ 重要说明**:
1. **initializing状态**: 执行刚启动时的短暂状态（1-5秒），此时`ready_for_monitoring`为`false`，建议等待变为`running`状态。
2. **ready_for_monitoring**: 为`true`时可以开始监控实时进度。
3. **ready_for_download**: 为`true`时可以下载翻译结果。
4. **轮询建议**: 建议每2秒轮询一次状态，或使用WebSocket实时监控。
5. **自动检测完成**: 当所有任务完成时，API会自动将状态更新为`completed`。

**测试页面**: `3_execute_translation.html`

---

### 3.3 暂停翻译

**接口**: `POST /api/execute/pause/{sessionId}`

**功能**: 暂停正在执行的翻译任务

**路径参数**:
- `sessionId` - 会话ID

**请求示例**:
```javascript
const response = await fetch(`/api/execute/pause/${sessionId}`, {
    method: 'POST'
});
```

**响应示例**:
```json
{
    "status": "paused",
    "message": "翻译已暂停",
    "session_id": "abc123def456"
}
```

**测试页面**: `3_execute_translation.html`

---

### 3.4 恢复翻译

**接口**: `POST /api/execute/resume/{sessionId}`

**功能**: 恢复已暂停的翻译任务

**路径参数**:
- `sessionId` - 会话ID

**请求示例**:
```javascript
const response = await fetch(`/api/execute/resume/${sessionId}`, {
    method: 'POST'
});
```

**响应示例**:
```json
{
    "status": "running",
    "message": "翻译已恢复",
    "session_id": "abc123def456"
}
```

**测试页面**: `3_execute_translation.html`

---

### 3.5 停止翻译

**接口**: `POST /api/execute/stop/{sessionId}`

**功能**: 停止翻译任务

**路径参数**:
- `sessionId` - 会话ID

**请求示例**:
```javascript
const response = await fetch(`/api/execute/stop/${sessionId}`, {
    method: 'POST'
});
```

**响应示例**:
```json
{
    "status": "stopped",
    "message": "翻译已停止",
    "session_id": "abc123def456"
}
```

**测试页面**: `3_execute_translation.html`

---

## 4. 下载导出 API

### 4.1 获取下载信息

**接口**: `GET /api/download/{sessionId}/info`

**功能**: 获取下载信息和执行状态

**路径参数**:
- `sessionId` - 会话ID

**请求示例**:
```javascript
const response = await fetch(`/api/download/${sessionId}/info`);
const data = await response.json();
```

**响应示例（已完成 - 可下载）**:
```json
{
    "session_id": "abc123def456",
    "status": "completed",
    "message": "翻译已完成，可以下载结果",
    "ready_for_download": true,
    "can_download": true,
    "execution_status": {
        "status": "completed",
        "ready_for_download": true,
        "error": null
    },
    "task_statistics": {
        "total": 450,
        "completed": 450,
        "pending": 0,
        "failed": 0
    },
    "export_info": {
        "has_export": true,
        "file_exists": true,
        "exported_file": "/path/to/file.xlsx",
        "filename": "translated_abc123def456.xlsx",
        "file_size": 2458624,
        "sheet_count": 3,
        "export_timestamp": "2025-10-08T12:34:56"
    }
}
```

**响应示例（执行中 - 不可下载 - ✨ 新增）**:
```json
{
    "session_id": "abc123def456",
    "status": "executing",
    "message": "翻译进行中 (120/450)，请等待完成后下载",
    "ready_for_download": false,
    "can_download": false,
    "execution_status": {
        "status": "running",
        "ready_for_download": false,
        "error": null
    },
    "task_statistics": {
        "total": 450,
        "completed": 120,
        "pending": 325,
        "failed": 5
    },
    "export_info": {
        "has_export": false,
        "file_exists": false
    }
}
```

**响应示例（未开始执行 - ✨ 新增）**:
```json
{
    "session_id": "abc123def456",
    "status": "not_started",
    "message": "任务已拆分但尚未执行，请先开始翻译",
    "ready_for_download": false,
    "can_download": false,
    "execution_status": null,
    "task_statistics": {
        "total": 450,
        "completed": 0,
        "pending": 450,
        "failed": 0
    },
    "export_info": {
        "has_export": false,
        "file_exists": false
    }
}
```

**响应示例（无任务 - ✨ 新增）**:
```json
{
    "session_id": "abc123def456",
    "status": "no_tasks",
    "message": "任务尚未拆分，无法下载",
    "ready_for_download": false,
    "can_download": false,
    "execution_status": null,
    "task_statistics": {},
    "export_info": {
        "has_export": false,
        "file_exists": false
    }
}
```

**响应示例（初始化中 - ✨ 新增）**:
```json
{
    "session_id": "abc123def456",
    "status": "initializing",
    "message": "执行初始化中，请稍候...",
    "ready_for_download": false,
    "can_download": false,
    "execution_status": {
        "status": "initializing",
        "ready_for_download": false,
        "error": null
    },
    "task_statistics": {
        "total": 450,
        "completed": 0,
        "pending": 450,
        "failed": 0
    },
    "export_info": {
        "has_export": false,
        "file_exists": false
    }
}
```

**可能的状态值**:
- `no_tasks` - ⚠️ 无任务（尚未拆分）
- `not_started` - ⚠️ 未开始（已拆分但未执行）
- `initializing` - ⏳ 初始化中（执行刚启动）
- `executing` - ⚡ 执行中（翻译进行中）
- `completed` - ✅ 已完成（可下载）
- `failed` - ❌ 失败

**字段说明**:
- `status` - 整体状态（基于execution_progress）
- `message` - 状态描述信息
- `ready_for_download` - 是否准备好下载（来自execution_progress）
- `can_download` - 是否可以下载（ready_for_download或已有导出文件）
- `execution_status` - 执行进度详情（null表示未执行）
- `task_statistics` - 任务统计信息
- `export_info` - 导出文件信息

**⚠️ 重要说明**:
1. **ready_for_download**: 只有执行完成时才为`true`
2. **can_download**: `ready_for_download`或已有导出文件时为`true`
3. **轮询建议**: 在执行中时，建议每2-5秒轮询一次直到状态变为`completed`
4. **第一次查询**: 如果任务刚完成，可能需要等待几秒钟生成导出文件

**测试页面**: `4_download_export.html`

---

### 4.2 获取翻译汇总报告

**接口**: `GET /api/download/{sessionId}/summary`

**功能**: 获取翻译任务的统计汇总

**路径参数**:
- `sessionId` - 会话ID

**请求示例**:
```javascript
const response = await fetch(`/api/download/${sessionId}/summary`);
const data = await response.json();
```

**响应示例**:
```json
{
    "session_id": "abc123def456",
    "statistics": {
        "total_tasks": 450,
        "completed": 445,
        "failed": 5,
        "total_duration": 3600000,
        "total_cost": 2.5436,
        "total_tokens": 125000
    },
    "language_breakdown": {
        "TR": {
            "total": 450,
            "completed": 445,
            "failed": 5
        }
    }
}
```

**测试页面**: `4_download_export.html`

---

### 4.3 下载翻译结果

**接口**: `GET /api/download/{sessionId}`

**功能**: 下载翻译完成的Excel文件

**路径参数**:
- `sessionId` - 会话ID

**请求示例**:
```javascript
const response = await fetch(`/api/download/${sessionId}`);
const blob = await response.blob();

// 从响应头获取文件名
const contentDisposition = response.headers.get('content-disposition');
let filename = 'translated.xlsx';
if (contentDisposition) {
    const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
    if (match && match[1]) {
        filename = match[1].replace(/['"]/g, '');
    }
}

// 创建下载
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = filename;
a.click();
window.URL.revokeObjectURL(url);
```

**响应**:
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="translated_{filename}"`

**测试页面**: `4_download_export.html`

---

### 4.4 获取所有会话

**接口**: `GET /api/sessions`

**功能**: 获取所有活跃会话列表

**请求示例**:
```javascript
const response = await fetch('/api/sessions');
const data = await response.json();
```

**响应示例**:
```json
{
    "sessions": [
        {
            "session_id": "abc123def456",
            "filename": "test1.xlsx",
            "created_at": "2025-01-20T10:30:00Z",
            "status": "completed"
        },
        {
            "session_id": "xyz789ghi012",
            "filename": "test2.xlsx",
            "created_at": "2025-01-20T11:00:00Z",
            "status": "running"
        }
    ]
}
```

**测试页面**: `4_download_export.html`

---

## 5. WebSocket API

### 5.1 实时进度推送

**接口**: `ws://localhost:8013/ws/progress/{sessionId}`

**功能**: 实时接收翻译任务进度更新

**连接示例**:
```javascript
const wsUrl = `ws://localhost:8013/ws/progress/${sessionId}`;
const websocket = new WebSocket(wsUrl);

websocket.onopen = function(event) {
    console.log('WebSocket connected');
};

websocket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === 'progress') {
        // 处理进度更新
        const progressData = data.data;
        console.log('Progress:', progressData);
    } else if (data.type === 'ping') {
        // 响应心跳
        websocket.send(JSON.stringify({ type: 'pong' }));
    } else if (data.type === 'initial_status') {
        // 处理初始状态
        const progressData = data.progress;
        console.log('Initial status:', progressData);
    }
};

websocket.onerror = function(error) {
    console.error('WebSocket error:', error);
};

websocket.onclose = function(event) {
    console.log('WebSocket closed:', event.code, event.reason);
};
```

**消息类型**:

#### 5.1.1 Progress消息（进度更新）
```json
{
    "type": "progress",
    "data": {
        "total": 450,
        "completed": 120,
        "processing": 5,
        "pending": 325,
        "failed": 0,
        "completion_rate": 26.7
    }
}
```

#### 5.1.2 Initial Status消息（初始状态）
```json
{
    "type": "initial_status",
    "progress": {
        "total": 450,
        "completed": 0,
        "processing": 0,
        "pending": 450,
        "failed": 0,
        "completion_rate": 0
    }
}
```

#### 5.1.3 Ping消息（心跳检测）
```json
{
    "type": "ping"
}
```

**客户端响应**:
```json
{
    "type": "pong"
}
```

**使用建议**:
1. WebSocket作为优化手段，HTTP轮询作为后备
2. 先启动HTTP轮询确保进度显示
3. WebSocket连接成功后停止轮询
4. WebSocket失败时自动切回轮询
5. 响应心跳ping以保持连接活跃

**测试页面**: `3_execute_translation.html`

---

## 6. 数据结构说明

### 6.1 Session ID
- 格式: 16位十六进制字符串
- 示例: `"abc123def4567890"`
- 用途: 唯一标识一个翻译会话

### 6.2 语言代码
支持的语言代码：
- `CH` - 中文
- `EN` - 英文
- `TR` - 土耳其语
- `TH` - 泰语
- `PT` - 葡萄牙语
- `VN` - 越南语
- `IND` - 印尼语
- `ES` - 西班牙语

### 6.3 任务类型
- `normal` - 普通翻译任务（空白单元格）
- `yellow` - 黄色重翻译任务（需要重新翻译）
- `blue` - 蓝色缩短任务（需要缩短长度）

### 6.4 状态值（✨ 已更新）

**会话全局阶段（SessionStage）** - 新增:
- `created` - 会话已创建
- `analyzed` - 分析完成，可拆分
- `split_complete` - 拆分完成，可执行
- `executing` - 执行中
- `completed` - 全部完成，可下载
- `failed` - 失败

**拆分状态（SplitStatus）** - 已更新:
- `not_started` - 未开始
- `processing` - 处理中（分析、分配、创建DF）
- `saving` - ✨ **保存中**（0-42秒，ready_for_next_stage=false）
- `completed` - 完成（ready_for_next_stage=true）
- `failed` - 失败

**拆分内部阶段（SplitStage）** - 新增:
- `analyzing` - 分析表格
- `allocating` - 分配批次
- `creating_df` - 创建DataFrame
- `saving` - ✨ **保存数据**
- `verifying` - 验证完整性
- `done` - 完成

**执行状态（ExecutionStatus）** - 已更新:
- `idle` - 空闲
- `initializing` - 初始化中
- `running` - 运行中（ready_for_monitoring=true）
- `paused` - 已暂停
- `stopped` - 已停止
- `completed` - 已完成（ready_for_download=true）
- `failed` - 失败

**任务状态**:
- `pending` - 待处理
- `processing` - 处理中
- `completed` - 已完成
- `failed` - 失败

### 6.5 就绪标志（✨ 新增）

这些布尔标志用于精确控制工作流转换：

**ready_for_next_stage** (SplitProgress):
- 含义: 拆分是否完成且验证通过，可以进入执行阶段
- `false`: 在`processing`、`saving`、`failed`状态时
- `true`: 只有在`completed`状态且验证通过后
- 用途: 执行前必须检查此标志

**ready_for_monitoring** (ExecutionProgress):
- 含义: 执行是否已初始化完成，可以开始监控进度
- `false`: 在`idle`、`initializing`状态时
- `true`: 在`running`状态时
- 用途: 决定是否可以立即开始轮询/WebSocket监控

**ready_for_download** (ExecutionProgress):
- 含义: 执行是否完成，可以下载结果
- `false`: 在非`completed`状态时
- `true`: 在`completed`状态时
- 用途: 决定是否显示下载按钮

---

## 7. 错误处理

### 7.1 常见错误响应

**Session不存在**:
```json
{
    "detail": "Session not found or Excel not loaded"
}
```
HTTP状态码: 404

**任务未就绪**:
```json
{
    "detail": "No tasks found for this session"
}
```
HTTP状态码: 404

**参数错误**:
```json
{
    "detail": "Invalid request parameters"
}
```
HTTP状态码: 400

**服务器错误**:
```json
{
    "detail": "Internal server error",
    "error": "具体错误信息"
}
```
HTTP状态码: 500

### 7.2 错误处理建议

1. **Session管理**:
   - 始终在localStorage中保存session_id
   - 页面加载时恢复session状态

2. **重试机制**:
   - API调用失败时等待2秒后重试
   - 最多重试3次

3. **状态轮询**:
   - 使用2秒间隔轮询
   - 检测到完成/失败状态时停止轮询

4. **WebSocket回退**:
   - WebSocket失败时切回HTTP轮询
   - 不要依赖WebSocket作为唯一进度来源

---

## 8. 完整工作流示例

```javascript
// 1. 上传文件
const formData = new FormData();
formData.append('file', fileObject);
const uploadRes = await fetch('/api/analyze/upload', {
    method: 'POST',
    body: formData
});
const { session_id } = await uploadRes.json();

// 2. 拆分任务
const splitRes = await fetch('/api/tasks/split', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        session_id,
        source_lang: 'EN',
        target_langs: ['TR']
    })
});

// 3. 轮询拆分状态
const pollSplit = setInterval(async () => {
    const statusRes = await fetch(`/api/tasks/split/status/${session_id}`);
    const { status } = await statusRes.json();
    if (status === 'completed') {
        clearInterval(pollSplit);
        // 继续下一步
    }
}, 2000);

// 4. 开始翻译
const execRes = await fetch('/api/execute/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id })
});

// 5. 监控进度（WebSocket + 轮询）
const ws = new WebSocket(`ws://localhost:8013/ws/progress/${session_id}`);
ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === 'progress') {
        console.log('Progress:', data.data.completion_rate);
    }
};

// 6. 下载结果
const downloadRes = await fetch(`/api/download/${session_id}`);
const blob = await downloadRes.blob();
// ... 处理下载
```

---

## 9. 测试页面映射

| 页面文件 | 主要功能 | 使用的API |
|---------|---------|----------|
| `1_upload_analyze.html` | 上传与分析 | `/api/analyze/upload`<br>`/api/analyze/status/{sessionId}` |
| `2_task_split.html` | 任务拆分 | `/api/tasks/split`<br>`/api/tasks/split/status/{sessionId}`<br>`/api/tasks/status/{sessionId}`<br>`/api/tasks/dataframe/{sessionId}`<br>`/api/tasks/export/{sessionId}` |
| `3_execute_translation.html` | 执行翻译 | `/api/execute/start`<br>`/api/execute/status/{sessionId}`<br>`/api/execute/pause/{sessionId}`<br>`/api/execute/resume/{sessionId}`<br>`/api/execute/stop/{sessionId}`<br>`ws://localhost:8013/ws/progress/{sessionId}` |
| `4_download_export.html` | 下载导出 | `/api/download/{sessionId}/info`<br>`/api/download/{sessionId}/summary`<br>`/api/download/{sessionId}`<br>`/api/sessions` |

---

**文档版本**: 1.0
**生成时间**: 2025-01-20
**后端端口**: 8013 (HTTP/WebSocket)
**前端端口**: 8014 (Nginx)
