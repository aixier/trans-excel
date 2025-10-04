# 页面设计：任务配置页

> **页面路径**: `#/config`
> **后端API**: `/api/tasks/*`
> **设计基于**: backend_v2 实际能力

---

## 1. 页面概述

### 1.1 核心功能
基于后端 `task_api.py` 的实际能力，此页面负责：
- 配置源语言和目标语言
- 设置上下文提取选项（影响翻译质量和速度）
- 拆分翻译任务为批次
- 查看拆分进度和结果

### 1.2 后端API能力
根据 `task_api.py` 代码分析：
- ✅ 支持多目标语言同时翻译
- ✅ 支持上下文提取开关（extract_context）
- ✅ 支持细粒度上下文选项（5个可选项）
- ✅ 支持异步任务拆分
- ✅ 支持拆分进度查询
- ✅ 支持导出任务DataFrame
- ❌ 不支持批次大小自定义
- ❌ 不支持自定义Prompt模板

---

## 2. 功能设计

### 2.1 语言配置

#### 基于后端定义（task_api.py）
```python
class SplitRequest(BaseModel):
    session_id: str
    source_lang: Optional[str] = None  # CH/EN, None for auto-detect
    target_langs: List[str]  # [PT, TH, VN, TR, IND, ES]
    extract_context: Optional[bool] = True
    context_options: Optional[ContextOptions] = None
```

#### 支持的语言
```javascript
// 根据测试页面和后端支持
源语言 = {
  'auto': '自动检测',
  'CH': '中文',
  'EN': '英文'
}

目标语言 = {
  'CH': '中文',
  'EN': '英文',
  'TR': '土耳其语',
  'TH': '泰语',
  'PT': '葡萄牙语',
  'VN': '越南语',
  'IND': '印尼语',
  'ES': '西班牙语'
}
```

### 2.2 上下文提取配置

#### 基于后端ContextOptions定义
```python
class ContextOptions(BaseModel):
    game_info: bool = True        # 游戏信息
    comments: bool = True         # 单元格注释
    neighbors: bool = True        # 相邻单元格
    content_analysis: bool = True # 内容特征分析
    sheet_type: bool = True       # 表格类型
```

#### 前端配置UI
```javascript
contextConfig = {
  // 总开关
  extract_context: true,  // 启用/禁用所有上下文

  // 细粒度选项（仅当extract_context=true时生效）
  context_options: {
    game_info: true,        // 提取游戏信息上下文
    comments: true,         // 提取单元格注释
    neighbors: true,        // 提取相邻单元格信息
    content_analysis: true, // 分析内容特征
    sheet_type: true        // 识别表格类型
  }
}
```

### 2.3 任务拆分流程

#### 异步拆分机制（基于后端实现）
```python
# task_api.py 支持的流程：
1. POST /api/tasks/split - 提交拆分请求
2. GET /api/tasks/split/status/{session_id} - 查询进度
3. GET /api/tasks/status/{session_id} - 查询任务状态
4. GET /api/tasks/dataframe/{session_id} - 获取任务详情
```

---

## 3. 界面布局

