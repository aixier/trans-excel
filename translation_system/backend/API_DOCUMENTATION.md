# 游戏本地化智能翻译系统 API 文档

## 基础信息
- **基础URL**: `http://localhost:8101`
- **API版本**: 1.0.0
- **文档地址**: `http://localhost:8101/docs` (Swagger UI)
- **备用文档**: `http://localhost:8101/redoc` (ReDoc)

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
  - `target_languages` (required): 目标语言列表，逗号分隔 (如: "pt,th,ind")
  - `total_rows` (optional): 处理总行数，默认190
  - `batch_size` (optional): 批次大小，默认3
  - `max_concurrent` (optional): 最大并发数，默认10
  - `region_code` (optional): 地区代码，默认"na"
  - `game_background` (optional): 游戏背景信息

- **响应**:
```json
{
  "task_id": "uuid-string",
  "status": "uploading",
  "message": "文件上传成功，翻译任务已启动",
  "created_at": "2025-09-19T05:18:00.000Z"
}
```

#### GET `/api/translation/tasks/{task_id}/status`
获取翻译任务状态

- **参数**:
  - `task_id` (path): 任务ID

- **响应**:
```json
{
  "task_id": "uuid-string",
  "status": "pending|processing|completed|failed",
  "progress": {
    "total_rows": 190,
    "translated_rows": 50,
    "current_iteration": 2,
    "max_iterations": 5,
    "completion_percentage": 26.3,
    "estimated_time_remaining": 120
  },
  "error_message": null,
  "created_at": "2025-09-19T05:18:00.000Z",
  "updated_at": "2025-09-19T05:19:00.000Z",
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
  "current_step": "翻译中",
  "progress_percentage": 26.3,
  "metrics": {
    "api_calls": 150,
    "tokens_used": 45000,
    "estimated_cost": 1.5,
    "success_rate": 0.95
  },
  "last_updated": "2025-09-19T05:19:00.000Z"
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

```json
{
  "detail": "错误详细信息",
  "status_code": 400,
  "error_code": "INVALID_PARAMETER"
}
```

## 认证说明

当前版本暂无认证要求，所有接口均可直接访问。

## 使用示例

### 1. 上传文件并翻译
```bash
curl -X POST http://localhost:8101/api/translation/upload \
  -F "file=@test.xlsx" \
  -F "target_languages=pt,th,ind" \
  -F "region_code=na"
```

### 2. 查询任务状态
```bash
curl http://localhost:8101/api/translation/tasks/{task_id}/status
```

### 3. 下载翻译结果
```bash
curl http://localhost:8101/api/translation/tasks/{task_id}/download \
  -o translated_result.xlsx
```

## 注意事项

1. **文件大小限制**: 建议单个Excel文件不超过10MB
2. **并发限制**: 默认最大并发数为10
3. **连接超时**: API请求超时时间为60秒
4. **翻译语言支持**:
   - pt (葡萄牙语)
   - th (泰语)
   - ind (印尼语)
   - es (西班牙语)
   - fr (法语)
   - de (德语)
5. **地区代码**:
   - na (北美)
   - sa (南美)
   - eu (欧洲)
   - me (中东)
   - as (亚洲)