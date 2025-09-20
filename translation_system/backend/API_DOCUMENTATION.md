# 游戏本地化智能翻译系统 API 文档

## 基础信息
- **基础URL**: `http://localhost:8000`
- **API版本**: 1.0.0
- **文档地址**: `http://localhost:8000/docs` (Swagger UI)
- **备用文档**: `http://localhost:8000/redoc` (ReDoc)
- **服务名称**: Translation System API Gateway
- **支持的语言**: pt(葡萄牙语), th(泰语), ind(印尼语), tw(繁体中文), vn(越南语), es(西班牙语), tr(土耳其语), ja(日语), ko(韩语)
- **支持的地区**: cn-hangzhou, na(北美), sa(南美), eu(欧洲), me(中东), as(亚洲)

## API 端点总览

### 1. 健康检查接口 (Health Check)

#### GET `/api/health/ping`
简单的心跳检查
- **响应**:
```json
{
  "status": "ok",
  "message": "Translation System is running"
}
```

#### GET `/api/health/status`
详细的系统健康状态
- **响应**:
```json
{
  "status": "healthy|unhealthy",
  "timestamp": "2025-09-19T05:18:00.000Z",
  "service": "Translation System",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy|unhealthy",
      "message": "Database connection status"
    },
    "llm_api": {
      "status": "healthy|unhealthy",
      "message": "LLM API configuration status"
    },
    "oss_storage": {
      "status": "healthy|unhealthy",
      "message": "OSS configuration status"
    }
  }
}
```

#### GET `/api/health/ready`
准备状态检查（用于K8s readiness probe）
- **响应**: `200 OK` 或 `503 Service Unavailable`

#### GET `/api/health/live`
存活状态检查（用于K8s liveness probe）
- **响应**: `200 OK`

---

### 2. 翻译任务接口 (Translation)

#### POST `/api/translation/upload`
上传文件并启动翻译任务

- **请求类型**: `multipart/form-data`
- **参数**:
  - `file` (required): Excel文件 (.xlsx, .xls)
  - `target_languages` (optional): 目标语言列表，逗号分隔，支持: pt,th,ind,tw,vn,es,tr,ja,ko。不传则自动检测所有需要的语言
  - `sheet_names` (optional): 要处理的Sheet名称，逗号分隔，不填则处理所有
  - `batch_size` (optional): 批次大小，默认10，最大30行
  - `max_concurrent` (optional): 最大并发数，默认20，限制20
  - `region_code` (optional): 地区代码，默认"cn-hangzhou"
  - `game_background` (optional): 游戏背景信息
  - `auto_detect` (optional): 自动检测需要翻译的sheets，默认true

- **响应**:
```json
{
  "task_id": "uuid-string",
  "status": "uploading",
  "message": "文件上传成功，翻译任务已启动",
  "created_at": "2025-09-20T05:18:00.000Z"
}
```

**任务状态说明**:
- `pending`: 等待处理
- `uploading`: 文件上传中
- `analyzing`: 文件分析中
- `translating`: 翻译中
- `iterating`: 迭代翻译中
- `completed`: 完成
- `failed`: 失败
- `cancelled`: 已取消

#### GET `/api/translation/tasks/{task_id}/status`
获取翻译任务状态

- **参数**:
  - `task_id` (path): 任务ID

- **响应**:
```json
{
  "task_id": "uuid-string",
  "status": "translating",
  "progress": {
    "total_rows": 190,
    "translated_rows": 50,
    "current_iteration": 2,
    "max_iterations": 5,
    "completion_percentage": 26.3,
    "estimated_time_remaining": 120
  },
  "sheet_progress": [
    {
      "name": "Sheet1",
      "total_rows": 100,
      "translated_rows": 30,
      "status": "processing",
      "percentage": 30.0
    }
  ],
  "current_sheet": "Sheet1",
  "total_sheets": 2,
  "completed_sheets": 0,
  "error_message": null,
  "created_at": "2025-09-20T05:18:00.000Z",
  "updated_at": "2025-09-20T05:19:00.000Z",
  "download_url": null
}
```

