# Excel翻译系统 - 完整工作流程分析

## 📋 目录
1. [前端四个测试页面流程](#前端四个测试页面流程)
2. [后端API架构](#后端API架构)
3. [Session管理机制](#Session管理机制)
4. [WebSocket实时通信](#WebSocket实时通信)
5. [问题诊断：session_status: not_found](#问题诊断)

---

## 🎯 前端四个测试页面流程

### 第一步：上传分析 (1_upload_analyze.html)

**功能：** 上传Excel文件并进行初步分析

**流程：**
```
1. 用户选择Excel文件
2. POST /api/analyze/upload
   - FormData: file + game_info(可选)
3. 后端响应:
   {
     "session_id": "uuid",
     "analysis": {
       "file_info": {...},
       "language_detection": {...},
       "statistics": {
         "estimated_tasks": N,
         "task_breakdown": {...}
       }
     }
   }
4. 前端自动填充session_id到下一步
```

**后端处理：**
- `analyze_api.py:upload_and_analyze()`
- 创建session: `session_manager.create_session()`
- 存储Excel: `session_manager.set_excel_df(session_id, excel_df)`
- 分析文件: `ExcelAnalyzer.analyze()`
- 存储结果: `session_manager.set_analysis(session_id, analysis)`

---

### 第二步：任务拆分 (2_task_split.html)

**功能：** 配置翻译参数并拆分任务

**流程：**
```
1. 输入session_id
2. 配置:
   - source_lang: 源语言
   - target_langs: 目标语言列表 []
   - extract_context: true/false
   - context_options: {game_info, comments, neighbors...}
3. POST /api/tasks/split
   {
     "session_id": "uuid",
     "config": {...}
   }
4. 响应: {"status": "processing"}
5. 轮询: GET /api/tasks/split/status/{session_id}
   - 每2秒查询一次
   - 返回: {status, progress, message}
6. 完成后获取任务统计
```

**后端处理：**
- `task_api.py:split_tasks()`
- 验证session存在
- 创建TaskDataFrameManager
- 后台异步拆分任务
- 更新进度状态

---

### 第三步：执行翻译 (3_execute_translation.html)

**功能：** 启动翻译并实时监控进度

**流程：**
```
1. 输入session_id
2. POST /api/execute/start
   {
     "session_id": "uuid",
     "max_workers": 8,
     "provider": "qwen-plus"
   }
3. 响应: {"status": "started"}
4. 建立WebSocket连接:
   ws://localhost:8013/ws/progress/{session_id}
5. WebSocket接收实时进度:
   {
     "type": "progress",
     "data": {
       "total": 1000,
       "completed": 250,
       "processing": 8,
       "pending": 742,
       "failed": 0,
       "completion_rate": 25.0
     }
   }
6. 降级方案: 若WebSocket失败，使用HTTP轮询
   GET /api/execute/progress/{session_id}
```

**WebSocket连接关键：**
```javascript
// test_pages/3_execute_translation.html:346
const wsUrl = `ws://localhost:8013/ws/progress/${sessionId}`;
websocket = new WebSocket(wsUrl);

websocket.onopen = () => {
  // 停止HTTP轮询，使用WebSocket实时更新
  clearInterval(statusInterval);
};

websocket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'progress') {
    updateProgressFromWebSocket(data.data);
  }
};

websocket.onerror = () => {
  // 回退到HTTP轮询
  startStatusPolling(sessionId);
};
```

**后端处理：**
- `execute_api.py:start_execution()`
- 创建Worker Pool
- 启动BatchExecutor
- WebSocket广播进度: `connection_manager.broadcast_to_session()`

---

### 第四步：下载导出 (4_download_export.html)

**功能：** 下载翻译完成的Excel文件

**流程：**
```
1. 输入session_id
2. GET /api/export/{session_id}
3. 后端返回Excel文件流
4. 前端触发下载
```

**后端处理：**
- `export_api.py:export_translated_excel()`
- 从session获取TaskDataFrameManager
- 合并翻译结果到原Excel
- 返回文件流

---

## 🏗️ 后端API架构

### 核心模块

```
backend_v2/
├── api/
│   ├── analyze_api.py      # 上传和分析
│   ├── task_api.py          # 任务拆分
│   ├── execute_api.py       # 执行控制
│   ├── export_api.py        # 导出下载
│   ├── websocket_api.py     # WebSocket实时通信
│   └── monitor_api.py       # 监控统计
├── services/
│   ├── excel_loader.py      # Excel加载
│   ├── excel_analyzer.py    # 文件分析
│   ├── task_splitter.py     # 任务拆分
│   ├── executor/
│   │   ├── worker_pool.py   # 并发Worker池
│   │   └── batch_executor.py # 批次执行器
│   └── llm/
│       ├── llm_factory.py   # LLM工厂
│       └── qwen_provider.py # 通义千问
├── models/
│   ├── excel_dataframe.py   # Excel数据模型
│   └── task_dataframe.py    # 任务数据模型
└── utils/
    └── session_manager.py   # Session管理（关键）
```

### API端点总览

| 端点 | 方法 | 功能 | 返回 |
|------|------|------|------|
| `/api/analyze/upload` | POST | 上传Excel并分析 | `{session_id, analysis}` |
| `/api/analyze/status/{session_id}` | GET | 获取分析状态 | `{session_id, analysis}` |
| `/api/tasks/split` | POST | 拆分翻译任务 | `{status: "processing"}` |
| `/api/tasks/split/status/{session_id}` | GET | 查询拆分进度 | `{status, progress, message}` |
| `/api/execute/start` | POST | 启动翻译执行 | `{status: "started"}` |
| `/api/execute/progress/{session_id}` | GET | 获取执行进度 | `{progress, statistics}` |
| `/api/execute/status/global` | GET | 全局执行状态 | `{is_executing, session_id}` |
| `/api/export/{session_id}` | GET | 导出翻译结果 | Excel文件流 |
| `/ws/progress/{session_id}` | WebSocket | 实时进度推送 | `{type, data}` |

---

## 🗄️ Session管理机制

### SessionManager单例模式

```python
# utils/session_manager.py

class SessionData:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.excel_df: Optional[ExcelDataFrame] = None       # Excel原始数据
        self.task_manager: Optional[TaskDataFrameManager] = None  # 任务管理器
        self.game_info: Optional[GameInfo] = None
        self.analysis: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

class SessionManager:
    _instance = None
    _sessions: Dict[str, SessionData] = {}  # 内存存储
    _session_timeout = timedelta(hours=8)   # 8小时超时
```

### Session生命周期

```
1. 创建 (analyze_api.py:59)
   session_id = session_manager.create_session()

2. 存储数据
   session_manager.set_excel_df(session_id, excel_df)
   session_manager.set_analysis(session_id, analysis)
   session_manager.set_task_manager(session_id, task_manager)

3. 读取数据
   session = session_manager.get_session(session_id)
   excel_df = session_manager.get_excel_df(session_id)

4. 超时清理
   自动清理8小时未访问的session
   调用 _cleanup_old_sessions()

5. 手动删除
   session_manager.delete_session(session_id)
```

### 关键方法

```python
def get_session(self, session_id: str) -> Optional[SessionData]:
    """获取session并更新访问时间"""
    if session_id in self._sessions:
        session = self._sessions[session_id]
        session.update_access_time()  # 重要！更新访问时间
        return session
    return None  # ⚠️ 返回None导致WebSocket显示not_found
```

---

## 🔌 WebSocket实时通信

### 连接管理器

```python
# api/websocket_api.py

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_sessions: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id].add(websocket)

        # 发送初始状态
        await self.send_initial_status(websocket, session_id)

    async def send_initial_status(self, websocket: WebSocket, session_id: str):
        progress = progress_tracker.get_progress(session_id)
        session_data = session_manager.get_session(session_id)  # ⚠️ 关键

        if session_data:
            session_status = getattr(session_data, 'status', 'unknown')
        else:
            session_status = 'not_found'  # ⚠️ 这里导致not_found

        await websocket.send_json({
            'type': 'initial_status',
            'session_id': session_id,
            'progress': progress,
            'session_status': session_status
        })
```

### WebSocket路由

```python
@router.websocket("/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    await connection_manager.connect(websocket, session_id)

    try:
        while True:
            data = await websocket.receive_text()
            # 处理ping/pong等
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
```

### 进度广播

```python
# executor/batch_executor.py

async def broadcast_progress(self):
    """后台任务广播进度"""
    while self.is_running:
        progress_data = {
            'type': 'progress',
            'data': {
                'total': stats['total'],
                'completed': stats['completed'],
                'processing': stats['processing'],
                'pending': stats['pending'],
                'failed': stats['failed'],
                'completion_rate': (completed / total * 100)
            }
        }
        await connection_manager.broadcast_to_session(
            self.session_id,
            progress_data
        )
        await asyncio.sleep(1)  # 每秒广播一次
```

---

## 🔍 问题诊断：session_status: not_found

### 问题表现

```json
{
    "type": "initial_status",
    "timestamp": "2025-10-04T06:52:21.121622",
    "session_id": "9a359dd0-ae64-4de8-b29d-9ec11f1cb723",
    "progress": {
        "total": 0,
        "completed": 0,
        "processing": 0,
        "pending": 0,
        "failed": 0,
        "completion_rate": 0,
        "estimated_remaining_seconds": null
    },
    "session_status": "not_found"
}
```

### 根本原因分析

#### 1. Session未创建或已过期

**可能情况：**
- 前端使用的session_id在后端不存在
- Session超过8小时未访问被清理
- 系统重启（内存模式）导致session丢失

**验证方法：**
```bash
# 检查后端日志
docker logs <container_id> 2>&1 | grep "session_id"

# 调用API验证session是否存在
curl http://localhost:8013/api/analyze/status/9a359dd0-ae64-4de8-b29d-9ec11f1cb723
```

#### 2. 前后端session_id不匹配

**问题场景：**
```javascript
// 前端可能使用了错误的session_id
const sessionId = "9a359dd0-ae64-4de8-b29d-9ec11f1cb723";  // 旧的或错误的ID

// 而后端实际创建的是另一个ID
// 后端返回: {"session_id": "new-uuid-xxx"}
```

**检查方法：**
```javascript
// 1. 检查localStorage
console.log(localStorage.getItem('current_session'));

// 2. 检查上传响应
const uploadResponse = await fetch('/api/analyze/upload', {...});
const {session_id} = await uploadResponse.json();
console.log('Backend session_id:', session_id);
```

#### 3. Docker容器重启导致session丢失

**现象：**
```
# Docker日志显示backend重启
2025-10-04 14:51:32.473 INFO supervisord started with pid 1
2025-10-04 14:51:33.477 INFO spawned: 'backend' with pid 8
```

**后果：**
- 所有内存中的session丢失
- SessionManager._sessions = {} 被重置
- 之前的session_id全部失效

**解决方案：**
1. 前端检测session失效，自动重新上传
2. 后端增加session持久化（文件/Redis）
3. 提供session恢复API

#### 4. 进度为0表示任务未开始

```json
"progress": {
    "total": 0,        // ⚠️ 没有任务
    "completed": 0,
    "processing": 0,
    "pending": 0,
    "failed": 0
}
```

**说明：**
- Session存在，但还没有执行拆分任务
- 需要先调用 `/api/tasks/split`
- 拆分完成后才有 total > 0

### 完整诊断步骤

```bash
# 1. 检查session是否存在
curl http://localhost:8013/api/analyze/status/{session_id}

# 2. 检查全局执行状态
curl http://localhost:8013/api/execute/status/global

# 3. 查看所有活跃session
curl http://localhost:8013/api/monitor/sessions

# 4. 测试WebSocket连接
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==" \
  http://localhost:8013/ws/progress/{session_id}
```

### 修复建议

#### 前端修复

```javascript
// 1. 存储session_id到localStorage
function saveSession(sessionId) {
    localStorage.setItem('current_session', sessionId);
    localStorage.setItem('session_timestamp', Date.now());
}

// 2. 页面加载时验证session
async function validateSession(sessionId) {
    try {
        const response = await fetch(`/api/analyze/status/${sessionId}`);
        if (response.status === 404) {
            console.warn('Session not found, redirecting to upload');
            window.location.href = '/1_upload_analyze.html';
            return false;
        }
        return true;
    } catch (error) {
        return false;
    }
}

// 3. WebSocket错误处理
websocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.session_status === 'not_found') {
        alert('会话已失效，请重新上传文件');
        window.location.href = '/1_upload_analyze.html';
    }
};
```

#### 后端修复

```python
# 1. 增加session验证中间件
@router.websocket("/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    # 先验证session存在
    session = session_manager.get_session(session_id)
    if not session:
        await websocket.close(code=1008, reason="Session not found")
        return

    await connection_manager.connect(websocket, session_id)
    # ...

# 2. 添加session活跃度检查
async def check_session_health(session_id: str) -> bool:
    session = session_manager.get_session(session_id)
    if not session:
        return False

    # 检查session是否有必要的数据
    if not session.excel_df:
        return False

    return True

# 3. 记录详细日志
logger.info(f"WebSocket connection attempt for session: {session_id}")
logger.info(f"Active sessions: {list(session_manager._sessions.keys())}")
```

---

## 📊 系统状态流转

```
State Machine:

[created] → 上传分析完成
    ↓
[analyzed] → 任务拆分完成
    ↓
[configured] → 开始执行翻译
    ↓
[executing] → 翻译进行中
    ↓
[completed] → 可以导出
    ↓
[exported] → 工作流结束
```

---

## 🚀 性能优化要点

1. **Session清理策略**
   - 当前：8小时超时自动清理
   - 建议：增加内存占用监控，超过阈值主动清理

2. **WebSocket连接管理**
   - 当前：每个session可以有多个WebSocket连接
   - 建议：限制每个session最多3个连接

3. **进度广播频率**
   - 当前：每秒广播一次
   - 建议：根据任务数量动态调整（大任务降频）

4. **内存使用**
   - 当前：所有数据在内存中
   - 建议：大文件使用磁盘缓存

---

**文档生成时间：** 2025-10-04
**系统版本：** V2 (Memory-Only Mode)
**分析者：** Claude Code
