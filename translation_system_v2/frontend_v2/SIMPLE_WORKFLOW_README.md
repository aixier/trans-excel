# 极简自动化工作流 - 使用指南

## 快速开始

### 1. 引入所需文件

在 `index.html` 中添加以下脚本（按顺序）：

```html
<!-- 核心依赖 -->
<script src="js/services/api.js"></script>

<!-- 新增：极简工作流组件 -->
<script src="js/components/config-confirm-modal.js"></script>
<script src="js/workflows/auto-workflow-orchestrator.js"></script>
<script src="js/pages/simple-upload-page.js"></script>
```

### 2. 修改路由配置

在 `app.js` 中，将上传页面路由指向新的极简页面：

```javascript
// 旧的路由（注释掉）
// this.router.register('/upload', () => this.loadPage('upload'));

// 新的路由
this.router.register('/upload', () => this.loadPage('simple-upload'));
this.router.register('/create', () => this.loadPage('simple-upload'));
```

修改 `loadPage` 方法：

```javascript
async loadPage(pageName) {
  const container = document.getElementById('app');

  switch(pageName) {
    case 'simple-upload':
      if (typeof SimpleUploadPage !== 'undefined') {
        const page = new SimpleUploadPage();
        await page.init();
      }
      break;

    // ... 其他页面
  }
}
```

### 3. 启动应用

```bash
# 启动后端
cd backend_v2
python main.py

# 启动前端（在另一个终端）
cd frontend_v2
python -m http.server 8090

# 访问
open http://localhost:8090
```

---

## 用户使用流程

### 步骤1: 上传文件

用户只需拖拽或点击上传Excel文件：

```
┌──────────────────────────────────┐
│      Translation Hub             │
│                                   │
│          📤                       │
│    拖拽Excel文件到此处             │
│          或                       │
│     [选择文件]                    │
│                                   │
│  支持 .xlsx, .xls，最大50MB       │
└──────────────────────────────────┘
```

### 步骤2: 确认配置（唯一交互）

文件上传后，系统自动分析并弹出确认对话框：

```
┌──────────────────────────────────┐
│ 开始翻译                          │
├──────────────────────────────────┤
│ 📄 game_example.xlsx             │
│                                   │
│ 中文 → 英文, 泰语, 葡萄牙语       │
│ 1,400 条任务 · 约 2 分钟         │
│ ⚠️ 包含 CAPS 工作表               │
│                                   │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                   │
│ 📚 术语库（可选）                 │
│                                   │
│ ○ 不使用术语库                   │
│ ● 选择已有: [游戏通用 v2.0 ▼]    │
│ ○ 上传新术语库: [选择文件]       │
│                                   │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                   │
│   [取消]      [🚀 开始翻译]      │
└──────────────────────────────────┘
```

### 步骤3: 自动执行（全自动）

点击"开始翻译"后，系统全自动处理：

```
┌──────────────────────────────────┐
│ 处理中...                         │
├──────────────────────────────────┤
│ 阶段1/2: AI翻译执行中...          │
│ 60%                               │
│ ████████████░░░░░░░░               │
│                                   │
│ 已完成: 720/1200                  │
│ 失败: 2                           │
│                                   │
│   [⏸️ 暂停]     [❌ 取消]         │
└──────────────────────────────────┘
```

### 步骤4: 完成下载

处理完成后自动跳转到完成页面：

```
┌──────────────────────────────────┐
│          🎉                       │
│      翻译完成！                   │
│                                   │
│  总任务: 1,400  成功: 1,395       │
│  失败: 5        耗时: 1分58秒     │
│                                   │
│  [📥 立即下载]  [🔄 处理新文件]  │
└──────────────────────────────────┘
```

---

## 自动化特性

### 1. 智能参数检测

所有参数都由系统自动处理，无需用户输入：

| 参数 | 自动化方式 |
|------|-----------|
| 源语言 | 从Excel列名自动检测 |
| 目标语言 | 从Excel列名自动检测 |
| 任务类型 | 根据单元格颜色自动识别 |
| 规则集 | 根据是否有CAPS自动选择 |
| 处理器 | LLM翻译 or 大写转换 |
| 并发数 | 使用最优默认值 |

### 2. 智能工作流选择

系统自动检测Excel结构，选择最佳工作流：

**标准流程**（无CAPS工作表）:
```
上传 → 分析 → 翻译 → 下载
```

**CAPS流程**（检测到CAPS工作表）:
```
上传 → 分析 → 翻译 → CAPS转换 → 下载
                (阶段1)    (阶段2)
```

### 3. 实时进度监控

- WebSocket实时更新
- 当前批次进度
- 成功/失败统计
- 剩余时间预估

---

## API集成说明

### 需要的后端API

确保后端提供以下API：

```
POST /api/tasks/split
  - 上传文件并自动分析
  - 返回: { session_id, status }

GET /api/sessions/{session_id}
  - 获取session详情（包含analysis）

POST /api/tasks/split (with parent_session_id)
  - 从父session继承数据创建子session
  - 用于CAPS阶段

POST /api/execute/start
  - 开始执行任务
  - 参数: processor (llm_qwen / uppercase)

WS /api/websocket/progress/{session_id}
  - 实时进度推送

GET /api/download/{session_id}
  - 下载最终文件

GET /api/download/{session_id}/summary
  - 获取执行摘要
```