#### GET `/api/translation/tasks/{task_id}/progress`
获取任务进度详情（高频轮询接口）

- **参数**:
  - `task_id` (path): 任务ID

- **响应**:
```json
{
  "task_id": "uuid-string",
  "status": "translating",
  "progress": {
    "total_rows": 190,
    "translated_rows": 50,
    "current_iteration": 2,
    "max_iterations": 5,
    "completion_percentage": 26.3,
    "estimated_time_remaining": 120
  },
  "sheet_progress": [
    {
      "name": "Sheet1",
      "total_rows": 100,
      "translated_rows": 30,
      "status": "processing",
      "percentage": 30.0
    }
  ],
  "current_sheet": "Sheet1",
  "total_sheets": 2,
  "completed_sheets": 0,
  "statistics": {
    "total_api_calls": 150,
    "total_tokens_used": 45000,
    "total_cost": 1.5,
    "average_response_time": 1.2,
    "success_rate": 0.95
  },
  "last_updated": "2025-09-20T05:19:00.000Z"
}
```

#### GET `/api/translation/tasks`
列出所有翻译任务

- **查询参数**:
  - `status` (optional): 状态筛选 (pending|processing|completed|failed)
  - `page` (optional): 页码，默认1
  - `limit` (optional): 每页数量，默认20

- **响应**:
```json
{
  "tasks": [
    {
      "task_id": "uuid-string",
      "file_name": "test.xlsx",
      "status": "completed",
      "created_at": "2025-09-19T05:18:00.000Z",
      "progress_percentage": 100
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20
}
```

#### DELETE `/api/translation/tasks/{task_id}`
取消翻译任务

- **参数**:
  - `task_id` (path): 任务ID

- **响应**:
```json
{
  "message": "Task cancelled successfully"
}
```

#### POST `/api/translation/analyze`
分析Excel文件结构

- **请求类型**: `multipart/form-data`
- **参数**:
  - `file` (required): Excel文件 (.xlsx, .xls)

- **响应**:
```json
{
  "file_name": "test.xlsx",
  "total_sheets": 2,
  "sheets": [
    {
      "name": "Sheet1",
      "total_rows": 100,
      "total_columns": 5,
      "columns": ["序号", "中文", "EN", "JA", "KO"],
      "language_columns": ["CH", "EN", "JA", "KO"],
      "sample_data": [
        {
          "序号": 1,
          "中文": "你好",
          "EN": "",
          "JA": "",
          "KO": ""
        }
      ]
    }
  ]
}
```

#### GET `/api/translation/tasks/{task_id}/download`
下载翻译结果

- **参数**:
  - `task_id` (path): 任务ID

- **响应**:
  - 成功: Excel文件流 (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)
  - 失败: JSON错误信息

---

### 3. 项目管理接口 (Project)

#### POST `/api/project/create`
创建新项目

- **请求体**:
```json
{
  "name": "项目名称",
  "description": "项目描述",
  "target_languages": ["pt", "th", "ind"],
  "game_background": "游戏背景信息",
  "region_code": "na",
  "user_id": "user-id"
}
```

- **响应**:
```json
{
  "project_id": "uuid-string",
  "name": "项目名称",
  "status": "active",
  "created_at": "2025-09-19T05:18:00.000Z"
}
```

#### GET `/api/project/{project_id}/summary`
获取项目概要

- **参数**:
  - `project_id` (path): 项目ID

- **响应**:
```json
{
  "project_id": "uuid-string",
  "name": "项目名称",
  "description": "项目描述",
  "target_languages": ["pt", "th", "ind"],
  "statistics": {
    "total_files": 10,
    "total_tasks": 25,
    "completed_tasks": 20,
    "total_rows_translated": 5000
  },
  "created_at": "2025-09-19T05:18:00.000Z",
  "updated_at": "2025-09-19T05:19:00.000Z"
}
```

#### POST `/api/project/{project_id}/versions`
创建项目版本

- **参数**:
  - `project_id` (path): 项目ID

