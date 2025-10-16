# 低优先级文件修复报告

**创建时间**: 2025-10-16
**状态**: 📋 待修复（不影响核心导出功能）

---

## 🎯 为什么是低优先级？

这些文件虽然包含旧API调用，但**不影响用户当前测试的核心功能**：
- ✅ 核心翻译流程（拆分 → 执行 → 导出）完全正常
- ✅ 阶段1、2、3的测试页面功能正常
- ✅ Session管理和数据状态转换正常

这些文件主要涉及：
- 🔧 辅助功能（性能监控、进度追踪）
- 💾 持久化功能（检查点、恢复）
- 🧹 清理功能（会话清理）
- 📡 WebSocket实时推送

---

## 📋 待修复文件清单

### 1. `services/cleanup/session_cleaner.py`
**功能**: 自动清理过期Session
**使用旧API**: 1处

```python
# Line 183
task_manager = pipeline_session_manager.get_task_manager(session_id)
```

**影响**:
- ⚠️ 清理功能可能会失败
- ✅ 不影响核心翻译流程

**修复方案**:
```python
task_manager = pipeline_session_manager.get_tasks(session_id)
```

---

### 2. `services/persistence/excel_writer.py`
**功能**: 将翻译结果写入Excel（可能是旧版本）
**使用旧API**: 4处

```python
# Line 56, 226, 254, 287
task_manager = pipeline_session_manager.get_task_manager(session_id)
```

**影响**:
- ⚠️ 如果代码调用此文件会失败
- ✅ 新的ExcelExporter已修复，应使用新的导出器

**修复方案**:
```python
task_manager = pipeline_session_manager.get_tasks(session_id)
```

**注意**: 这个文件可能与 `excel_exporter.py` 功能重复，建议检查是否可以删除。

---

### 3. `services/executor/progress_tracker.py`
**功能**: 实时进度追踪
**使用旧API**: 4处

```python
# Line 53, 73, 164, 219
task_manager = pipeline_session_manager.get_task_manager(session_id)
```

**影响**:
- ⚠️ 进度追踪可能不准确
- ✅ 基本执行流程不受影响

**修复方案**:
```python
task_manager = pipeline_session_manager.get_tasks(session_id)
```

---

### 4. `services/persistence/checkpoint_service.py`
**功能**: 检查点服务（断点保存）
**使用旧API**: 3处

```python
# Line 56, 159, 265
task_manager = pipeline_session_manager.get_task_manager(session_id)
```

**影响**:
- ⚠️ 检查点功能可能失败
- ✅ 不影响正常翻译流程

**修复方案**:
```python
task_manager = pipeline_session_manager.get_tasks(session_id)
```

**注意**: 已修复 `executor/resume_handler.py`，可能与此文件功能重复。

---

### 5. `api/websocket_api.py`
**功能**: WebSocket实时推送进度
**使用旧API**: 1处

```python
# Line 297
task_manager = pipeline_session_manager.get_task_manager(session_id)
```

**影响**:
- ⚠️ WebSocket推送可能失败
- ✅ HTTP轮询仍可正常工作

**修复方案**:
```python
task_manager = pipeline_session_manager.get_tasks(session_id)
```

---

### 6. `api/session_api.py`
**功能**: Session管理API端点
**使用旧API**: 2处

```python
# Line 43, 187
task_manager = pipeline_session_manager.get_task_manager(session_id)
```

**影响**:
- ⚠️ 部分Session API可能失败
- ✅ 核心Session创建和获取功能正常

**修复方案**:
```python
task_manager = pipeline_session_manager.get_tasks(session_id)
```

---

### 7. `api/resume_api.py`
**功能**: 恢复中断的Session
**使用旧API**: 3处

```python
# Line 63, 138, 189
if pipeline_session_manager.get_task_manager(session_id):
    # ...
task_manager = pipeline_session_manager.get_task_manager(session_id)
```

**影响**:
- ⚠️ 恢复功能可能失败
- ✅ 新Session正常创建

**修复方案**:
```python
task_manager = pipeline_session_manager.get_tasks(session_id)
```

---

## 📊 统计摘要

| 文件 | 旧API使用次数 | 功能类型 | 优先级 |
|-----|------------|---------|-------|
| session_cleaner.py | 1 | 清理 | 低 |
| excel_writer.py | 4 | 持久化 | 低（可能废弃） |
| progress_tracker.py | 4 | 监控 | 中 |
| checkpoint_service.py | 3 | 持久化 | 低 |
| websocket_api.py | 1 | 实时通信 | 中 |
| session_api.py | 2 | API | 中 |
| resume_api.py | 3 | API | 低 |
| **总计** | **18处** | - | - |

---

## 🔧 统一修复方案

所有文件的修复都非常简单，只需要将：

```python
# 旧API ❌
task_manager = pipeline_session_manager.get_task_manager(session_id)
excel_df = pipeline_session_manager.get_excel_df(session_id)

# 新API ✅
task_manager = pipeline_session_manager.get_tasks(session_id)
excel_df = pipeline_session_manager.get_output_state(session_id)  # 或 get_input_state()
```

---

## ⏰ 建议修复时机

**现在不需要修复的理由**:
1. ✅ 核心导出功能已修复（`ExcelExporter`）
2. ✅ 用户测试不会触发这些文件
3. ✅ 系统可以正常运行核心功能

**建议修复时机**:
- 当用户测试通过后
- 当需要使用这些辅助功能时
- 集中修复所有旧API调用

---

## 🚀 快速修复脚本

如果需要快速修复所有文件，可以使用：

```bash
# 批量替换所有文件
cd /mnt/d/work/trans_excel/translation_system_v2/backend_v2

# 修复 get_task_manager
sed -i 's/\.get_task_manager(/.get_tasks(/g' \
  services/cleanup/session_cleaner.py \
  services/persistence/excel_writer.py \
  services/executor/progress_tracker.py \
  services/persistence/checkpoint_service.py \
  api/websocket_api.py \
  api/session_api.py \
  api/resume_api.py

# 修复 get_excel_df（如果有）
sed -i 's/\.get_excel_df(/.get_output_state(/g' \
  services/cleanup/session_cleaner.py \
  services/persistence/excel_writer.py \
  services/executor/progress_tracker.py \
  services/persistence/checkpoint_service.py \
  api/websocket_api.py \
  api/session_api.py \
  api/resume_api.py

echo "✅ 所有低优先级文件已修复"
```

**注意**: 使用批量替换后需要人工检查，确保没有误替换。

---

## 📝 相关文档

- `ARCHITECTURE_FIX_SUMMARY.md` - 已完成的核心修复摘要
- `/mnt/d/work/trans_excel/translation_system_v2/.claude/ARCHITECTURE_PRINCIPLES.md` - Pipeline架构原则

---

**结论**: 这些文件可以等核心功能测试通过后再修复，不影响当前用户的测试流程。
