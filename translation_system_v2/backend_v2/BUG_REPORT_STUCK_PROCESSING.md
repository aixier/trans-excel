# 🐛 Bug Report: 翻译进度卡在 Processing 状态

## 问题描述

翻译任务进度卡在 85.7% (6/7 完成)，有 1 个任务显示为 "processing" 但实际上没有在执行。

## 复现步骤

1. 创建一个翻译 session: `POST /api/tasks/split`
2. 开始翻译执行: `POST /api/execute/start`
3. 等待一段时间
4. 查询状态: `GET /api/monitor/status/{session_id}`

## 实际表现

**Session ID**: `f4d9a3f4-310d-4477-b790-b1ef0e136dda`

```json
{
    "status": "running",
    "progress": {
        "total": 7,
        "completed": 6,
        "failed": 0,
        "processing": 1,  // ⚠️ 显示为 processing
        "pending": 0
    },
    "active_workers": 0,      // ⚠️ 但没有活跃的工作进程
    "current_tasks": []       // ⚠️ 也没有当前任务
}
```

## 期望表现

应该有以下情况之一：
1. 任务正常完成，`completed: 7`
2. 任务失败，`failed: 1`
3. 任务仍在处理，`active_workers > 0` 且 `current_tasks` 不为空

## 影响

- ✅ 用户无法获取翻译结果（`ready_for_download: false`）
- ✅ 无法停止执行（返回 "Session ID does not match"）
- ✅ Session 永久卡在 "running" 状态

## 可能原因

### 1. 工作进程异常退出
- Worker 进程崩溃或异常退出
- 任务状态没有正确更新为 failed

### 2. 状态同步问题
- 任务实际已完成，但状态更新失败
- TaskDataFrame 中的状态与监控状态不一致

### 3. 异常未捕获
- 翻译 API 调用失败但未捕获异常
- 任务卡在 processing 状态无法恢复

## 诊断信息

### 工作池状态
```bash
curl http://localhost:8013/api/pool/monitor/f4d9a3f4-310d-4477-b790-b1ef0e136dda
```
返回: `{"detail": "Not Found"}`

说明工作池已经不存在，但任务状态未更新。

### 停止执行
```bash
curl -X POST http://localhost:8013/api/execute/stop/f4d9a3f4-310d-4477-b790-b1ef0e136dda
```
返回: `{"detail": "Session ID does not match current execution"}`

说明这个 session 不在执行队列中。

## 相关代码位置

需要检查以下文件：

1. `/backend_v2/services/executor/worker_pool.py`
   - Worker 进程的异常处理
   - 任务状态更新逻辑

2. `/backend_v2/services/executor/batch_executor.py`
   - 批次执行的状态管理
   - 完成/失败回调

3. `/backend_v2/api/monitor_api.py`
   - 状态查询逻辑
   - `active_workers` 和 `current_tasks` 的计算

4. `/backend_v2/services/executor/progress_tracker.py`
   - 进度跟踪逻辑
   - 任务状态同步

## 建议修复方案

### 方案1: 添加超时机制
- 检测任务 processing 时间
- 如果超过阈值（如 5 分钟）自动标记为 failed

### 方案2: 加强异常处理
- Worker 进程的 try-except 包裹
- 确保任何异常都能正确更新任务状态

### 方案3: 状态一致性检查
- 定期检查 `processing` 任务
- 如果 `active_workers == 0` 且任务仍为 processing，自动修复

### 方案4: 添加恢复 API
- 提供 API 端点手动修复卡住的 session
- 例如: `POST /api/execute/recover/{session_id}`

## 临时解决方案

目前用户可以：
1. 重新创建新的 session
2. 使用不同的文件重试
3. 等待系统自动清理（如果有清理机制）

## 优先级

**HIGH** - 影响用户体验，导致翻译任务无法完成

## 测试建议

1. 添加单元测试模拟 Worker 崩溃场景
2. 添加集成测试检查长时间运行的任务
3. 添加压力测试验证高并发场景

## 相关 Issue

- [ ] 需要检查是否有其他 session 也卡在类似状态
- [ ] 需要添加监控告警机制
- [ ] 需要完善日志记录（当前日志文件为空）

## 复现测试脚本

```bash
#!/bin/bash
# 文件位置: /tmp/test_translation_stuck.sh

SESSION_ID="f4d9a3f4-310d-4477-b790-b1ef0e136dda"

echo "检查 session 状态:"
curl -s "http://localhost:8013/api/monitor/status/$SESSION_ID" | python3 -m json.tool

echo -e "\n关键指标:"
curl -s "http://localhost:8013/api/monitor/status/$SESSION_ID" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f\"Processing: {d['progress']['processing']}\")
print(f\"Active Workers: {d['active_workers']}\")
print(f\"Current Tasks: {d['current_tasks']}\")
"
```

---

**报告时间**: 2025-10-17
**Backend 版本**: v2.0.0
**Session ID**: f4d9a3f4-310d-4477-b790-b1ef0e136dda