- **请求体**:
```json
{
  "version_name": "v1.0.0",
  "description": "版本描述"
}
```

#### GET `/api/project/list`
列出所有项目

- **查询参数**:
  - `user_id` (required): 用户ID
  - `status` (optional): 状态筛选
  - `page` (optional): 页码
  - `limit` (optional): 每页数量

#### DELETE `/api/project/{project_id}`
删除项目

- **参数**:
  - `project_id` (path): 项目ID

---

### 4. 系统信息接口 (System)

#### GET `/`
获取根路径信息

- **响应**:
```json
{
  "service": "Translation System API Gateway",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

#### GET `/api/info`
获取系统详细信息

- **响应**:
```json
{
  "service": "Translation System",
  "version": "1.0.0",
  "environment": "development",
  "supported_languages": ["pt", "th", "ind", "tw", "vn", "es", "tr", "ja", "ko"],
  "supported_regions": ["cn-hangzhou", "na", "sa", "eu", "me", "as"],
  "features": [
    "Excel文件翻译",
    "项目版本管理",
    "批量并发处理",
    "迭代翻译优化",
    "术语管理",
    "区域化本地化",
    "占位符保护"
  ]
}
```

---

## 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 404 | 资源未找到 |
| 500 | 服务器内部错误 |
| 503 | 服务暂时不可用 |

## 错误响应格式

### 标准错误响应
```json
{
  "error": "validation_error",
  "message": "错误详细信息",
  "details": {
    "field": "具体字段错误信息"
  }
}
```

### 验证错误响应
```json
{
  "error": "validation_error",
  "message": "请求参数验证失败",
  "field_errors": [
    {
      "field": "target_languages",
      "message": "目标语言不能为空"
    }
  ]
}
```

### HTTP异常响应
```json
{
  "error": "http_error",
  "message": "详细错误信息",
  "details": {
    "status_code": 400
  }
}
```

## 认证说明

当前版本暂无认证要求，所有接口均可直接访问。

## 使用示例

### 1. 分析文件结构
```bash
curl -X POST http://localhost:8000/api/translation/analyze \
  -F "file=@test.xlsx"
```

### 2. 上传文件并翻译
```bash
curl -X POST http://localhost:8000/api/translation/upload \
  -F "file=@test.xlsx" \
  -F "target_languages=pt,th,ind" \
  -F "sheet_names=Sheet1,Sheet2" \
  -F "batch_size=10" \
  -F "max_concurrent=20" \
  -F "region_code=cn-hangzhou" \
  -F "auto_detect=true"
```

### 3. 查询任务状态
```bash
curl http://localhost:8000/api/translation/tasks/{task_id}/status
```

### 4. 查询任务进度详情
```bash
curl http://localhost:8000/api/translation/tasks/{task_id}/progress
```

### 5. 下载翻译结果
```bash
curl http://localhost:8000/api/translation/tasks/{task_id}/download \
  -o translated_result.xlsx
```

### 6. 取消任务
```bash
curl -X DELETE http://localhost:8000/api/translation/tasks/{task_id}
```

## 注意事项

1. **文件大小限制**: 建议单个Excel文件不超过10MB
2. **并发限制**: 默认最大并发数为20，可配置最大20
3. **连接超时**: API请求超时时间为60秒
4. **翻译语言支持**:
   - pt (葡萄牙语)
   - th (泰语)
   - ind (印尼语)
   - tw (繁体中文)
   - vn (越南语)
   - es (西班牙语)
   - tr (土耳其语)
   - ja (日语)
   - ko (韩语)
5. **地区代码**:
   - cn-hangzhou (中国杭州，默认)
   - na (北美)
   - sa (南美)
   - eu (欧洲)
   - me (中东)
   - as (亚洲)
6. **Sheet处理特性**:
   - 支持多Sheet文件处理
   - 自动检测需要翻译的Sheet
   - 可指定特定Sheet进行翻译
   - 实时Sheet级别进度跟踪
7. **并发控制**:
   - 最大并发数限制：20
   - 批次大小限制：30行
   - 智能批次调度算法