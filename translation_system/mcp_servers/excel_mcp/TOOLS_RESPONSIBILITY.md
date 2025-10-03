# Excel MCP 工具职责定义

## 🎯 设计原则

1. **单一职责** - 每个工具只做一件事
2. **清晰边界** - 分析与处理分离
3. **可组合性** - 工具可以独立使用或组合使用
4. **向后兼容** - 保留原有工具，新增任务处理工具

---

## 📊 工具分类

### A. 分析类工具 (Analysis Tools)
**职责**: 理解 Excel 内容，不做修改

### B. 处理类工具 (Processing Tools)
**职责**: 基于分析结果进行数据处理

### C. 导出类工具 (Export Tools)
**职责**: 输出结果为不同格式

---

## 🔧 工具职责详细定义

### 1. excel_analyze (已有 - Analysis)
**职责**: 分析 Excel 文件结构和内容

**功能**:
- ✅ 文件结构分析 (sheets, rows, columns)
- ✅ 语言检测 (source/target languages)
- ✅ 颜色检测 (yellow/blue cells)
- ✅ 格式检测 (comments, formulas)
- ✅ 统计信息 (task estimation)

**输入**:
```json
{
  "token": "Bearer xxx",
  "file_url": "http://example.com/file.xlsx",
  "options": {
    "detect_language": true,
    "detect_formats": true,
    "analyze_colors": true
  }
}
```

**输出**:
```json
{
  "session_id": "excel_abc123",
  "status": "queued"
}
```

---

### 2. excel_get_analysis (新增 - Analysis)
**职责**: 获取分析结果

**功能**:
- ✅ 查询分析状态
- ✅ 返回完整分析报告
- ✅ 不包含任务拆分数据

**输入**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123"
}
```

**输出**:
```json
{
  "session_id": "excel_abc123",
  "status": "completed",
  "result": {
    "file_info": {...},
    "language_detection": {...},
    "color_analysis": {...},
    "statistics": {...}
  }
}
```

---

### 3. excel_split_tasks (新增 - Processing)
**职责**: 基于已分析的 Excel 拆分翻译任务

**功能**:
- ✅ 根据源/目标语言拆分任务
- ✅ 颜色标记任务类型识别 (normal/yellow/blue)
- ✅ 批次智能分配
- ✅ 任务优先级计算
- ✅ 上下文提取 (可选)

**前置条件**: 必须先调用 `excel_analyze`

**输入**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123",
  "source_lang": "CH",
  "target_langs": ["PT", "TH", "VN"],
  "extract_context": true,
  "context_options": {
    "game_info": true,
    "neighbors": true,
    "content_analysis": true
  }
}
```

**输出**:
```json
{
  "session_id": "excel_abc123",
  "status": "queued",
  "message": "Task splitting submitted"
}
```

---

### 4. excel_get_tasks (新增 - Processing)
**职责**: 获取任务拆分结果和批次信息

**功能**:
- ✅ 查询拆分状态
- ✅ 返回任务统计摘要
- ✅ 返回批次分布信息
- ✅ 支持任务预览 (limit)

**输入**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123",
  "preview_limit": 10
}
```

**输出**:
```json
{
  "session_id": "excel_abc123",
  "status": "completed",
  "result": {
    "summary": {
      "total_tasks": 150,
      "batch_count": 6,
      "task_breakdown": {
        "normal": 100,
        "yellow": 30,
        "blue": 20
      },
      "batch_distribution": {
        "PT": 2,
        "TH": 2,
        "VN": 2
      },
      "type_batch_distribution": {
        "normal": 4,
        "yellow": 1,
        "blue": 1
      }
    },
    "preview_tasks": [...]
  }
}
```

---

### 5. excel_get_batches (新增 - Processing)
**职责**: 获取批次详细信息

**功能**:
- ✅ 返回所有批次列表
- ✅ 每个批次的统计信息
- ✅ 按语言/类型分组

**输入**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123"
}
```

**输出**:
```json
{
  "batches": [
    {
      "batch_id": "batch_001",
      "target_lang": "PT",
      "task_count": 50,
      "char_count": 5000,
      "task_types": {
        "normal": 40,
        "yellow": 10
      }
    }
  ]
}
```

---

### 6. excel_export_analysis (已有 - Export)
**职责**: 导出分析结果

**功能**:
- ✅ JSON 格式导出分析报告
- ✅ CSV 格式导出统计数据

