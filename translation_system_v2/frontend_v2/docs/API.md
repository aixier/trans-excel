# RESTful API 文档

> Translation System V2 - 后端API完整参考
>
> **Base URL**: `http://localhost:8013`
>
> **Version**: 2.0
>
> **Last Updated**: 2025-10-17

---

## 📋 目录

1. [快速开始](#快速开始)
2. [核心API](#核心api)
   - [任务拆分](#1-任务拆分api)
   - [任务执行](#2-任务执行api)
   - [结果下载](#3-结果下载api)
   - [会话管理](#4-会话管理api)
   - [术语表管理](#5-术语表管理api)
3. [WebSocket API](#websocket-api)
4. [数据模型](#数据模型)
5. [错误处理](#错误处理)
6. [使用示例](#使用示例)

---

## 🚀 快速开始

### 典型工作流程

```bash
# 1. 上传文件并拆分任务
POST /api/tasks/split

# 2. 开始翻译执行
POST /api/execute/start

# 3. 监控进度（轮询或WebSocket）
GET /api/execute/status/{session_id}
WS /ws/progress/{session_id}

# 4. 下载结果
GET /api/download/{session_id}
```

### 基础配置

```javascript
const API_CONFIG = {
  baseURL: 'http://localhost:8013',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
};
```

---

## 🔌 核心API

### 1. 任务拆分API

#### 📤 上传并拆分任务

```http
POST /api/tasks/split
```

**请求格式**: `multipart/form-data`

**参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | File | ✅ | Excel文件 (.xlsx) |
| `source_lang` | String | ✅ | 源语言代码 (CH/EN/TH/PT/VN) |
| `target_langs` | String | ✅ | 目标语言列表，逗号分隔 (EN,TH,PT) |
| `rule_set` | String | ✅ | 规则集名称 (translation/caps_only) |
| `parent_session_id` | String | ❌ | 父Session ID（链式调用时使用） |
| `extract_context` | Boolean | ❌ | 是否提取上下文（默认true） |
| `max_chars_per_batch` | Integer | ❌ | 每批最大字符数（默认1000） |

**示例请求** (JavaScript):

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('source_lang', 'CH');
formData.append('target_langs', 'EN,TH');
formData.append('rule_set', 'translation');

const response = await fetch('http://localhost:8013/api/tasks/split', {
  method: 'POST',
  body: formData
});

const result = await response.json();
```

**成功响应** (200):

```json
{
  "status": "success",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "split_complete",
  "total_tasks": 150,
  "statistics": {
    "by_type": {
      "normal": 120,
      "yellow": 25,
      "blue": 5
    },
    "by_sheet": {
      "Sheet1": 100,
      "Sheet2": 50
    },
    "by_target_lang": {
      "EN": 75,
      "TH": 75
    }
  }
}
```

---

#### 📊 查询拆分状态

```http
GET /api/tasks/split/status/{session_id}
```

**路径参数**:
- `session_id`: 会话ID

**成功响应** (200):

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "split_complete",
  "progress": 100,
  "total_tasks": 150,
  "statistics": {
    "by_type": {"normal": 120, "yellow": 25, "blue": 5},
    "by_sheet": {"Sheet1": 100, "Sheet2": 50},
    "by_target_lang": {"EN": 75, "TH": 75}
  }
}
```

---

#### 📥 导出任务表

```http
GET /api/tasks/export/{session_id}?export_type=tasks
```

**查询参数**:

| 参数 | 值 | 说明 |
|------|---|------|
| `export_type` | `tasks` | 导出任务分解表 (TaskDataFrame) |
| `export_type` | `dataframe` | 导出完整数据框架（含color_*和comment_*列） |

**响应**: Excel文件下载

---

### 2. 任务执行API

#### ▶️ 开始执行

```http
POST /api/execute/start
```

**请求体**:

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "processor": "llm_qwen",
  "max_workers": 10,
  "glossary_config": {
    "enabled": true,
    "id": "default"
  }
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `session_id` | String | ✅ | 会话ID |
| `processor` | String | ✅ | 处理器类型 (llm_qwen/llm_openai/uppercase) |
| `max_workers` | Integer | ❌ | 并发工作数（默认10） |
| `glossary_config` | Object | ❌ | 术语表配置 |
| `glossary_config.enabled` | Boolean | ❌ | 是否启用术语表 |
| `glossary_config.id` | String | ❌ | 术语表ID |

**成功响应** (200):

```json
{
  "status": "started",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_batches": 15,
  "total_tasks": 150,
  "workers": 10,
  "message": "Execution started successfully"
}
```

---

#### 📈 查询执行状态

```http
GET /api/execute/status/{session_id}
```

**成功响应** (200):

```json
{
  "status": "executing",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "progress": {
    "total": 150,
    "completed": 90,
    "failed": 3,
    "pending": 57,
    "processing": 0
  },
  "batches": {
    "total": 15,
    "completed": 9,
    "failed": 0,
    "processing": 1,
    "pending": 5
  },
  "completion_rate": 60.0,
  "estimated_remaining_seconds": 180,
  "active_workers": 10,
  "start_time": "2025-10-17T10:30:00",
  "end_time": null
}
```

**状态说明**:

| Status | 说明 |
|--------|------|
| `idle` | 空闲，未开始 |
| `running` | 执行中 |
| `completed` | 已完成 |
| `failed` | 执行失败 |

---

#### ⏸️ 暂停执行

```http
POST /api/execute/pause/{session_id}
```

**成功响应** (200):

```json
{
  "status": "paused",
  "message": "Execution paused successfully"
}
```

---

#### ▶️ 恢复执行

```http
POST /api/execute/resume/{session_id}
```

**成功响应** (200):

```json
{
  "status": "resumed",
  "message": "Execution resumed successfully"
}
```

---

#### ⏹️ 停止执行

```http
POST /api/execute/stop/{session_id}
```

**成功响应** (200):

```json
{
  "status": "stopped",
  "completed_batches": 9,
  "completed_tasks": 90,
  "message": "Execution stopped successfully"
}
```

---

### 3. 结果下载API

#### 📥 下载翻译结果

```http
GET /api/download/{session_id}
```

**前置条件**:
- ✅ `session.stage == "completed"`
- ✅ `output_state != null`

**成功响应** (200):
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="translated.xlsx"`

**错误响应** (400):

```json
{
  "detail": "Cannot download: execution not completed (current stage: executing)"
}
```

---

#### ℹ️ 获取下载信息

```http
GET /api/download/{session_id}/info
```

**成功响应** (200):

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "翻译已完成，可以下载结果",
  "ready_for_download": true,
  "can_download": true,
  "execution_status": {
    "stage": "completed",
    "ready_for_download": true,
    "has_output": true
  },
  "task_statistics": {
    "total": 150,
    "completed": 147,
    "failed": 3,
    "processing": 0,
    "pending": 0
  },
  "export_info": {
    "has_export": true,
    "exported_file": "/tmp/export_550e8400.xlsx",
    "export_timestamp": "2025-10-17T11:00:00",
    "file_exists": true,
    "file_size": 102400
  }
}
```

---

#### 🗑️ 清理导出缓存

```http
DELETE /api/download/{session_id}/files
```

**成功响应** (200):

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "files_removed": 1,
  "errors": [],
  "success": true,
  "message": "Export files cleaned successfully"
}
```

---

### 4. 会话管理API

#### 📋 列出所有会话

```http
GET /api/sessions/list
```

**成功响应** (200):

```json
{
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "stage": "completed",
      "created_at": "2025-10-17T10:00:00",
      "input_source": "file",
      "parent_session_id": null,
      "rules": ["empty", "yellow", "blue"],
      "processor": "llm_qwen",
      "task_count": 150,
      "has_output": true,
      "child_sessions": 1
    }
  ],
  "total": 10
}
```

---

#### 🔍 获取会话详情

```http
GET /api/sessions/detail/{session_id}
```

**成功响应** (200):

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-10-17T10:00:00",
  "last_accessed": "2025-10-17T11:00:00",
  "stage": "completed",
  "input_source": "file",
  "parent_session_id": null,
  "rules": ["empty", "yellow", "blue"],
  "processor": "llm_qwen",
  "task_statistics": {
    "total": 150,
    "by_type": {
      "normal": 120,
      "yellow": 25,
      "blue": 5
    },
    "by_target_lang": {
      "EN": 75,
      "TH": 75
    }
  },
  "execution_statistics": {
    "total_time_seconds": 300,
    "avg_time_per_task": 2.0
  },
  "metadata": {
    "input_file_path": "/tmp/input_550e8400.pkl",
    "task_file_path": "/tmp/tasks_550e8400.parquet",
    "output_file_path": "/tmp/output_550e8400.pkl",
    "output_state_timestamp": "2025-10-17T11:00:00"
  },
  "child_session_ids": ["660f9511-f3ac-52e5-b827-557766551111"]
}
```

---

#### 🗑️ 删除会话

```http
DELETE /api/sessions/{session_id}
```

**成功响应** (200):

```json
{
  "status": "success",
  "message": "Session deleted successfully",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 5. 术语表管理API

#### 📋 列出所有术语表

```http
GET /api/glossaries/list
```

**成功响应** (200):

```json
{
  "glossaries": [
    {
      "id": "default",
      "name": "通用游戏术语",
      "description": "包含常见RPG游戏术语",
      "version": "1.0",
      "term_count": 50,
      "languages": ["EN", "TH", "PT", "VN"],
      "created_at": "2025-10-01T00:00:00",
      "updated_at": "2025-10-15T12:00:00"
    }
  ],
  "count": 1
}
```

---

#### 🔍 获取术语表详情

```http
GET /api/glossaries/{glossary_id}
```

**成功响应** (200):

```json
{
  "id": "default",
  "name": "通用游戏术语",
  "description": "包含常见RPG游戏术语",
  "version": "1.0",
  "languages": ["EN", "TH"],
  "term_count": 50,
  "terms": [
    {
      "id": "term_001",
      "source": "攻击力",
      "category": "属性",
      "priority": 10,
      "translations": {
        "EN": "ATK",
        "TH": "พลังโจมตี"
      },
      "context": "角色属性面板",
      "notes": "常用简写"
    }
  ]
}
```

---

#### 📤 上传术语表

```http
POST /api/glossaries/upload
```

**请求格式**: `multipart/form-data`

**参数**:
- `file`: JSON文件
- `glossary_id`: 术语表ID（可选）

**支持的JSON格式**:

**格式1 - 完整格式**:

```json
{
  "id": "my_glossary",
  "name": "我的术语表",
  "description": "自定义术语",
  "version": "1.0",
  "languages": ["EN", "TH"],
  "terms": [
    {
      "id": "term_001",
      "source": "攻击力",
      "category": "属性",
      "priority": 10,
      "translations": {
        "EN": "ATK",
        "TH": "พลังโจมตี"
      }
    }
  ]
}
```

**格式2 - 简化格式**:

```json
{
  "攻击力": "ATK",
  "生命值": "HP",
  "防御力": "DEF"
}
```

**成功响应** (200):

```json
{
  "status": "success",
  "glossary_id": "my_glossary",
  "term_count": 3,
  "message": "Glossary uploaded successfully"
}
```

---

#### 🗑️ 删除术语表

```http
DELETE /api/glossaries/{glossary_id}
```

**成功响应** (200):

```json
{
  "status": "success",
  "glossary_id": "my_glossary",
  "message": "Glossary deleted successfully"
}
```

---

## 🔌 WebSocket API

### 实时进度推送

```http
WS /ws/progress/{session_id}
```

### 连接示例

```javascript
const ws = new WebSocket(`ws://localhost:8013/ws/progress/${sessionId}`);

ws.onopen = () => {
  console.log('WebSocket connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleWebSocketMessage(data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
};
```

### 消息类型

#### 1. 初始状态

**服务端 → 客户端** (连接时自动发送):

```json
{
  "type": "initial_status",
  "timestamp": "2025-10-17T10:30:00",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "progress": {
    "total": 150,
    "completed": 0,
    "failed": 0,
    "pending": 150
  },
  "session_status": "created"
}
```

---

#### 2. 进度更新

**服务端 → 客户端**:

```json
{
  "type": "progress",
  "timestamp": "2025-10-17T10:31:00",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "total": 150,
    "completed": 45,
    "failed": 2,
    "pending": 103,
    "completion_rate": 30.0,
    "estimated_remaining_seconds": 210
  }
}
```

---

#### 3. 任务更新

**服务端 → 客户端**:

```json
{
  "type": "task_update",
  "timestamp": "2025-10-17T10:31:05",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "task_123",
  "status": "completed",
  "result": "Translated text here"
}
```

---

#### 4. 会话完成

**服务端 → 客户端**:

```json
{
  "type": "session_completed",
  "timestamp": "2025-10-17T10:35:00",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

#### 5. 错误消息

**服务端 → 客户端**:

```json
{
  "type": "error",
  "timestamp": "2025-10-17T10:31:10",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "error_type": "translation_error",
  "message": "Failed to translate task_456"
}
```

---

#### 6. Ping/Pong (心跳)

**客户端 → 服务端**:

```json
{
  "type": "ping"
}
```

**服务端 → 客户端**:

```json
{
  "type": "pong",
  "timestamp": "2025-10-17T10:31:15"
}
```

---

#### 7. 获取当前进度

**客户端 → 服务端**:

```json
{
  "type": "get_progress"
}
```

**服务端 → 客户端**: 返回 `progress` 消息

---

#### 8. 获取任务摘要

**客户端 → 服务端**:

```json
{
  "type": "get_tasks"
}
```

**服务端 → 客户端**:

```json
{
  "type": "task_summary",
  "timestamp": "2025-10-17T10:31:20",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "tasks": {
    "total": 150,
    "by_status": {
      "completed": 45,
      "failed": 2,
      "pending": 103
    }
  }
}
```

---

### 系统监控WebSocket

```http
WS /ws/monitor
```

用于监控所有活跃会话的系统状态。

**服务端推送** (每5秒):

```json
{
  "type": "monitor_update",
  "timestamp": "2025-10-17T10:31:00",
  "active_sessions": 3,
  "total_connections": 5,
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "connections": 2,
      "progress": {
        "total": 150,
        "completed": 45,
        "completion_rate": 30.0
      }
    }
  ]
}
```

---

## 📊 数据模型

### Session (会话)

```typescript
interface Session {
  session_id: string;           // UUID
  stage: SessionStage;          // created | split_complete | executing | completed | failed
  created_at: string;           // ISO 8601
  last_accessed: string;        // ISO 8601
  input_source: string;         // "file" | "parent_session"
  parent_session_id?: string;   // 父会话ID（可选）
  rules: string[];              // 规则列表
  processor?: string;           // 处理器类型
  task_count: number;           // 任务数量
  has_output: boolean;          // 是否有输出
  child_session_ids: string[];  // 子会话ID列表
}
```

### Task (任务)

```typescript
interface Task {
  task_id: string;              // 任务ID
  batch_id: string;             // 批次ID
  sheet_name: string;           // 工作表名称
  row_idx: number;              // 行索引
  col_idx: number;              // 列索引
  source_text: string;          // 源文本
  target_lang: string;          // 目标语言
  task_type: TaskType;          // normal | yellow | blue | caps
  status: TaskStatus;           // pending | processing | completed | failed
  result?: string;              // 翻译结果
  error_message?: string;       // 错误信息
  context?: string;             // 上下文信息
}
```

### TaskType (任务类型)

```typescript
type TaskType =
  | 'normal'    // 普通翻译（空单元格）
  | 'yellow'    // 黄色单元格（强制重译）
  | 'blue'      // 蓝色单元格（自我缩短）
  | 'caps';     // CAPS工作表（大写转换）
```

### TaskStatus (任务状态)

```typescript
type TaskStatus =
  | 'pending'     // 待处理
  | 'processing'  // 处理中
  | 'completed'   // 已完成
  | 'failed';     // 失败
```

### SessionStage (会话阶段)

```typescript
type SessionStage =
  | 'created'         // 已创建
  | 'split_complete'  // 拆分完成
  | 'executing'       // 执行中
  | 'completed'       // 已完成
  | 'failed';         // 失败
```

### Glossary (术语表)

```typescript
interface Glossary {
  id: string;                   // 术语表ID
  name: string;                 // 名称
  description: string;          // 描述
  version: string;              // 版本
  languages: string[];          // 支持的语言列表
  term_count: number;           // 术语数量
  terms: Term[];                // 术语列表
  created_at: string;           // 创建时间
  updated_at: string;           // 更新时间
}
```

### Term (术语)

```typescript
interface Term {
  id: string;                   // 术语ID
  source: string;               // 源术语
  category: string;             // 分类
  priority: number;             // 优先级
  translations: {               // 翻译映射
    [lang: string]: string;
  };
  context?: string;             // 使用场景
  notes?: string;               // 备注
}
```

---

## ❌ 错误处理

### HTTP状态码

| 状态码 | 含义 | 示例场景 |
|--------|------|---------|
| 200 | 成功 | 正常响应 |
| 400 | 请求错误 | 参数缺失、格式错误、状态不匹配 |
| 404 | 资源不存在 | Session不存在、术语表不存在 |
| 500 | 服务器错误 | 内部处理异常 |

### 错误响应格式

```json
{
  "detail": "Error message describing what went wrong"
}
```

### 常见错误示例

#### 1. Session不存在

```json
{
  "detail": "Session not found: 550e8400-e29b-41d4-a716-446655440000"
}
```

#### 2. 状态不匹配

```json
{
  "detail": "Cannot start execution: Session stage must be 'split_complete', current: 'created'"
}
```

#### 3. 参数缺失

```json
{
  "detail": "Missing required parameter: session_id"
}
```

#### 4. 文件格式错误

```json
{
  "detail": "Invalid file format: expected .xlsx, got .csv"
}
```

#### 5. 下载条件不满足

```json
{
  "detail": "Cannot download: execution not completed (current stage: executing)"
}
```

---

## 📚 使用示例

### 场景1: 简单翻译流程

```javascript
// 1. 上传文件并拆分任务
async function uploadAndSplit(file) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_lang', 'CH');
  formData.append('target_langs', 'EN,TH');
  formData.append('rule_set', 'translation');

  const response = await fetch('http://localhost:8013/api/tasks/split', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  return result.session_id;
}

// 2. 开始翻译
async function startTranslation(sessionId) {
  const response = await fetch('http://localhost:8013/api/execute/start', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      session_id: sessionId,
      processor: 'llm_qwen',
      max_workers: 10
    })
  });

  return await response.json();
}

// 3. 轮询进度
async function pollProgress(sessionId) {
  const interval = setInterval(async () => {
    const response = await fetch(
      `http://localhost:8013/api/execute/status/${sessionId}`
    );
    const status = await response.json();

    console.log(`Progress: ${status.completion_rate}%`);

    if (status.status === 'completed') {
      clearInterval(interval);
      await downloadResult(sessionId);
    }
  }, 2000);
}

// 4. 下载结果
async function downloadResult(sessionId) {
  window.location.href =
    `http://localhost:8013/api/download/${sessionId}`;
}

// 完整流程
async function completeWorkflow(file) {
  const sessionId = await uploadAndSplit(file);
  await startTranslation(sessionId);
  await pollProgress(sessionId);
}
```

---

### 场景2: WebSocket实时监控

```javascript
class TranslationMonitor {
  constructor(sessionId) {
    this.sessionId = sessionId;
    this.ws = null;
  }

  connect() {
    this.ws = new WebSocket(
      `ws://localhost:8013/ws/progress/${this.sessionId}`
    );

    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
    };

    // 心跳检测
    this.startHeartbeat();
  }

  handleMessage(data) {
    switch(data.type) {
      case 'initial_status':
        this.updateUI(data.progress);
        break;

      case 'progress':
        this.updateProgress(data.data);
        break;

      case 'session_completed':
        this.onCompleted();
        break;

      case 'error':
        this.showError(data.message);
        break;
    }
  }

  updateProgress(progress) {
    const percent = progress.completion_rate;
    document.getElementById('progressBar').style.width = `${percent}%`;
    document.getElementById('progressText').textContent =
      `${progress.completed} / ${progress.total}`;
  }

  onCompleted() {
    this.ws.close();
    this.downloadResult();
  }

  startHeartbeat() {
    setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({type: 'ping'}));
      }
    }, 30000);
  }

  downloadResult() {
    window.location.href =
      `http://localhost:8013/api/download/${this.sessionId}`;
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// 使用
const monitor = new TranslationMonitor(sessionId);
monitor.connect();
```

---

### 场景3: 链式调用（翻译 + CAPS）

```javascript
async function translationWithCaps(file) {
  // Stage 1: 翻译
  const formData1 = new FormData();
  formData1.append('file', file);
  formData1.append('source_lang', 'CH');
  formData1.append('target_langs', 'EN,TH');
  formData1.append('rule_set', 'translation');

  const split1 = await fetch('http://localhost:8013/api/tasks/split', {
    method: 'POST',
    body: formData1
  });
  const session1 = await split1.json();

  await fetch('http://localhost:8013/api/execute/start', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      session_id: session1.session_id,
      processor: 'llm_qwen'
    })
  });

  // 等待翻译完成
  await waitForCompletion(session1.session_id);

  // Stage 2: CAPS转换
  const formData2 = new FormData();
  formData2.append('parent_session_id', session1.session_id);
  formData2.append('rule_set', 'caps_only');

  const split2 = await fetch('http://localhost:8013/api/tasks/split', {
    method: 'POST',
    body: formData2
  });
  const session2 = await split2.json();

  await fetch('http://localhost:8013/api/execute/start', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      session_id: session2.session_id,
      processor: 'uppercase'
    })
  });

  // 等待完成并下载
  await waitForCompletion(session2.session_id);
  window.location.href =
    `http://localhost:8013/api/download/${session2.session_id}`;
}

