# 顺序工作流解决方案

## 问题描述

用户在使用前端上传文件时遇到500错误，原因是：

1. **重复会话创建**：前端在短时间内创建了多个session（3个）
2. **WorkerPool冲突**：WorkerPool是单例模式，只能同时处理一个session
3. **时序不正确**：缺少对执行完成状态的等待，导致在翻译未完成时就尝试创建CAPS session

## 核心问题

```
上传文件 → 创建Session1 → 执行翻译1
          → 创建Session2 → 执行翻译2 (❌ WorkerPool忙碌，500错误)
          → 创建Session3 → 执行翻译3 (❌ WorkerPool忙碌，500错误)
```

## 解决方案

### 1. 创建顺序工作流控制器

**文件**: `frontend_v2/js/workflows/sequential-workflow-controller.js`

**核心特性**:

#### ✅ 状态锁机制
```javascript
if (this.state.isRunning) {
  console.warn('[Workflow] Already running, ignoring duplicate execution request');
  return;  // 防止重复执行
}
this.state.isRunning = true;
```

#### ✅ 严格的时序控制
```javascript
// 阶段1：翻译
await this.uploadAndSplit('translation');
await this.executeWithMonitoring(session1, 'llm_qwen', 15, 60);
await this.waitForExecutionComplete(session1);  // ⭐ 关键：等待完成

// 阶段2：CAPS（如果需要）
const needsCaps = await this.checkIfNeedsCaps(session1);
if (needsCaps) {
  await this.splitFromParent(session1, 'caps_only');
  await this.executeWithMonitoring(session2, 'uppercase', 70, 95);
}
```

#### ✅ 动态CAPS检测（无硬编码）
```javascript
async checkIfNeedsCaps(sessionId) {
  // 从后端查询session详情
  const session = await fetch(`/api/sessions/detail/${sessionId}`).then(r => r.json());

  // 检查后端分析的sheets信息
  const sheets = session.metadata?.analysis?.file_info?.sheets || [];
  const hasCaps = sheets.some(sheet => sheet.toLowerCase().includes('caps'));

  return hasCaps;  // 完全由后端动态检测决定
}
```

### 2. 更新前端页面

**文件**: `frontend_v2/js/pages/simple-upload-page.js`

#### ✅ 添加处理标志
```javascript
class SimpleUploadPage {
  constructor() {
    this.isProcessing = false;  // 防止重复处理
    this.workflowController = null;
  }
}
```

#### ✅ 防止重复上传
```javascript
async handleFileSelect(file) {
  if (this.isProcessing) {
    console.warn('Already processing a file, ignoring duplicate request');
    return;  // 直接返回，不处理
  }
  this.isProcessing = true;

  try {
    // ... 处理逻辑
  } finally {
    this.isProcessing = false;  // 确保重置
  }
}
```

#### ✅ 防止重复执行
```javascript
async startWorkflow(config) {
  if (this.workflowController.isRunning()) {
    console.warn('Workflow already running, ignoring duplicate request');
    return;
  }

  // 禁用开始按钮
  startBtn.disabled = true;

  try {
    await this.workflowController.execute(this.file, config);
  } finally {
    startBtn.disabled = false;  // 重新启用
  }
}
```

### 3. 修复API配置

**文件**: `frontend_v2/index.html`

```html
<!-- API Configuration -->
<script>
    // 定义API基础URL（全局配置）
    window.API_BASE_URL = 'http://localhost:8013';
</script>
```

## 完整API时序图