### 术语库API

```
GET /api/glossaries/list
  - 获取术语库列表

POST /api/glossaries
  - 上传新术语库
```

---

## 组件说明

### 1. ConfigConfirmModal（配置确认对话框）

```javascript
// 显示对话框
await configConfirmModal.show(file, analysis, (config) => {
  // 用户确认后的回调
  console.log('Selected glossary:', config.glossaryId);
  console.log('Uploaded glossary:', config.glossaryFile);
});
```

**主要方法**:
- `init()` - 初始化，加载术语库列表
- `show(file, analysis, onConfirm)` - 显示对话框
- `render()` - 渲染对话框内容

### 2. AutoWorkflowOrchestrator（工作流编排器）

```javascript
const orchestrator = new AutoWorkflowOrchestrator();

// 设置回调
orchestrator.onProgress((progress) => {
  console.log(progress.message, progress.percent);
});

orchestrator.onCompletion((result) => {
  console.log('Completed:', result.sessionId);
});

// 执行
await orchestrator.execute(file, {
  analysis,
  glossaryId,
  glossaryFile
});
```

**主要方法**:
- `execute(file, config)` - 执行完整工作流
- `onProgress(callback)` - 设置进度回调
- `onCompletion(callback)` - 设置完成回调

**内部方法**:
- `executeStandardWorkflow()` - 标准翻译流程
- `executeWithCapsWorkflow()` - 带CAPS的两阶段流程
- `monitorProgress()` - WebSocket进度监控

### 3. SimpleUploadPage（极简上传页面）

```javascript
const page = new SimpleUploadPage();
await page.init();
```

**主要方法**:
- `init()` - 初始化页面
- `handleFileSelect(file)` - 处理文件上传
- `startWorkflow(config)` - 启动工作流
- `updateProgress(progress)` - 更新进度显示
- `showCompletion(result)` - 显示完成页面

---

## 自定义配置

### 修改默认并发数

在 `auto-workflow-orchestrator.js` 中：

```javascript
// 翻译并发数（默认10）
await window.api.startExecution(sessionId, {
  processor: 'llm_qwen',
  max_workers: 10  // 修改这里
});

// CAPS并发数（默认20）
await window.api.startExecution(sessionId, {
  processor: 'uppercase',
  max_workers: 20  // 修改这里
});
```

### 修改进度映射

在 `auto-workflow-orchestrator.js` 中：

```javascript
// 标准流程进度范围
// 上传分析: 0-5%
// 拆分任务: 5-10%
// 翻译执行: 10-90%
// 生成文件: 90-100%

// CAPS流程进度范围
// 阶段1 翻译: 0-60%
// 阶段2 CAPS: 60-95%
// 生成文件: 95-100%
```

### 添加自定义规则集

在后端 `config/rules.yaml` 中添加新规则集：

```yaml
rule_sets:
  my_custom_workflow:
    - empty
    - yellow
    - my_custom_rule
```

然后在前端指定：

```javascript
await window.api.uploadFile(file, {
  rule_set: 'my_custom_workflow'
});
```

---

## 故障排查

### 问题1: 配置对话框不显示

**检查**:
- 确保 `config-confirm-modal.js` 已加载
- 检查 `#configModal` 元素是否存在
- 查看console是否有JavaScript错误

### 问题2: 进度不更新

**检查**:
- WebSocket连接是否成功（查看Network标签）
- 后端WebSocket endpoint是否正常
- 是否被防火墙阻止

### 问题3: CAPS流程只执行了阶段1

**检查**:
- 是否正确检测到CAPS工作表
- `splitFromParent` API是否正常
- 后端logs是否有错误

### 问题4: 术语库上传失败

**检查**:
- 术语库Excel格式是否正确（需要CH, EN等列）
- 文件大小是否超限
- 术语库API是否正常工作

---

## 性能优化建议

### 1. 使用批量上传

对于多个小文件，可以扩展为批量模式：

```javascript
const files = [file1, file2, file3];
for (const file of files) {
  await orchestrator.execute(file, config);
}
```

### 2. 预加载术语库

在应用启动时预加载术语库列表：

```javascript
// 在 app.js 初始化时
await configConfirmModal.init();
```

### 3. 缓存分析结果

对于重复上传的相同文件，可以缓存分析结果：

```javascript
const cacheKey = `analysis_${file.name}_${file.size}`;
const cached = localStorage.getItem(cacheKey);
if (cached) {
  this.analysis = JSON.parse(cached);
} else {
  // 执行分析
  localStorage.setItem(cacheKey, JSON.stringify(analysis));
}
```

---

## 未来扩展方向

1. **批量处理**: 支持同时上传多个文件
2. **进度持久化**: 刷新页面后可以继续
3. **邮件通知**: 长时间任务完成后发送邮件
4. **历史记录**: 快速重用之前的配置
5. **模板保存**: 保存常用配置为模板

---

## 总结

极简工作流的核心优势：

✅ **零配置**: 只需选择术语库
✅ **全自动**: 系统自动选择最佳流程
✅ **可视化**: 实时进度反馈
✅ **智能化**: 自动检测CAPS并分阶段处理
✅ **容错性**: 失败不影响整体，单独导出

**用户体验**：从上传到下载，只需2次点击！