### 3.1 页面结构
```
┌────────────────────────────────────────────────┐
│  [会话剩余: 7:45] ⚠️     配置翻译任务            │
│      Session: xxx-xxx-xxx                       │
├────────────────────────────────────────────────┤
│                                                 │
│  ┌─── 左侧配置区 ──────┐  ┌─── 右侧预览区 ──┐  │
│  │                     │  │                  │  │
│  │ 📍 语言设置         │  │ 📊 配置预览      │  │
│  │                     │  │                  │  │
│  │ 源语言:             │  │ 当前配置:        │  │
│  │ [自动检测 ▼]        │  │ • 源: 自动检测   │  │
│  │                     │  │ • 目标: 3种语言  │  │
│  │ 目标语言:           │  │                  │  │
│  │ ☑ 土耳其语(TR)     │  │ 预估影响:        │  │
│  │ ☑ 泰语(TH)         │  │ • 任务数: 2,568  │  │
│  │ ☑ 葡萄牙语(PT)     │  │ • 批次数: ~72   │  │
│  │ ☐ 越南语(VN)       │  │                  │  │
│  │ ☐ 印尼语(IND)      │  │ 性能提示:        │  │
│  │ ☐ 西班牙语(ES)     │  │ 开启上下文:      │  │
│  │                     │  │ • 质量: ⭐⭐⭐⭐⭐  │  │
│  │ ─────────────────   │  │ • 速度: ⭐⭐⭐     │  │
│  │                     │  │                  │  │
│  │ 🔧 上下文提取       │  │ 关闭上下文:      │  │
│  │                     │  │ • 质量: ⭐⭐⭐     │  │
│  │ [●] 启用上下文      │  │ • 速度: ⭐⭐⭐⭐⭐  │  │
│  │                     │  │                  │  │
│  │ 选择提取内容:       │  │ 💡 建议:         │  │
│  │ ☑ 游戏信息         │  │ 小文件建议开启    │  │
│  │ ☑ 单元格注释       │  │ 所有上下文选项    │  │
│  │ ☑ 相邻单元格       │  │                  │  │
│  │ ☑ 内容特征         │  │                  │  │
│  │ ☑ 表格类型         │  │                  │  │
│  │                     │  │                  │  │
│  └────────────────────┘  └──────────────────┘  │
│                                                 │
│           [重置] [开始拆分任务 →]               │
│                                                 │
│  ┌───────────────────────────────────────┐     │
│  │ 拆分进度 (点击拆分后显示)               │     │
│  │                                         │     │
│  │ ▓▓▓▓▓▓▓▓▓░░░░░ 75%                    │     │
│  │ 正在处理 Sheet 9/12...                  │     │
│  │                                         │     │
│  └───────────────────────────────────────┘     │
│                                                 │
│  ┌───────────────────────────────────────┐     │
│  │ 拆分结果 (完成后显示)                   │     │
│  │                                         │     │
│  │ ✅ 拆分完成！                          │     │
│  │                                         │     │
│  │ 统计信息:                              │     │
│  │ • 总任务数: 2,568                      │     │
│  │ • 总批次数: 72                         │     │
│  │ • 总字符数: 135,702                    │     │
│  │                                         │     │
│  │ 语言分布:                              │     │
│  │ • TR: 24批次，856任务                  │     │
│  │ • TH: 24批次，856任务                  │     │
│  │ • PT: 24批次，856任务                  │     │
│  │                                         │     │
│  │ [查看详情] [导出Excel] [开始翻译 →]    │     │
│  └───────────────────────────────────────┘     │
│                                                 │
└────────────────────────────────────────────────┘
```

### 3.2 响应式设计

#### 桌面端 (≥1024px)
- 左右分栏布局（60% + 40%）
- 配置区和预览区并排显示

#### 平板端 (768-1023px)
- 左右分栏调整为70% + 30%
- 预览区内容精简

#### 移动端 (<768px)
- 单列布局
- 预览区折叠到配置区下方
- 底部固定主操作按钮

---

## 4. 交互设计

### 4.1 配置交互

#### 语言选择
```javascript
// 目标语言至少选择1个
validation = {
  target_langs: {
    min: 1,
    max: 6,
    error: "请至少选择一个目标语言"
  }
}

// 选择变化时实时更新预览
onLanguageChange = () => {
  updateTaskEstimation();
  updatePerformanceHint();
}
```

#### 上下文提取交互
```javascript
// Toggle总开关逻辑
onContextToggle = (enabled) => {
  if (!enabled) {
    // 关闭时禁用所有子选项
    disableAllContextOptions();
    showPerformanceBoost(); // 显示速度提升提示
  } else {
    // 开启时恢复子选项
    enableContextOptions();
    showQualityImprovement(); // 显示质量提升提示
  }
}
```

### 4.2 拆分任务流程

#### 状态流转
```
1. 配置状态
   - 用户选择语言和选项
   - 实时预览影响

2. 提交拆分
   - 验证配置
   - 显示确认对话框
   - POST /api/tasks/split

3. 拆分中（异步）
   - 轮询进度 GET /api/tasks/split/status/{session_id}
   - 更新进度条
   - 显示当前处理的Sheet

4. 拆分完成
   - 显示统计结果
   - 启用"开始翻译"按钮
   - 可导出任务详情
```

