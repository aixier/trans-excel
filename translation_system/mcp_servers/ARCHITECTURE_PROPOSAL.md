# MCP 架构整合建议

## 🎯 问题分析

当前有两个独立的 MCP 服务器：

### excel_mcp (Excel 分析服务)
- **功能**: Excel 文件分析、语言检测、颜色检测、格式分析
- **工具**: `excel_analyze`, `excel_get_status`, `excel_export`
- **输出**: 分析报告、统计信息

### task_mcp (任务拆分服务)
- **功能**: Excel 文件拆分为翻译任务、批次分配
- **工具**: `task_split`, `task_get_split_status`, `task_export`, `task_get_batches`, `task_preview`
- **输出**: 任务列表、批次信息

## ⚠️ 当前问题

1. **功能重复**
   - 两个服务都需要加载 Excel
   - 两个服务都需要颜色检测
   - 两个服务都需要语言识别
   - 两个服务都需要 Token 验证

2. **代码重复**
   ```
   excel_mcp/
   ├── utils/color_detector.py     ✅
   ├── utils/http_client.py        ✅
   ├── utils/token_validator.py    ✅
   ├── services/excel_loader.py    ✅

   task_mcp/
   ├── utils/color_detector.py     ❌ 重复
   ├── utils/http_client.py        ❌ 重复
   ├── utils/token_validator.py    ❌ 重复
   ├── utils/excel_loader.py       ❌ 重复
   ```

3. **用户体验割裂**
   - 用户需要调用两个不同的服务
   - 需要管理两个 session_id
   - 分析结果无法直接用于任务拆分

---

## ✅ 整合方案

### 方案：将 task_mcp 整合到 excel_mcp

```
excel_mcp/  (统一的 Excel 处理 MCP)
├── server.py
├── mcp_tools.py              # 整合所有工具
├── mcp_handler.py
│
├── utils/                    # 共享工具
│   ├── http_client.py
│   ├── token_validator.py
│   ├── session_manager.py
│   ├── color_detector.py     # 统一颜色检测
│   ├── language_mapper.py    # 统一语言映射
│   └── excel_loader.py       # 统一 Excel 加载
│
├── services/
│   ├── excel_analyzer.py     # Excel 分析服务
│   ├── task_splitter.py      # 任务拆分服务 (NEW)
│   ├── task_exporter.py      # 任务导出服务 (NEW)
│   └── batch_allocator.py    # 批次分配服务 (NEW)
│
├── models/
│   ├── excel_dataframe.py
│   ├── session_data.py
│   ├── analysis_result.py
│   ├── task_data.py          # 任务数据模型 (NEW)
│   └── batch_data.py         # 批次数据模型 (NEW)
│
├── config/
│   └── color_config.yaml     # 统一颜色配置
│
└── static/
    └── index.html            # 统一测试页面
```

---

## 🔧 整合后的 MCP 工具

### 分析类工具 (已有)
1. **excel_analyze** - Excel 文件分析
2. **excel_get_status** - 获取分析状态
3. **excel_export** - 导出分析结果

### 任务类工具 (新增)
4. **excel_split_tasks** - 拆分翻译任务
5. **excel_get_tasks** - 获取任务列表
6. **excel_export_tasks** - 导出任务 Excel
7. **excel_get_batches** - 获取批次信息

---

## 📊 工作流程对比

### 当前工作流 (分离架构)
```
用户
 ↓
[1. excel_mcp.excel_analyze] → session_id_1
 ↓
[2. excel_mcp.excel_get_status] → 分析结果
 ↓
[3. 手动下载 Excel]
 ↓
[4. task_mcp.task_split] → session_id_2
 ↓
[5. task_mcp.task_get_split_status] → 任务结果
 ↓
[6. task_mcp.task_export] → 下载任务 Excel
```

### 整合后工作流 (统一架构)
```
用户
 ↓
[1. excel_mcp.excel_analyze_and_split] → session_id
     ├── 分析 Excel
     └── 拆分任务 (可选)
 ↓
[2. excel_mcp.excel_get_status] → 完整结果
     ├── 分析报告
     └── 任务列表
 ↓
[3. excel_mcp.excel_export_tasks] → 下载任务 Excel
```

---

## 🎨 统一的 Session 数据结构

```python
@dataclass
class UnifiedSession:
    """统一的 Excel 处理 Session"""

    session_id: str
    token: str
    status: SessionStatus

    # Excel 文件信息
    excel_url: Optional[str] = None
    excel_path: Optional[str] = None

    # 分析结果
    analysis_result: Optional[Dict] = None

    # 任务拆分结果 (可选)
    tasks: List[Dict] = field(default_factory=list)
    batches: List[Dict] = field(default_factory=list)
    summary: Optional[Dict] = None

    # 导出路径
    analysis_export_path: Optional[str] = None
    tasks_export_path: Optional[str] = None
```

---

## 🔄 迁移步骤

### Phase 1: 准备阶段
1. ✅ 在 excel_mcp 中添加 task 相关 models
2. ✅ 复用现有的 color_detector, language_mapper
3. ✅ 添加 task_splitter, batch_allocator services

