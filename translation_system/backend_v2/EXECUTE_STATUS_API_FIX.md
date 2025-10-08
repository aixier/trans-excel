# Execute Status API 修复总结

**问题**: 执行状态查询API未正确处理各种执行阶段的状态
**时间**: 2025-10-08
**影响**: 类似于任务拆分状态API的问题，用户在执行初始化或完成后查询状态可能收到不准确的信息

---

## 问题分析

### 原始逻辑问题

`GET /api/execute/status/{session_id}` 的原始逻辑：

```python
# 1. 检查是否正在执行
if worker_pool.current_session_id == session_id:
    return worker_pool.get_status()

# 2. 检查 task_manager 是否存在
if not session_manager.get_task_manager(session_id):
    raise HTTPException(404, "Session not found")

# 3. 返回 idle
return {'status': 'idle', ...}
```

### 问题场景

1. **初始化阶段**: 执行刚启动，worker_pool可能还未设置current_session_id → 错误返回idle
2. **完成后**: 执行完成，worker_pool.current_session_id已清空 → 无法获取历史状态
3. **失败时**: 执行失败，无法获取失败原因
4. **未使用execution_progress**: 忽略了Session中的execution_progress状态模块

---

## 修复方案

### 1. 后端API修复 (`backend_v2/api/execute_api.py`)

**新逻辑流程**:

```python
# 1. 首先检查 Session 是否存在
session = session_manager.get_session(session_id)
if not session:
    raise HTTPException(404, "Session not found")

# 2. 检查是否正在执行（实时状态优先）
if worker_pool.current_session_id == session_id:
    worker_status = worker_pool.get_status()
    # 合并 execution_progress 状态
    if session.execution_progress:
        return {**exec_progress.to_dict(), **worker_status}
    return worker_status

# 3. 不在执行中 - 检查 execution_progress（历史状态）
if session.execution_progress:
    exec_progress = session.execution_progress

    # 根据不同的执行状态返回相应信息
    if exec_progress.status == ExecutionStatus.INITIALIZING:
        return {..., 'message': '执行初始化中，请稍候...'}

    elif exec_progress.status == ExecutionStatus.RUNNING:
        # 可能已完成或已停止，检查任务统计
        task_manager = session.task_manager
        if task_manager:
            stats = task_manager.get_statistics()
            if stats['completed'] >= stats['total']:
                # 自动标记为完成
                exec_progress.mark_completed()
                session.session_status.update_stage(SessionStage.COMPLETED)
        return {...}

    elif exec_progress.status == ExecutionStatus.COMPLETED:
        return {..., 'message': '翻译已完成'}

    elif exec_progress.status == ExecutionStatus.FAILED:
        return {..., 'message': f'翻译失败: {exec_progress.error}'}

# 4. 无 execution_progress - 检查是否有 task_manager
if not session.task_manager:
    raise HTTPException(404, "Task manager not found...")

# 5. 有任务但从未执行
return {'status': 'idle', 'message': 'No execution started...'}
```

### 2. 关键改进点

#### ✅ 使用 execution_progress 状态模块
- 从Session对象获取execution_progress
- 返回包含 `ready_for_monitoring` 和 `ready_for_download` 标志
- 保留历史执行状态

#### ✅ 自动检测完成
```python
# 当任务统计显示全部完成时，自动更新状态
if stats['completed'] >= stats['total']:
    exec_progress.mark_completed()
    session.session_status.update_stage(SessionStage.COMPLETED)
```

#### ✅ 区分不同的执行状态
- `initializing` - 初始化中（1-5秒）
- `running` - 正在执行
- `completed` - 已完成
- `failed` - 失败
- `idle` - 未开始

#### ✅ 友好的错误消息
```python
# 不是简单的404，而是提供具体指导
raise HTTPException(404,
    "Task manager not found. Please split tasks first before checking execution status.")
```

### 3. 前端HTML更新 (`3_execute_translation.html`)

**改进 getStatus() 函数**:

```javascript
async function getStatus() {
    const response = await fetch(`/api/execute/status/${sessionId}`);
    const data = await response.json();

    if (response.ok) {
        // 根据状态显示不同的UI
        if (status === 'initializing') {
            statusMsg = '⏳ 初始化中\n执行初始化中，请稍候...';
        } else if (status === 'running') {
            statusMsg = '⚡ 执行中\n';
            if (data.ready_for_monitoring) {
                statusMsg += '✅ 可以监控进度';
            }
        } else if (status === 'completed') {
            statusMsg = '✅ 已完成\n';
            if (data.ready_for_download) {
                statusMsg += '✅ 可以下载结果';
            }
        } else if (status === 'failed') {
            statusMsg = '❌ 失败\n错误: ' + data.error;
        } else if (status === 'idle') {
            statusMsg = '⏸️ 空闲\n' + data.message;
        }
    } else {
        // 友好的错误处理
        if (data.detail.includes('Session not found')) {
            errorMsg = '❌ Session 不存在\n提示: 请检查 Session ID';
        } else if (data.detail.includes('Task manager not found')) {
            errorMsg = '❌ 任务管理器未找到\n提示: 请先执行任务拆分';
        }
    }
}
```

### 4. API文档更新

更新了 `API_DOCUMENTATION.md` 第3.2节：
- 添加了所有可能的状态响应示例
- 详细说明了每种状态的含义
- 添加了错误响应示例和处理建议
- 说明了 `ready_for_monitoring` 和 `ready_for_download` 标志