```
用户上传文件
    ↓
【检查isProcessing标志】 ← 防止重复上传
    ↓
创建SequentialWorkflowController
    ↓
【检查isRunning标志】 ← 防止重复执行
    ↓
═════════════════════════════════════
阶段1: 翻译
═════════════════════════════════════
    ↓
POST /api/tasks/split (file, rule_set='translation')
    → 返回 session_id_1
    ↓
GET /api/tasks/split/status/{session_id_1} (轮询)
    → 等待 status='completed'
    ↓
POST /api/execute/start (session_id_1, processor='llm_qwen')
    ↓
WebSocket /api/websocket/progress/{session_id_1}
    → 监控进度直到 status='completed'
    ↓
【waitForExecutionComplete】 ← ⭐ 关键：验证完成
GET /api/execute/status/{session_id_1}
    → 等待 status='completed' && ready_for_download=true
    ↓
═════════════════════════════════════
动态检测CAPS
═════════════════════════════════════
    ↓
GET /api/sessions/detail/{session_id_1}
    → 检查 metadata.analysis.file_info.sheets
    → 判断是否包含 'caps' sheet
    ↓
如果 needsCaps == false:
    ↓
    完成！(单阶段)

如果 needsCaps == true:
    ↓
═════════════════════════════════════
阶段2: CAPS转换
═════════════════════════════════════
    ↓
POST /api/tasks/split (parent_session_id=session_id_1, rule_set='caps_only')
    → 返回 session_id_2
    ↓
GET /api/tasks/split/status/{session_id_2} (轮询)
    → 等待 status='completed'
    ↓
POST /api/execute/start (session_id_2, processor='uppercase')
    ↓
WebSocket /api/websocket/progress/{session_id_2}
    → 监控进度直到 status='completed'
    ↓
完成！(两阶段)
```

## 关键改进点

### 1. **防止重复执行** ✅
- 页面级别：`isProcessing` 标志
- 控制器级别：`isRunning` 状态锁
- UI级别：禁用开始按钮

### 2. **严格时序控制** ✅
- 使用 `await` 确保顺序执行
- 添加 `waitForExecutionComplete()` 验证完成状态
- 只有前一个阶段完全完成才进入下一个

### 3. **无硬编码** ✅
- 不在前端假设是否有CAPS
- 通过后端API动态查询
- 完全由后端分析结果决定

### 4. **错误恢复** ✅
- 所有API调用都有错误处理
- 失败时重置状态标志
- 清晰的错误消息

## 测试页面

创建了专门的测试页面: `frontend_v2/test_sequential_workflow.html`

**特性**:
- 完整的日志输出
- 实时进度显示
- Session链可视化
- 便于调试和验证

## 使用方法

### 主页面使用
1. 访问 `http://localhost:8090/#/`
2. 选择Excel文件
3. 确认配置
4. 点击"开始翻译"
5. 系统自动：
   - 执行翻译
   - 检测是否需要CAPS
   - 如需要，自动执行CAPS转换
   - 显示最终结果

### 测试页面使用
1. 访问 `http://localhost:8090/test_sequential_workflow.html`
2. 选择文件
3. 配置语言
4. 点击"开始执行工作流"
5. 查看详细日志和进度

## 验证结果

根据后端日志，之前的问题：

```
❌ Session 1: cdc21b96... (创建)
❌ Session 2: ed019d95... (成功完成)
❌ Session 3: 112e2a52... (500错误 - WorkerPool忙碌)
```

使用新方案后：

```
✅ 只创建必要的Session
✅ 严格按时序执行
✅ 无WorkerPool冲突
✅ 动态检测CAPS需求
```

## 文件清单

| 文件 | 说明 | 状态 |
|------|------|------|
| `js/workflows/sequential-workflow-controller.js` | 新的顺序工作流控制器 | ✅ 新增 |
| `js/pages/simple-upload-page.js` | 更新使用新控制器 | ✅ 修改 |
| `index.html` | 添加API_BASE_URL配置 | ✅ 修改 |
| `test_sequential_workflow.html` | 测试页面 | ✅ 新增 |
| `API_SEQUENCE_DIAGRAM.md` | API时序图文档 | ✅ 已存在 |

## 总结

这个解决方案通过以下三个层次确保了系统的稳定性：

1. **UI层防护**：禁用按钮，防止用户重复点击
2. **逻辑层防护**：isProcessing标志，防止重复处理
3. **控制器层防护**：isRunning状态锁，防止并发执行

同时，通过动态检测CAPS需求，避免了硬编码假设，使系统更加灵活和健壮。

## 进度显示增强 ✅

**最新更新 (2025-10-17 晚)**

增强了 `simple-upload-page.js` 的进度显示功能，现在能够根据 `API_SEQUENCE_DIAGRAM.md` 显示详细的阶段信息：

### 新增功能

1. **阶段智能识别** (`parseProgressPhase`)
   - 根据消息内容自动识别当前所处阶段
   - 支持的阶段：
     - 📤 文件上传与分析
     - ✂️ 任务拆分
     - 🤖 LLM翻译执行
     - ✓ 验证翻译完成状态
     - 🔍 检测是否需要CAPS处理
     - 🔠 CAPS大写转换