**输入**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123",
  "format": "json"
}
```

**输出**:
```json
{
  "download_url": "http://localhost:8022/downloads/analysis_abc123.json",
  "filename": "analysis_abc123.json",
  "size": 12345
}
```

---

### 7. excel_export_tasks (新增 - Export)
**职责**: 导出任务列表为 Excel/JSON/CSV

**功能**:
- ✅ Excel 格式 (包含所有字段)
- ✅ JSON 格式 (结构化数据)
- ✅ CSV 格式 (表格数据)

**输入**:
```json
{
  "token": "Bearer xxx",
  "session_id": "excel_abc123",
  "format": "excel",
  "include_context": true
}
```

**输出**:
```json
{
  "download_url": "http://localhost:8022/downloads/tasks_abc123.xlsx",
  "filename": "tasks_abc123.xlsx",
  "size": 524288
}
```

---

## 📋 工具调用流程

### 流程 A: 仅分析 (Analysis Only)
```
1. excel_analyze → session_id
2. excel_get_analysis → 分析报告
3. excel_export_analysis → 下载分析结果
```

### 流程 B: 分析 + 任务拆分 (Analysis + Task Splitting)
```
1. excel_analyze → session_id
2. excel_get_analysis → 确认分析完成
3. excel_split_tasks → 使用同一 session_id
4. excel_get_tasks → 获取任务和批次信息
5. excel_export_tasks → 下载任务 Excel
```

### 流程 C: 快速拆分 (Quick Split - 推荐)
```
1. excel_analyze (options: {quick_split: true, target_langs: [...]})
   → 自动触发分析 + 拆分
2. excel_get_tasks → 获取完整结果
3. excel_export_tasks → 下载任务 Excel
```

---

## 🔄 工具依赖关系

```
excel_analyze (独立)
    ↓
    ├→ excel_get_analysis (依赖 analyze)
    ├→ excel_export_analysis (依赖 analyze)
    └→ excel_split_tasks (依赖 analyze)
           ↓
           ├→ excel_get_tasks (依赖 split_tasks)
           ├→ excel_get_batches (依赖 split_tasks)
           └→ excel_export_tasks (依赖 split_tasks)
```

---

## ⚙️ Session 生命周期

### 阶段 1: 分析中
```json
{
  "session_id": "excel_abc123",
  "status": "analyzing",
  "has_analysis": false,
  "has_tasks": false
}
```

### 阶段 2: 分析完成
```json
{
  "session_id": "excel_abc123",
  "status": "completed",
  "has_analysis": true,
  "has_tasks": false,
  "analysis_result": {...}
}
```

### 阶段 3: 任务拆分中
```json
{
  "session_id": "excel_abc123",
  "status": "splitting",
  "has_analysis": true,
  "has_tasks": false,
  "analysis_result": {...}
}
```

### 阶段 4: 全部完成
```json
{
  "session_id": "excel_abc123",
  "status": "completed",
  "has_analysis": true,
  "has_tasks": true,
  "analysis_result": {...},
  "tasks_result": {...}
}
```

---

## 🎯 职责边界总结

| 工具 | 职责 | 输入 | 输出 | 依赖 |
|------|------|------|------|------|
| excel_analyze | 分析 Excel 结构和内容 | Excel 文件 | session_id | 无 |
| excel_get_analysis | 获取分析结果 | session_id | 分析报告 | analyze |
| excel_split_tasks | 拆分翻译任务 | session_id + 语言配置 | session_id | analyze |
| excel_get_tasks | 获取任务列表和统计 | session_id | 任务数据 | split_tasks |
| excel_get_batches | 获取批次详细信息 | session_id | 批次列表 | split_tasks |
| excel_export_analysis | 导出分析结果 | session_id + format | 下载链接 | analyze |
| excel_export_tasks | 导出任务列表 | session_id + format | 下载链接 | split_tasks |

---

## ✅ 设计验证

### ✓ 单一职责原则
- 每个工具只负责一个明确的功能
- 分析工具不做处理，处理工具不做分析

### ✓ 开放封闭原则
- 可以添加新工具而不修改现有工具
- 通过 session_id 关联不同阶段

### ✓ 依赖倒置原则
- 高层工具 (split_tasks) 依赖低层工具 (analyze)
- 通过 session 解耦具体实现

### ✓ 接口隔离原则
- 客户端只依赖需要的工具
- 不强制使用所有工具

---

**版本**: 1.0.0
**创建时间**: 2025-10-03
**状态**: ✅ 设计完成，准备实施