---

## 状态流转图

```
用户查询执行状态
    ↓
┌────────────────────────┐
│ Session 存在?          │
└──┬─────────────────────┘
   │ No → 404 "Session not found"
   │
   │ Yes
   ↓
┌────────────────────────┐
│ 正在执行?              │
│ (worker_pool)          │
└──┬─────────────────────┘
   │
   │ Yes → 返回实时状态 + execution_progress
   │
   │ No
   ↓
┌────────────────────────┐
│ execution_progress     │
│ 存在?                  │
└──┬─────────────────────┘
   │
   │ Yes
   │  ↓
   │  ┌─────────────┬─────────────┬─────────────┬─────────────┐
   │  │ initializing│   running   │  completed  │   failed    │
   │  ├─────────────┼─────────────┼─────────────┼─────────────┤
   │  │ 初始化中    │  检查是否   │  翻译完成   │  显示错误   │
   │  │             │  实际完成   │             │             │
   │  └─────────────┴─────────────┴─────────────┴─────────────┘
   │
   │ No
   ↓
┌────────────────────────┐
│ task_manager 存在?     │
└──┬─────────────────────┘
   │
   │ No → 404 "Task manager not found..."
   │
   │ Yes → 返回 idle (未开始执行)
```

---

## 对比示例

### Before (修复前)

```bash
# 初始化阶段查询（执行刚启动1秒后）
GET /api/execute/status/{session_id}
→ 200 {"status": "idle", "message": "No active execution..."}
# ❌ 错误：实际上正在初始化
```

```bash
# 完成后查询
GET /api/execute/status/{session_id}
→ 200 {"status": "idle", "message": "No active execution..."}
# ❌ 错误：应该显示已完成
```

### After (修复后)

```bash
# 初始化阶段查询
GET /api/execute/status/{session_id}
→ 200 {
    "status": "initializing",
    "message": "执行初始化中，请稍候...",
    "ready_for_monitoring": false
}
# ✅ 正确：显示初始化状态
```

```bash
# 完成后查询
GET /api/execute/status/{session_id}
→ 200 {
    "status": "completed",
    "message": "翻译已完成",
    "ready_for_download": true,
    "statistics": {"total": 100, "completed": 100, ...}
}
# ✅ 正确：显示完成状态和统计
```

---

## 响应字段说明

### 核心字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 执行状态（initializing/running/completed/failed/idle） |
| `session_id` | string | 会话ID |
| `message` | string | 状态描述信息 |
| `ready_for_monitoring` | boolean | 是否可以监控进度 |
| `ready_for_download` | boolean | 是否可以下载结果 |
| `statistics` | object | 任务统计（total/completed/pending/failed） |
| `completion_rate` | number | 完成百分比（0-100） |
| `error` | string | 错误信息（仅在failed时） |

### 状态与标志对应关系

| 状态 | ready_for_monitoring | ready_for_download |
|------|----------------------|---------------------|
| initializing | ❌ false | ❌ false |
| running | ✅ true | ❌ false |
| completed | ✅ true | ✅ true |
| failed | ❌ false | ❌ false |
| idle | ❌ false | ❌ false |

---

## 相关文件

### 修改的文件
1. `backend_v2/api/execute_api.py` - 执行状态查询API逻辑
2. `frontend_v2/test_pages/3_execute_translation.html` - 前端状态显示
3. `frontend_v2/test_pages/API_DOCUMENTATION.md` - API文档更新

### 相关的状态模块
- `backend_v2/services/execution_state.py` - ExecutionProgress类
- `backend_v2/models/session_state.py` - SessionStage枚举

---

## 测试建议

### 测试场景1: 初始化阶段查询
```bash
# 1. 启动执行
POST /api/execute/start

# 2. 立即查询（0-5秒内）
GET /api/execute/status/{session_id}

# 预期: status = "initializing", ready_for_monitoring = false
```

### 测试场景2: 执行中查询
```bash
# 1. 等待5秒后查询
GET /api/execute/status/{session_id}

# 预期: status = "running", ready_for_monitoring = true
```

### 测试场景3: 完成后查询
```bash
# 1. 等待所有任务完成
# 2. 查询状态
GET /api/execute/status/{session_id}

# 预期: status = "completed", ready_for_download = true
```

### 测试场景4: 未执行查询
```bash
# 1. 只拆分任务，不执行
# 2. 查询执行状态
GET /api/execute/status/{session_id}

# 预期: status = "idle", message = "No execution started..."
```

---

## 总结

**问题**: 执行状态查询未使用execution_progress，无法提供准确的历史状态
**原因**:
- 只依赖worker_pool的实时状态
- 未检查Session中的execution_progress模块
- 缺少对不同执行阶段的区分

**修复**:
- ✅ 使用execution_progress保存和查询执行状态
- ✅ 区分 initializing/running/completed/failed/idle 状态
- ✅ 提供 ready_for_monitoring 和 ready_for_download 标志
- ✅ 自动检测任务完成并更新状态
- ✅ 友好的错误消息和状态描述
- ✅ 更新前端UI和API文档

**用户体验改进**:
- 用户可以准确了解执行的任何阶段状态
- 清楚知道何时可以监控进度、何时可以下载结果
- 收到友好的错误提示而非简单的404