#### 进度轮询机制
```javascript
async function pollSplitProgress(sessionId) {
  const interval = setInterval(async () => {
    const response = await fetch(`/api/tasks/split/status/${sessionId}`);
    const data = await response.json();

    updateProgress(data.progress);
    updateMessage(data.message);

    if (data.status === 'completed' || data.status === 'failed') {
      clearInterval(interval);
      handleSplitComplete(data);
    }
  }, 1000); // 每秒轮询一次
}
```

---

## 5. API集成

### 5.1 提交拆分任务

```javascript
// POST /api/tasks/split
async function splitTasks(config) {
  const request = {
    session_id: getCurrentSessionId(),
    source_lang: config.sourceLang || null, // null = auto-detect
    target_langs: config.targetLangs,
    extract_context: config.extractContext,
    context_options: config.extractContext ? config.contextOptions : null
  };

  const response = await fetch('/api/tasks/split', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });

  return response.json();
}
```

### 5.2 查询拆分进度

```javascript
// GET /api/tasks/split/status/{session_id}
async function getSplitStatus(sessionId) {
  const response = await fetch(`/api/tasks/split/status/${sessionId}`);
  const data = await response.json();

  // 返回数据结构（基于后端）
  // {
  //   status: 'processing' | 'completed' | 'failed',
  //   progress: 0-100,
  //   message: '当前处理信息',
  //   total_sheets: 12,
  //   processed_sheets: 9,
  //   task_count?: 2568,        // 完成时返回
  //   batch_count?: 72,         // 完成时返回
  //   batch_distribution?: {...} // 完成时返回
  // }

  return data;
}
```

### 5.3 获取任务状态

```javascript
// GET /api/tasks/status/{session_id}
async function getTaskStatus(sessionId) {
  const response = await fetch(`/api/tasks/status/${sessionId}`);
  return response.json();

  // 返回结构：
  // {
  //   status: 'ready' | 'splitting' | 'split_failed',
  //   has_tasks: true,
  //   task_count: 2568,
  //   batch_count: 72
  // }
}
```

### 5.4 导出任务DataFrame

```javascript
// GET /api/tasks/export/{session_id}
async function exportTasks(sessionId) {
  const response = await fetch(`/api/tasks/export/${sessionId}`);

  if (response.ok) {
    const blob = await response.blob();
    downloadFile(blob, `tasks_${sessionId}.xlsx`);
  }
}
```

---

## 6. 状态管理

### 6.1 页面状态
```javascript
pageState = {
  // Session信息
  sessionId: 'xxx-xxx-xxx',

  // 配置状态
  config: {
    sourceLang: null,      // null = auto-detect
    targetLangs: [],       // ['TR', 'TH', 'PT']
    extractContext: true,
    contextOptions: {
      game_info: true,
      comments: true,
      neighbors: true,
      content_analysis: true,
      sheet_type: true
    }
  },

  // 拆分状态
  splitStatus: 'idle', // idle | splitting | completed | failed
  splitProgress: 0,
  splitMessage: '',

  // 拆分结果
  splitResult: {
    task_count: 0,
    batch_count: 0,
    batch_distribution: {},
    statistics: {}
  },

  // UI状态
  isSubmitting: false,
  error: null
}
```

### 6.2 数据持久化
```javascript
// 保存配置到LocalStorage
function saveConfig() {
  localStorage.setItem('taskConfig', JSON.stringify({
    sourceLang: pageState.config.sourceLang,
    targetLangs: pageState.config.targetLangs,
    extractContext: pageState.config.extractContext,
    contextOptions: pageState.config.contextOptions
  }));
}

// 恢复上次配置
function loadLastConfig() {
  const saved = localStorage.getItem('taskConfig');
  if (saved) {
    const config = JSON.parse(saved);
    // 应用到当前页面
    applyConfig(config);
  }
}
```