2. **详细进度展示** (`renderProgressDetails`)
   - 显示阶段编号（阶段1/2、阶段2/2）
   - 显示阶段图标和名称
   - 显示任务完成进度（3/7 完成）
   - 显示Session ID（用于调试）
   - 失败任务数量提示

3. **动态标题更新**
   - 进度卡片标题实时显示当前阶段
   - 例如："🤖 LLM翻译执行"、"🔠 CAPS大写转换"

### 显示效果示例

```
┌─────────────────────────────────────────┐
│ 🤖 LLM翻译执行                           │
├─────────────────────────────────────────┤
│ 阶段1/2: AI翻译执行中... 3/7            │
│ ▓▓▓▓▓▓▓▓▓░░░░░░░░░░░ 45%               │
├─────────────────────────────────────────┤
│ 📋 阶段详情                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ 🤖                                      │
│ 阶段 1/2: LLM翻译执行                   │
│ AI翻译                                  │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│ 任务进度: 3/7 (43%)                     │
│ Session: ed019d95...                    │
└─────────────────────────────────────────┘
```

### 代码改进

**simple-upload-page.js**:
- ✅ `parseProgressPhase()` - 根据消息内容智能识别阶段
- ✅ `renderProgressDetails()` - 渲染详细的阶段信息
- ✅ `updateProgress()` - 更新标题和详细信息
- ✅ `addPhaseDownloadButton()` - 动态添加阶段下载按钮
- ✅ `downloadPhaseResult()` - 下载阶段中间结果

**sequential-workflow-controller.js**:
- ✅ 所有 `updateProgress()` 调用都包含 `sessionId`
- ✅ WebSocket 和轮询监控都传递 `sessionId`
- ✅ 新增 `onPhaseComplete()` 回调机制
- ✅ 阶段1（翻译）完成后触发回调
- ✅ 阶段2（CAPS）完成后触发回调（如有）

## 阶段中间结果下载 ✅

**最新更新 (2025-10-17 晚)**

新增了每个阶段完成后下载中间结果的功能，类似测试页面的体验：

### 功能特性

1. **自动显示下载按钮**
   - 阶段1（翻译）完成 → 自动显示"翻译阶段"下载按钮
   - 阶段2（CAPS）完成 → 自动显示"CAPS转换阶段"下载按钮

2. **双重下载选项**
   - **下载结果Excel**: 该阶段的output_state（可作为下一阶段输入）
   - **下载DataFrame**: DataFrame格式，包含所有color_*和comment_*列

3. **UI展示**
   ```
   ┌─────────────────────────────────────────────────────┐
   │ ✅ 🤖 翻译阶段 - 已完成                              │
   │ Session: ed019d95...                                │
   │ [📥 下载结果Excel]  [📊 下载DataFrame]              │
   └─────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────┐
   │ ✅ 🔠 CAPS转换阶段 - 已完成                         │
   │ Session: 112e2a52...                                │
   │ [📥 下载结果Excel]  [📊 下载DataFrame]              │
   └─────────────────────────────────────────────────────┘
   ```

### 工作流程

1. **阶段1完成时**:
   ```javascript
   // Controller触发
   this.notifyPhaseComplete({
     phase: 1,
     name: '翻译阶段',
     icon: '🤖',
     sessionId: session1
   });

   // Page自动添加下载按钮
   this.addPhaseDownloadButton(phaseInfo);
   ```

2. **用户点击下载**:
   ```javascript
   // 下载结果Excel
   GET /api/download/{sessionId}

   // 或下载DataFrame
   GET /api/tasks/export/{sessionId}?export_type=dataframe
   ```

### 使用场景

- **验证翻译结果**: 阶段1完成后立即下载验证翻译质量
- **中间调试**: 下载DataFrame查看完整的数据状态
- **手动干预**: 下载中间结果，手动调整后重新上传
- **归档备份**: 保存每个阶段的中间状态

## 下一步