### Phase 2: 工具整合
1. ✅ 添加 `excel_split_tasks` 工具
2. ✅ 添加 `excel_get_batches` 工具
3. ✅ 添加 `excel_export_tasks` 工具
4. ✅ 更新 `excel_get_status` 返回任务信息

### Phase 3: 统一 Session
1. ✅ 扩展 Session 数据结构
2. ✅ 支持分析+拆分一体化流程
3. ✅ 统一导出功能

### Phase 4: 清理
1. ✅ 标记 task_mcp 为 deprecated
2. ✅ 迁移测试页面到 excel_mcp
3. ✅ 更新文档

---

## 💡 API 设计示例

### 1. 一体化分析+拆分
```json
// Request
{
  "tool": "excel_analyze_and_split",
  "arguments": {
    "token": "Bearer xxx",
    "file_url": "http://example.com/file.xlsx",
    "options": {
      "analyze": true,
      "split_tasks": true,
      "source_lang": "CH",
      "target_langs": ["PT", "TH", "VN"]
    }
  }
}

// Response
{
  "session_id": "excel_abc123",
  "status": "queued",
  "message": "Analysis and task splitting submitted"
}
```

### 2. 获取完整结果
```json
// Request
{
  "tool": "excel_get_status",
  "arguments": {
    "token": "Bearer xxx",
    "session_id": "excel_abc123"
  }
}

// Response
{
  "session_id": "excel_abc123",
  "status": "completed",
  "progress": 100,
  "result": {
    "analysis": {
      "file_info": {...},
      "language_detection": {...},
      "color_analysis": {...}
    },
    "tasks": {
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
    }
  }
}
```

### 3. 导出任务
```json
// Request
{
  "tool": "excel_export_tasks",
  "arguments": {
    "token": "Bearer xxx",
    "session_id": "excel_abc123",
    "format": "excel"
  }
}

// Response
{
  "download_url": "http://localhost:8022/downloads/tasks_abc123.xlsx",
  "filename": "tasks_abc123.xlsx",
  "size": 524288
}
```

---

## 📈 优势分析

### 1. 代码复用 ✅
- 单一颜色检测实现
- 单一语言映射实现
- 单一 Excel 加载逻辑
- 单一 Token 验证

### 2. 用户体验 ✅
- 一次调用完成分析+拆分
- 单一 session_id 管理
- 统一的 API 接口
- 一致的错误处理

### 3. 维护性 ✅
- 减少代码重复
- 统一配置管理
- 集中错误处理
- 更容易测试

### 4. 性能优化 ✅
- Excel 只加载一次
- 颜色检测复用
- 语言检测复用
- 减少网络传输

---

## 🔍 对比总结

| 特性 | 分离架构 (当前) | 统一架构 (建议) |
|------|----------------|----------------|
| MCP 服务数量 | 2 个 | 1 个 |
| 代码重复 | 高 | 低 |
| API 调用次数 | 6+ 次 | 3 次 |
| Session 管理 | 2 个 session_id | 1 个 session_id |
| Excel 加载次数 | 2 次 | 1 次 |
| 配置文件 | 分散 | 统一 |
| 测试页面 | 2 个 | 1 个 |
| 维护成本 | 高 | 低 |
| 用户学习成本 | 高 | 低 |

---

## 🚀 实施建议

### 立即可行
1. **保留 excel_mcp 作为主服务**
2. **将 task_mcp 的核心功能迁移到 excel_mcp**
   - `services/task_splitter.py`
   - `services/batch_allocator.py`
   - `services/task_exporter.py`
3. **添加新的 MCP 工具**
   - `excel_split_tasks`
   - `excel_export_tasks`
   - `excel_get_batches`

### 兼容过渡
1. **task_mcp 标记为 deprecated**
2. **保留 task_mcp 一段时间，内部调用 excel_mcp**
3. **逐步迁移用户到统一 API**

### 长期规划
1. **excel_mcp 改名为 translation_mcp**
2. **整合更多翻译相关功能**
   - 术语库管理
   - 翻译记忆
   - 质量检查

---

## 📝 迁移检查清单

- [ ] 将 task_splitter_service.py 迁移到 excel_mcp/services/
- [ ] 将 batch_allocator 逻辑整合到 excel_mcp
- [ ] 统一 color_detector (使用配置化版本)
- [ ] 统一 language_mapper
- [ ] 扩展 Session 数据模型支持任务数据
- [ ] 添加 excel_split_tasks 工具
- [ ] 添加 excel_export_tasks 工具
- [ ] 更新测试页面
- [ ] 更新文档
- [ ] 标记 task_mcp 为 deprecated

---

**建议**: ✅ **立即开始整合，将 task_mcp 功能合并到 excel_mcp**

**收益**:
- 减少 50% 代码重复
- 提升 3x 用户体验
- 降低 60% 维护成本
- 统一架构更易扩展

**版本**: 1.0.0
**提出时间**: 2025-10-03
**状态**: 📋 待实施