### 6.3 会话超时监控
```javascript
// 继续监控会话剩余时间
class SessionTimeoutMonitor {
  constructor(sessionId) {
    const session = JSON.parse(localStorage.getItem('currentSession'));
    this.expiresAt = session.expiresAt;
    this.startMonitoring();
  }

  startMonitoring() {
    this.updateInterval = setInterval(() => {
      const remaining = this.expiresAt - Date.now();

      if (remaining <= 0) {
        this.handleExpired();
      } else if (remaining <= 30 * 60 * 1000) { // 30分钟警告
        this.showWarning(remaining);
      }

      this.updateDisplay(remaining);
    }, 60000); // 每分钟更新
  }

  updateDisplay(remaining) {
    const hours = Math.floor(remaining / 3600000);
    const minutes = Math.floor((remaining % 3600000) / 60000);

    const display = document.getElementById('session-timer');
    if (display) {
      display.textContent = `会话剩余: ${hours}:${minutes.toString().padStart(2, '0')}`;

      // 临期警告样式
      if (remaining < 30 * 60 * 1000) {
        display.classList.add('warning');
        display.innerHTML = `⚠️ ${display.textContent}`;
      }
    }
  }

  showWarning(remaining) {
    const minutes = Math.floor(remaining / 60000);
    showAlert({
      type: 'warning',
      title: '会话即将过期',
      message: `您的翻译会话将在 ${minutes} 分钟后过期，请尽快完成配置并开始翻译`,
      actions: [
        { label: '立即开始翻译', primary: true },
        { label: '知道了' }
      ]
    });
  }

  handleExpired() {
    clearInterval(this.updateInterval);
    showError({
      title: '会话已过期',
      message: '您的翻译数据已被清除，请重新上传文件',
      blocking: true,
      action: () => window.location.hash = '#/create'
    });
  }
}
```

---

## 7. 性能优化

### 7.1 实时预览优化
```javascript
// 使用防抖避免频繁计算
const updatePreview = debounce(() => {
  calculateTaskEstimation();
  updatePerformanceHints();
}, 300);
```

### 7.2 进度轮询优化
```javascript
// 动态调整轮询频率
function adaptivePolling(progress) {
  if (progress < 30) return 2000;  // 初期2秒
  if (progress < 70) return 1000;  // 中期1秒
  return 500;                      // 后期0.5秒
}
```

---

## 8. 错误处理

### 8.1 常见错误场景

| 错误类型 | 用户提示 | 恢复操作 |
|---------|---------|---------|
| 未选择目标语言 | "请至少选择一个目标语言" | 高亮语言选择区 |
| Session过期 | "会话已过期，请重新上传文件" | 跳转到上传页 |
| 拆分失败 | "任务拆分失败：{原因}" | 显示重试按钮 |
| 网络错误 | "网络连接失败，请检查网络" | 自动重试3次 |

### 8.2 错误恢复策略
```javascript
async function handleSplitError(error) {
  if (error.code === 'SESSION_NOT_FOUND') {
    // Session不存在，引导重新上传
    showError('文件数据已失效，请重新上传');
    setTimeout(() => navigateTo('/upload'), 3000);
  } else if (error.code === 'NETWORK_ERROR') {
    // 网络错误，自动重试
    retryCount++;
    if (retryCount < 3) {
      await delay(1000 * retryCount);
      retrySpilt();
    }
  } else {
    // 其他错误，显示具体信息
    showError(error.message);
  }
}
```

---

## 9. 测试要点

### 9.1 功能测试
- [ ] 源语言选择（自动检测/手动选择）
- [ ] 多目标语言选择
- [ ] 上下文提取开关切换
- [ ] 细粒度上下文选项配置
- [ ] 拆分任务提交
- [ ] 进度实时更新
- [ ] 结果正确显示
- [ ] 任务导出功能

### 9.2 边界测试
- [ ] 未选择目标语言时的验证
- [ ] Session过期处理
- [ ] 拆分超时处理（大文件）
- [ ] 网络中断恢复

### 9.3 性能测试
- [ ] 大文件拆分（>1000任务）
- [ ] 多语言并发拆分
- [ ] 进度更新流畅性

---

## 10. 实现注意事项

### 10.1 必须遵循的后端限制
1. source_lang可为null（自动检测）
2. target_langs必须是数组
3. context_options仅在extract_context=true时有效
4. 拆分是异步过程，需要轮询状态

### 10.2 前端可优化项
1. 配置记忆和恢复
2. 实时预览计算（纯前端）
3. 性能提示（基于经验值）
4. 智能默认配置

### 10.3 不要实现的功能
基于后端限制：
1. ❌ 自定义批次大小
2. ❌ 自定义Prompt模板
3. ❌ 实时预估成本（后端无此接口）
4. ❌ 任务优先级设置

---

**文档版本**: 1.0
**基于后端**: backend_v2/api/task_api.py
**创建日期**: 2025-10-04
**作者**: Frontend Team