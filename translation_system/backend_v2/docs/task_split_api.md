# 任务拆分 API 说明

## 接口概览

### 1. POST `/api/tasks/split` - 提交拆分任务
**用途**：提交Excel拆分为翻译任务（异步处理）

**请求体**：
```json
{
  "session_id": "uuid",
  "source_lang": "EN",  // 可选，null为自动检测
  "target_langs": ["TR", "TH", "PT"]
}
```

**响应**：
- **小文件（立即完成）**：返回完整统计信息
- **大文件（后台处理）**：
  ```json
  {
    "session_id": "uuid",
    "status": "processing",
    "message": "任务拆分已启动...",
    "status_url": "/api/tasks/split/status/{session_id}"
  }
  ```

---

### 2. GET `/api/tasks/split/status/{session_id}` - 查询拆分进度
**用途**：查询任务拆分的实时进度（大文件专用）

**响应状态**：
- **processing（处理中）**：
  ```json
  {
    "status": "processing",
    "progress": 45,  // 0-100
    "message": "正在处理表格: TEXT (2/5)",
    "total_sheets": 5,
    "processed_sheets": 2
  }
  ```

- **completed（完成）**：
  ```json
  {
    "status": "completed",
    "progress": 100,
    "message": "拆分完成!",
    "task_count": 19842,
    "batch_count": 87,
    "statistics": {...},
    "preview": [...]
  }
  ```

- **failed（失败）**：
  ```json
  {
    "status": "failed",
    "message": "拆分失败: 错误详情"
  }
  ```

---

### 3. GET `/api/tasks/status/{session_id}` - 查询任务统计
**用途**：查询已拆分任务的统计信息（拆分完成后使用）

**响应**：
- **拆分完成**：
  ```json
  {
    "status": "ready",
    "statistics": {
      "total": 19842,
      "pending": 19842,
      "completed": 0,
      "failed": 0,
      "by_language": {...},
      "by_type": {...}
    },
    "has_tasks": true
  }
  ```

- **拆分进行中**：
  ```json
  {
    "status": "splitting_in_progress",
    "message": "任务正在拆分中...",
    "split_progress": 65
  }
  ```

- **拆分失败**：
  ```json
  {
    "status": "split_failed",
    "message": "任务拆分失败: 错误详情",
    "has_tasks": false
  }
  ```

---

## 使用流程

### 大文件拆分流程（推荐）

```javascript
// 1. 提交拆分任务
const splitResponse = await fetch('/api/tasks/split', {
  method: 'POST',
  body: JSON.stringify({
    session_id: 'xxx',
    target_langs: ['TR', 'TH']
  })
});

const splitData = await splitResponse.json();

// 2. 如果返回 processing 状态，开始轮询
if (splitData.status === 'processing') {
  const interval = setInterval(async () => {
    const statusRes = await fetch(`/api/tasks/split/status/${sessionId}`);
    const statusData = await statusRes.json();

    // 更新进度条
    updateProgress(statusData.progress, statusData.message);

    // 完成或失败时停止轮询
    if (statusData.status === 'completed') {
      clearInterval(interval);
      showResults(statusData);
    } else if (statusData.status === 'failed') {
      clearInterval(interval);
      showError(statusData.message);
    }
  }, 1000);  // 每秒轮询一次
}
```

### 小文件拆分流程

```javascript
// 小文件会立即返回完整结果
const response = await fetch('/api/tasks/split', {...});
const data = await response.json();

// 直接显示结果（无需轮询）
if (data.task_count) {
  showResults(data);
}
```

---

## 性能优化说明

### 问题
- **原来**：同步处理，6575行文件需要30-60秒，页面卡死
- **用户体验差**：无法知道进度，以为系统崩溃

### 解决方案
- **异步处理**：立即返回（<100ms），后台处理
- **进度反馈**：实时显示当前处理的表格和进度百分比
- **资源释放**：每处理一个表格后释放控制权（asyncio.sleep）

### 进度阶段
- **0-10%**：初始化和准备
- **10-80%**：逐表处理（按表数量平均分配进度）
- **80-85%**：分配批次（batch allocation）
- **85-90%**：创建DataFrame
- **90-100%**：计算统计信息和完成

---

## 接口对比表

| 接口 | 用途 | 何时使用 | 返回内容 |
|------|------|----------|----------|
| `POST /split` | 提交拆分任务 | 上传Excel后 | 立即响应或processing状态 |
| `GET /split/status/{id}` | 查询拆分进度 | 大文件拆分时轮询 | 进度百分比+当前状态 |
| `GET /status/{id}` | 查询任务统计 | 拆分完成后 | 任务统计信息 |

---

## 注意事项

1. **拆分进度数据是内存存储**：重启服务器会丢失，但已拆分的任务数据在session中保留
2. **轮询频率建议**：1秒一次，避免过于频繁
3. **超时处理**：超长时间无响应可能是后台任务失败，检查服务器日志
4. **并发限制**：同一session不能同时进行多次拆分