async function waitForCompletion(sessionId) {
  return new Promise((resolve) => {
    const interval = setInterval(async () => {
      const response = await fetch(
        `http://localhost:8013/api/execute/status/${sessionId}`
      );
      const status = await response.json();

      if (status.status === 'completed') {
        clearInterval(interval);
        resolve();
      }
    }, 2000);
  });
}
```

---

### 场景4: 使用术语表

```javascript
async function translateWithGlossary(file, glossaryFile) {
  // 1. 上传术语表
  const glossaryFormData = new FormData();
  glossaryFormData.append('file', glossaryFile);
  glossaryFormData.append('glossary_id', 'my_terms');

  await fetch('http://localhost:8013/api/glossaries/upload', {
    method: 'POST',
    body: glossaryFormData
  });

  // 2. 上传并拆分任务
  const fileFormData = new FormData();
  fileFormData.append('file', file);
  fileFormData.append('source_lang', 'CH');
  fileFormData.append('target_langs', 'EN');
  fileFormData.append('rule_set', 'translation');

  const splitResponse = await fetch('http://localhost:8013/api/tasks/split', {
    method: 'POST',
    body: fileFormData
  });
  const session = await splitResponse.json();

  // 3. 开始翻译（启用术语表）
  await fetch('http://localhost:8013/api/execute/start', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      session_id: session.session_id,
      processor: 'llm_qwen',
      glossary_config: {
        enabled: true,
        id: 'my_terms'
      }
    })
  });
}
```

---

## 🔧 开发建议

### 1. 状态轮询间隔

推荐的轮询间隔：
- 拆分状态: **1秒**
- 执行状态: **2秒**
- 下载信息: **3秒**

### 2. WebSocket vs 轮询

**推荐使用WebSocket**:
- ✅ 实时推送，无延迟
- ✅ 减少服务器负载
- ✅ 更好的用户体验

**轮询适用于**:
- 不需要实时更新的场景
- WebSocket不可用的环境
- 后台任务

### 3. 缓存策略

| 数据类型 | 缓存时间 | 更新策略 |
|---------|---------|---------|
| Session列表 | 30秒 | 手动刷新 |
| 术语表列表 | 5分钟 | 修改时清除 |
| 执行状态 | 不缓存 | 实时查询 |
| 下载信息 | 不缓存 | 实时查询 |

### 4. 错误处理

```javascript
async function apiCall(url, options) {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    // 显示用户友好的错误提示
    showErrorToast(error.message);
    throw error;
  }
}
```

### 5. 超时处理

```javascript
async function fetchWithTimeout(url, options = {}, timeout = 30000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    if (error.name === 'AbortError') {
      throw new Error('Request timeout');
    }
    throw error;
  }
}
```

---

## 📝 附录

### 规则集说明

#### translation (翻译规则集)

启用规则: `['empty', 'yellow', 'blue']`

任务类型:
- `normal`: 空单元格翻译
- `yellow`: 黄色单元格强制重译
- `blue`: 蓝色单元格自我缩短

#### caps_only (大写转换规则集)

启用规则: `['caps']`

任务类型:
- `caps`: CAPS工作表的大写转换

### 处理器类型

| Processor | 功能 | 备注 |
|-----------|------|------|
| `llm_qwen` | 通义千问翻译 | 需要API密钥 |
| `llm_openai` | OpenAI翻译 | 需要API密钥 |
| `uppercase` | 大写转换 | 仅处理ASCII字符 |

### 语言代码

| 代码 | 语言 |
|------|------|
| `CH` | 中文 |
| `EN` | 英文 |
| `TH` | 泰文 |
| `PT` | 葡萄牙文 |
| `VN` | 越南文 |
| `JP` | 日文 |

---

**文档版本**: v2.0
**最后更新**: 2025-10-17
**维护者**: Backend Team

如有问题或建议，请联系后端开发团队或提交Issue。