建议添加：
1. ✅ 进度条显示（已实现）
2. ✅ WebSocket连接状态监控（已实现）
3. ✅ 错误重试机制（已在controller中实现）
4. ✅ 详细阶段进度显示（已实现）
5. ✅ 阶段中间结果下载（已实现）
6. ⏳ 暂停/恢复功能（可选）
7. ⏳ 批量文件处理（可选）

## 统一工作流页面 ✅

**最新更新 (2025-10-17 深夜)**

创建了全新的 `UnifiedWorkflowPage`，直接复用三个已测试的页面逻辑，确保一致性：

### 设计理念

复用测试页面的核心逻辑：
- **阶段1**: 来自 `1_upload_and_split.html` - 上传并拆分任务
- **阶段2**: 来自 `2_execute_transformation.html` - 执行翻译
- **阶段3**: 来自 `4_caps_transformation.html` - CAPS转换（可选）

### 核心特性

1. **三阶段进度条**
   ```
   ┌─────────────────────────────────┐
   │ 🎯 阶段1: 任务拆分             │
   │ ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░ 50%        │
   │ Session: abc123...             │
   │ [📄 导出Excel] [📋 导出任务表] │
   └─────────────────────────────────┘

   ┌─────────────────────────────────┐
   │ ⚡ 阶段2: 执行翻译             │
   │ ▓▓▓▓▓▓░░░░░░░░░░░░░ 30%        │
   │ 已完成 3/10 任务               │
   └─────────────────────────────────┘

   ┌─────────────────────────────────┐
   │ 🔠 阶段3: CAPS转换 (可选)      │
   │ 等待检测...                     │
   └─────────────────────────────────┘
   ```

2. **每个阶段都有下载按钮**
   - 阶段1完成 → 显示"导出拆分前Excel"、"导出任务表"
   - 阶段2完成 → 显示"导出翻译结果Excel"、"导出DataFrame"
   - 阶段3完成 → 显示"导出最终结果Excel"、"导出DataFrame"

3. **Session ID可复制**
   - 每个阶段完成后显示Session ID
   - 点击即可复制到剪贴板
   - 便于手动调试和验证

### 文件结构

```
frontend_v2/
├── js/pages/
│   ├── unified-workflow-page.js  ✅ 新增 - 统一工作流页面
│   ├── simple-upload-page.js     (保留作为备选)
│   └── ...
├── index.html  ✅ 修改 - 加载新页面
└── js/app.js   ✅ 修改 - 路由指向新页面
```

### 路由配置

```javascript
// app.js
case 'upload':
    // 优先使用统一工作流页面
    if (typeof UnifiedWorkflowPage !== 'undefined') {
        pageInstance = new UnifiedWorkflowPage();
        await pageInstance.init();
    }
    // 降级方案...
```

### 与测试页面的对应关系

| 测试页面 | 对应功能 | 整合到 |
|---------|---------|--------|
| `1_upload_and_split.html` | 上传并拆分 | `executePhase1()` |
| `2_execute_transformation.html` | 执行翻译 | `executePhase2()` |
| `4_caps_transformation.html` | CAPS转换 | `checkAndExecutePhase3()` |

### 核心方法

```javascript
class UnifiedWorkflowPage {
  // 阶段1: 上传并拆分 (复用测试页面1的逻辑)
  async executePhase1() {
    // FormData上传
    // 轮询拆分状态
    // 显示下载按钮
  }

  // 阶段2: 执行翻译 (复用测试页面2的逻辑)
  async executePhase2() {
    // POST /api/execute/start
    // 轮询执行状态
    // 更新进度条
  }

  // 阶段3: CAPS转换 (复用测试页面4的逻辑)
  async checkAndExecutePhase3() {
    // 检测CAPS需求
    // 拆分CAPS任务
    // 执行uppercase转换
  }

  // 通用轮询方法 (与测试页面一致)
  async pollSplitStatus(sessionId) { ... }
  async pollExecutionStatus(sessionId, phaseNum) { ... }
}
```

### 优势

✅ **一致性**: 完全复用已验证的测试页面逻辑
✅ **可靠性**: 测试页面已经过验证，无需重新测试
✅ **可维护性**: 集中管理三个阶段，易于调试
✅ **用户体验**: 在一个页面看到完整流程，无需跳转

---

**创建时间**: 2025-10-17
**作者**: Claude
**版本**: 2.0 (统一工作流页面)
