# Translation Hub - 前端设计规划文档

> 版本: v2.0
> 更新时间: 2025-10-03
> 技术栈: 纯 HTML5 + CSS3 + Vanilla JavaScript (无框架)

---

## 📋 目录

1. [项目概述](#项目概述)
2. [技术选型](#技术选型)
3. [目录结构](#目录结构)
4. [页面架构](#页面架构)
5. [路由设计](#路由设计)
6. [页面详细设计](#页面详细设计)
7. [组件设计](#组件设计)
8. [状态管理](#状态管理)
9. [API 集成](#api-集成)
10. [交互流程](#交互流程)

---

## 项目概述

### 产品定位
Translation Hub 是一个专业的 Excel 文件翻译系统，为游戏本地化团队提供高效的批量翻译工作流。

### 核心功能
- 📤 Excel 文件上传与智能分析
- ⚙️ 灵活的翻译任务配置
- 🚀 实时翻译执行与进度监控
- 📊 详细的统计分析与成本核算
- 📥 翻译结果下载与历史管理

### 设计原则
1. **零依赖**: 不使用任何前端框架和构建工具
2. **原生优先**: 使用现代浏览器原生 API
3. **渐进增强**: 基础功能优先，高级特性渐进
4. **性能至上**: 最小化资源加载，优化运行时性能
5. **可维护性**: 模块化设计，清晰的代码组织

---

## 技术选型

### 核心技术
```yaml
HTML5:
  - 语义化标签
  - 原生表单验证
  - 拖拽 API (Drag & Drop)
  - File API

CSS3:
  - CSS Grid / Flexbox 布局
  - CSS Variables (设计系统)
  - CSS Animations (动画)
  - Media Queries (响应式)

JavaScript (ES6+):
  - 原生 Fetch API
  - WebSocket API
  - LocalStorage API
  - Custom Elements (Web Components)
  - ES6 Modules
```

### 不使用的技术
❌ React / Vue / Angular
❌ SASS / LESS
❌ Webpack / Vite
❌ TypeScript
❌ jQuery

### 为什么选择原生技术？
✅ **零构建时间** - 直接运行，无需编译
✅ **极小体积** - 无框架开销
✅ **长期稳定** - 无版本升级烦恼
✅ **学习成本低** - 标准 Web 技术
✅ **性能最优** - 无虚拟 DOM 开销

---

## 目录结构

```
frontend_v2/
├── .gitignore                    # Git 忽略文件
├── FRONTEND_DESIGN.md            # 本文档
├── README.md                     # 项目说明
│
├── index.html                    # 主入口文件 (SPA)
│
├── assets/                       # 静态资源
│   ├── images/                   # 图片资源
│   │   ├── logo.svg
│   │   ├── icons/
│   │   └── illustrations/
│   └── fonts/                    # 字体文件 (可选)
│
├── css/                          # 样式文件
│   ├── design-tokens.css         # 设计系统变量
│   ├── base.css                  # 基础样式 (reset + base)
│   ├── layout.css                # 布局样式
│   ├── components.css            # 组件样式
│   ├── pages.css                 # 页面样式
│   └── utilities.css             # 工具类
│
├── js/                           # JavaScript 文件
│   ├── main.js                   # 主入口
│   ├── router.js                 # 路由管理器
│   ├── store.js                  # 状态管理
│   ├── api.js                    # API 封装
│   │
│   ├── utils/                    # 工具函数
│   │   ├── dom.js                # DOM 操作
│   │   ├── format.js             # 格式化工具
│   │   ├── validate.js           # 表单验证
│   │   └── animation.js          # 动画工具
│   │
│   ├── components/               # 可复用组件
│   │   ├── Navbar.js             # 导航栏
│   │   ├── Sidebar.js            # 侧边栏
│   │   ├── StatusBar.js          # 状态栏
│   │   ├── Toast.js              # 通知组件
│   │   ├── Modal.js              # 模态框
│   │   ├── ProgressBar.js        # 进度条
│   │   ├── Card.js               # 卡片组件
│   │   ├── Button.js             # 按钮组件
│   │   └── FileUpload.js         # 文件上传
│   │
│   └── pages/                    # 页面组件
│       ├── ProjectCreate.js      # 页面1: 项目创建
│       ├── TaskConfig.js         # 页面2: 任务配置
│       ├── TranslationExec.js    # 页面3: 翻译执行
│       ├── ResultExport.js       # 页面4: 结果导出
│       └── HistoryManager.js     # 页面5: 历史管理
│
└── test_pages/                   # 测试页面 (保留)
    ├── 1_upload_analyze.html
    ├── 2_task_split.html
    ├── 3_execute_translation.html
    └── 4_download_export.html
```

---

## 页面架构

### 整体架构模式

**单页应用 (SPA)** - 使用 Hash 路由实现页面切换

```
┌─────────────────────────────────────────────────────────┐
│                     index.html                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │            <div id="app">                        │   │
│  │  ┌───────────────────────────────────────────┐  │   │
│  │  │  Navbar (全局导航栏)                       │  │   │
│  │  └───────────────────────────────────────────┘  │   │
│  │  ┌────────┬──────────────────────────────────┐  │   │
│  │  │Sidebar │  <div id="page-container">       │  │   │
│  │  │(侧边栏)│    (动态加载页面内容)             │  │   │
│  │  │        │                                   │  │   │
│  │  └────────┴──────────────────────────────────┘  │   │
│  │  ┌───────────────────────────────────────────┐  │   │
│  │  │  StatusBar (状态栏)                        │  │   │
│  │  └───────────────────────────────────────────┘  │   │
│  │            </div>                                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  <script type="module" src="js/main.js"></script>      │
└─────────────────────────────────────────────────────────┘
```

### 布局系统

采用 **CSS Grid + Flexbox** 混合布局

```css
/* 主布局 */
#app {
  display: grid;
  grid-template-areas:
    "navbar navbar"
    "sidebar main"
    "statusbar statusbar";
  grid-template-rows: 64px 1fr 48px;
  grid-template-columns: 240px 1fr;
  height: 100vh;
}

/* 响应式 */
@media (max-width: 768px) {
  #app {
    grid-template-areas:
      "navbar"
      "main"
      "statusbar";
    grid-template-columns: 1fr;
  }
}
```

---

## 路由设计

### 路由表

| 路由路径 | 页面组件 | 页面名称 | 功能描述 |
|---------|---------|---------|---------|
| `#/` 或 `#/create` | ProjectCreate | 项目创建 | 上传 Excel 文件并分析 |
| `#/config` | TaskConfig | 任务配置 | 配置语言和上下文提取选项 |
| `#/execute` | TranslationExec | 翻译执行 | 执行翻译并实时监控进度 |
| `#/result` | ResultExport | 结果导出 | 查看统计并下载结果 |
| `#/history` | HistoryManager | 历史管理 | 管理历史翻译项目 |

### 路由实现

```javascript
// js/router.js
class Router {
  constructor() {
    this.routes = new Map();
    this.currentPage = null;
  }

  // 注册路由
  register(path, pageComponent) {
    this.routes.set(path, pageComponent);
  }

  // 导航到指定路由
  navigate(path) {
    window.location.hash = path;
  }

  // 初始化路由监听
  init() {
    window.addEventListener('hashchange', () => this.handleRoute());
    this.handleRoute(); // 初始加载
  }

  // 处理路由变化
  handleRoute() {
    const hash = window.location.hash.slice(1) || '/create';
    const pageComponent = this.routes.get(hash);

    if (pageComponent) {
      this.renderPage(pageComponent);
    } else {
      this.navigate('/create'); // 默认路由
    }
  }

  // 渲染页面
  renderPage(pageComponent) {
    const container = document.getElementById('page-container');
    if (this.currentPage && this.currentPage.destroy) {
      this.currentPage.destroy(); // 清理旧页面
    }
    this.currentPage = new pageComponent(container);
    this.currentPage.render();
  }
}
```

### 路由守卫

```javascript
// 检查 Session 是否存在
function requireSession(next) {
  const sessionId = store.get('currentSession');
  if (!sessionId) {
    toast.warning('请先创建项目');
    router.navigate('/create');
    return false;
  }
  return next();
}

// 使用示例
router.register('/config', () => requireSession(() => new TaskConfig()));
```

---

## 页面详细设计

### 页面1: 项目创建页 (ProjectCreate)

**路由**: `#/create`
**文件**: `js/pages/ProjectCreate.js`

#### 功能模块

1. **文件上传区**
   - 支持拖拽上传
   - 文件格式验证 (.xlsx, .xls)
   - 文件大小限制 (100MB)
   - 上传进度显示

2. **元数据表单**
   - 游戏名称 (可选)
   - 版本号 (可选)
   - 项目备注 (可选)

3. **分析结果展示**
   - Session ID 显示与复制
   - 文件统计信息
   - 任务类型分布图表
   - 继续配置按钮

#### 数据流

```
用户操作                API 调用                    状态更新
────────                ────────                    ────────
选择文件
  ↓
点击上传               POST /api/analyze/upload
  ↓                           ↓
显示进度               接收响应 (Session ID)
  ↓                           ↓
分析完成               GET /api/analyze/status/:id
  ↓                           ↓
显示结果               保存 Session 到 Store        更新 UI
  ↓
点击继续               router.navigate('/config')   跳转配置页
```

#### 关键代码结构

```javascript
class ProjectCreate {
  constructor(container) {
    this.container = container;
    this.file = null;
    this.sessionId = null;
  }

  render() {
    this.container.innerHTML = this.template();
    this.attachEvents();
  }

  template() {
    return `
      <div class="page-create">
        <h1>🚀 开始新翻译项目</h1>

        <div class="upload-zone" id="upload-zone">
          <p>🖱️ 拖拽Excel文件到这里或点击选择文件</p>
          <input type="file" id="file-input" accept=".xlsx,.xls">
        </div>

        <form id="metadata-form">
          <input type="text" name="game_name" placeholder="游戏名称">
          <input type="text" name="version" placeholder="版本号">
          <textarea name="notes" placeholder="项目备注"></textarea>
        </form>

        <button id="upload-btn">上传并分析</button>

        <div id="analysis-result" style="display:none;">
          <!-- 动态生成分析结果 -->
        </div>
      </div>
    `;
  }

  attachEvents() {
    // 拖拽上传
    const zone = document.getElementById('upload-zone');
    zone.addEventListener('drop', (e) => this.handleDrop(e));
    zone.addEventListener('dragover', (e) => e.preventDefault());

    // 点击上传
    const input = document.getElementById('file-input');
    input.addEventListener('change', (e) => this.handleFileSelect(e));

    // 提交上传
    const btn = document.getElementById('upload-btn');
    btn.addEventListener('click', () => this.uploadFile());
  }

  async uploadFile() {
    const formData = new FormData();
    formData.append('file', this.file);
    // ... API 调用
  }
}
```

---

### 页面2: 任务配置页 (TaskConfig)

**路由**: `#/config`
**文件**: `js/pages/TaskConfig.js`

#### 功能模块

1. **语言配置**
   - 源语言选择 (下拉框)
   - 目标语言多选 (复选框组)
   - 语言添加/删除

2. **上下文提取配置**
   - 总开关 (Toggle)
   - 细粒度选项 (复选框组)
     - ☑️ 游戏信息
     - ☑️ 单元格注释
     - ☑️ 相邻单元格
     - ☑️ 内容特征
     - ☑️ 表格类型

3. **实时预览**
   - 任务统计 (总数/批次/字符)
   - 预估耗时
   - 预估成本
   - 语言批次分布
   - 任务类型分布

4. **高级选项** (可折叠)
   - 批次大小配置
   - 并发数设置
   - 自定义 Prompt 模板

#### 数据流

```
用户操作                API 调用                    状态更新
────────                ────────                    ────────
选择目标语言
  ↓
实时计算               无 (前端计算)                更新预览面板
  ↓
切换上下文选项
  ↓
更新耗时估算           无 (前端计算)                更新预估信息
  ↓
点击拆解任务           POST /api/tasks/split
  ↓                           ↓
显示进度               WebSocket /ws/split/:id     实时更新进度
  ↓                           ↓
拆解完成               GET /api/tasks/status/:id   更新任务统计
  ↓
点击开始翻译           router.navigate('/execute')  跳转执行页
```

#### 组件设计

```javascript
class TaskConfig {
  constructor(container) {
    this.container = container;
    this.config = {
      source_lang: 'EN',
      target_langs: [],
      extract_context: true,
      context_options: {
        game_info: true,
        comments: true,
        neighbors: true,
        content_analysis: true,
        sheet_type: true
      }
    };
  }

  render() {
    this.container.innerHTML = `
      <div class="page-config">
        <div class="config-panel">
          ${this.renderLanguageConfig()}
          ${this.renderContextConfig()}
          ${this.renderAdvancedOptions()}
        </div>

        <div class="preview-panel">
          ${this.renderPreview()}
        </div>

        <button id="split-btn">开始拆解任务</button>
      </div>
    `;
    this.attachEvents();
  }

  renderLanguageConfig() {
    return `
      <section class="language-config">
        <h2>🌍 语言设置</h2>
        <label>
          源语言:
          <select id="source-lang">
            <option value="EN">英文 (EN)</option>
            <option value="CH">中文 (CH)</option>
          </select>
        </label>

        <fieldset>
          <legend>目标语言 (多选):</legend>
          <label><input type="checkbox" value="TR"> 土耳其语 (TR)</label>
          <label><input type="checkbox" value="TH"> 泰语 (TH)</label>
          <label><input type="checkbox" value="PT"> 葡萄牙语 (PT)</label>
          <label><input type="checkbox" value="VN"> 越南语 (VN)</label>
        </fieldset>
      </section>
    `;
  }

  renderContextConfig() {
    return `
      <section class="context-config">
        <h2>🧠 上下文提取配置</h2>
        <label class="toggle">
          <input type="checkbox" id="context-toggle" checked>
          <span>启用上下文提取</span>
        </label>

        <div id="context-options">
          <label><input type="checkbox" checked> 游戏信息</label>
          <label><input type="checkbox" checked> 单元格注释</label>
          <label><input type="checkbox" checked> 相邻单元格</label>
          <label><input type="checkbox" checked> 内容特征</label>
          <label><input type="checkbox" checked> 表格类型</label>
        </div>

        <p class="hint">💡 大文件可关闭以提升5-10倍速度</p>
      </section>
    `;
  }

  async splitTasks() {
    const sessionId = store.get('currentSession');
    const response = await api.post('/api/tasks/split', {
      session_id: sessionId,
      ...this.config
    });
    // 开始轮询进度
    this.pollSplitProgress(sessionId);
  }
}
```

---

### 页面3: 翻译执行页 (TranslationExec)

**路由**: `#/execute`
**文件**: `js/pages/TranslationExec.js`

#### 功能模块

1. **LLM 配置面板**
   - LLM 引擎选择 (下拉)
   - 并发数设置 (滑块)

2. **控制面板**
   - 开始/暂停/恢复/停止按钮
   - 手动刷新状态按钮

3. **实时进度仪表盘**
   - WebSocket 连接状态指示器
   - 总体进度条
   - 统计卡片 (已完成/执行中/待处理/失败)
   - 语言进度分布
   - 实时统计 (耗时/速度/Token)

4. **任务流视图**
   - Tab 切换 (全部/执行中/已完成/失败/待处理)
   - 任务卡片列表 (虚拟滚动)
   - 任务详情展开

#### 数据流

```
用户操作                API 调用                    状态更新
────────                ────────                    ────────
选择 LLM 引擎
  ↓
点击开始翻译           POST /api/execute/start
  ↓                           ↓
建立 WebSocket         WebSocket /ws/progress/:id
  ↓                           ↓
接收实时进度           持续推送进度数据             实时更新 UI
  ↓                           ↓
用户点击暂停           POST /api/execute/pause
  ↓                           ↓
暂停成功               停止推送                     更新按钮状态
  ↓
点击恢复               POST /api/execute/resume
  ↓                           ↓
恢复翻译               继续推送                     更新 UI
  ↓
翻译完成               WebSocket 关闭               显示完成动画
  ↓
自动跳转               router.navigate('/result')   跳转结果页
```

#### WebSocket 集成

```javascript
class TranslationExec {
  constructor(container) {
    this.container = container;
    this.ws = null;
    this.progressData = {
      total: 0,
      completed: 0,
      processing: 0,
      pending: 0,
      failed: 0,
      completion_rate: 0
    };
  }

  connectWebSocket(sessionId) {
    const wsUrl = `ws://localhost:8013/ws/progress/${sessionId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.updateConnectionStatus(true);
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'progress') {
        this.updateProgress(data.data);
      }
    };

    this.ws.onerror = () => {
      this.updateConnectionStatus(false);
      this.fallbackToPolling(sessionId); // 降级到轮询
    };

    this.ws.onclose = () => {
      this.updateConnectionStatus(false);
    };
  }

  updateProgress(data) {
    this.progressData = data;

    // 更新进度条
    const progressBar = document.getElementById('progress-bar');
    progressBar.style.width = `${data.completion_rate}%`;
    progressBar.textContent = `${data.completion_rate.toFixed(1)}%`;

    // 更新统计卡片
    document.getElementById('stat-completed').textContent = data.completed;
    document.getElementById('stat-pending').textContent = data.pending;
    document.getElementById('stat-failed').textContent = data.failed;

    // 检查是否完成
    if (data.completed === data.total) {
      this.showCompletionAnimation();
      setTimeout(() => router.navigate('/result'), 3000);
    }
  }

  async fallbackToPolling(sessionId) {
    // WebSocket 失败时降级到轮询
    this.pollingInterval = setInterval(async () => {
      const status = await api.get(`/api/execute/status/${sessionId}`);
      this.updateProgress(status.progress);
    }, 2000);
  }
}
```

---

### 页面4: 结果导出页 (ResultExport)

**路由**: `#/result`
**文件**: `js/pages/ResultExport.js`

#### 功能模块

1. **顶部摘要卡片**
   - 完成状态图标
   - 时间信息 (开始/结束/耗时)
   - 主下载按钮

2. **统计看板**
   - 任务统计 (总数/完成/失败/成功率)
   - 成本统计 (总计/各 LLM 分项)
   - 性能统计 (速度/Token/字符数)

3. **语言维度分析**
   - 各语言翻译详情
   - 进度条 + 统计数据
   - 成本/耗时分解

4. **任务类型分析**
   - 柱状图对比
   - 耗时/成本分析
   - 优化建议

5. **下载中心**
   - 翻译结果文件
   - 任务详情表
   - PDF 报告

#### 数据可视化

使用原生 Canvas API 绘制图表

```javascript
class ChartRenderer {
  // 绘制柱状图
  static drawBarChart(canvas, data) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const barWidth = width / data.length / 1.5;
    const maxValue = Math.max(...data.map(d => d.value));

    data.forEach((item, index) => {
      const barHeight = (item.value / maxValue) * height * 0.8;
      const x = (width / data.length) * index + barWidth / 2;
      const y = height - barHeight;

      // 绘制柱子
      ctx.fillStyle = item.color || '#4F46E5';
      ctx.fillRect(x, y, barWidth, barHeight);

      // 绘制标签
      ctx.fillStyle = '#1F2937';
      ctx.textAlign = 'center';
      ctx.fillText(item.label, x + barWidth / 2, height - 5);
      ctx.fillText(item.value, x + barWidth / 2, y - 5);
    });
  }

  // 绘制饼图
  static drawPieChart(canvas, data) {
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) * 0.8;

    let currentAngle = -Math.PI / 2;
    const total = data.reduce((sum, item) => sum + item.value, 0);

    data.forEach(item => {
      const sliceAngle = (item.value / total) * Math.PI * 2;

      // 绘制扇形
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
      ctx.closePath();
      ctx.fillStyle = item.color;
      ctx.fill();

      currentAngle += sliceAngle;
    });
  }
}
```

---

### 页面5: 历史管理页 (HistoryManager)

**路由**: `#/history`
**文件**: `js/pages/HistoryManager.js`

#### 功能模块

1. **搜索&筛选栏**
   - 关键词搜索 (Session ID/文件名)
   - 状态筛选 (全部/已完成/进行中/失败)
   - 语言筛选
   - 时间范围筛选
   - 排序选项

2. **会话列表**
   - 表格视图
   - 分页控制
   - 批量选择
   - 行内快捷操作

3. **批量操作**
   - 批量下载
   - 批量删除
   - 汇总统计

4. **统计概览**
   - 月度统计卡片
   - 常用语言对分析
   - 详细报表链接

#### 列表渲染优化

```javascript
class HistoryManager {
  constructor(container) {
    this.container = container;
    this.sessions = [];
    this.filteredSessions = [];
    this.currentPage = 1;
    this.pageSize = 20;
  }

  async loadSessions() {
    const response = await api.get('/api/sessions');
    this.sessions = response.sessions;
    this.applyFilters();
    this.renderTable();
  }

  applyFilters() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const statusFilter = document.getElementById('status-filter').value;

    this.filteredSessions = this.sessions.filter(session => {
      const matchSearch = session.session_id.includes(searchTerm) ||
                         session.filename.toLowerCase().includes(searchTerm);
      const matchStatus = !statusFilter || session.status === statusFilter;
      return matchSearch && matchStatus;
    });

    this.renderTable();
  }

  renderTable() {
    const start = (this.currentPage - 1) * this.pageSize;
    const end = start + this.pageSize;
    const pageSessions = this.filteredSessions.slice(start, end);

    const tbody = document.getElementById('sessions-tbody');
    tbody.innerHTML = pageSessions.map(session => `
      <tr>
        <td><input type="checkbox" value="${session.session_id}"></td>
        <td>${session.session_id}</td>
        <td>${session.filename}</td>
        <td>${this.renderStatusBadge(session.status)}</td>
        <td>${session.task_count}</td>
        <td>¥${session.total_cost.toFixed(2)}</td>
        <td>${session.languages.join(', ')}</td>
        <td>${this.formatDate(session.created_at)}</td>
        <td>${this.renderActions(session)}</td>
      </tr>
    `).join('');

    this.renderPagination();
  }

  renderStatusBadge(status) {
    const badges = {
      completed: '<span class="badge badge-success">✅ 已完成</span>',
      processing: '<span class="badge badge-info">⚡ 进行中</span>',
      failed: '<span class="badge badge-error">❌ 失败</span>'
    };
    return badges[status] || status;
  }

  renderActions(session) {
    if (session.status === 'completed') {
      return `
        <button onclick="viewSession('${session.session_id}')">👁️ 查看</button>
        <button onclick="downloadSession('${session.session_id}')">📥 下载</button>
        <button onclick="deleteSession('${session.session_id}')">🗑️ 删除</button>
      `;
    } else if (session.status === 'processing') {
      return `
        <button onclick="continueSession('${session.session_id}')">▶️ 继续</button>
        <button onclick="pauseSession('${session.session_id}')">⏸ 暂停</button>
      `;
    }
    // ... 其他状态
  }
}
```

---

## 组件设计

### 组件化原则

使用 **ES6 Class** 实现可复用组件，所有组件继承自 `BaseComponent`

```javascript
// js/components/BaseComponent.js
class BaseComponent {
  constructor(container) {
    this.container = container;
    this.state = {};
  }

  setState(newState) {
    this.state = { ...this.state, ...newState };
    this.render();
  }

  render() {
    throw new Error('render() must be implemented');
  }

  destroy() {
    this.container.innerHTML = '';
  }
}
```

### 核心组件列表

#### 1. Toast 通知组件

```javascript
// js/components/Toast.js
class Toast {
  static show(message, type = 'info', duration = 5000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${this.getIcon(type)}</span>
      <span class="toast-message">${message}</span>
      <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    document.body.appendChild(toast);

    // 自动消失
    setTimeout(() => toast.remove(), duration);

    // 入场动画
    setTimeout(() => toast.classList.add('toast-show'), 10);
  }

  static getIcon(type) {
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };
    return icons[type] || icons.info;
  }

  static success(msg) { this.show(msg, 'success'); }
  static error(msg) { this.show(msg, 'error'); }
  static warning(msg) { this.show(msg, 'warning'); }
  static info(msg) { this.show(msg, 'info'); }
}
```

#### 2. Modal 模态框组件

```javascript
// js/components/Modal.js
class Modal {
  static show(options) {
    const { title, content, onConfirm, onCancel } = options;

    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal">
        <div class="modal-header">
          <h3>${title}</h3>
          <button class="modal-close">×</button>
        </div>
        <div class="modal-body">${content}</div>
        <div class="modal-footer">
          <button class="btn btn-secondary" id="modal-cancel">取消</button>
          <button class="btn btn-primary" id="modal-confirm">确定</button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // 事件绑定
    modal.querySelector('.modal-close').onclick = () => {
      modal.remove();
      onCancel && onCancel();
    };

    modal.querySelector('#modal-cancel').onclick = () => {
      modal.remove();
      onCancel && onCancel();
    };

    modal.querySelector('#modal-confirm').onclick = () => {
      modal.remove();
      onConfirm && onConfirm();
    };

    // 点击遮罩关闭
    modal.onclick = (e) => {
      if (e.target === modal) {
        modal.remove();
        onCancel && onCancel();
      }
    };
  }

  static confirm(title, message) {
    return new Promise((resolve) => {
      this.show({
        title,
        content: message,
        onConfirm: () => resolve(true),
        onCancel: () => resolve(false)
      });
    });
  }
}
```

#### 3. ProgressBar 进度条组件

```javascript
// js/components/ProgressBar.js
class ProgressBar extends BaseComponent {
  constructor(container, options = {}) {
    super(container);
    this.percentage = options.percentage || 0;
    this.showLabel = options.showLabel !== false;
    this.color = options.color || 'primary';
  }

  render() {
    this.container.innerHTML = `
      <div class="progress-bar">
        <div class="progress-fill progress-${this.color}"
             style="width: ${this.percentage}%">
          ${this.showLabel ? `${this.percentage.toFixed(1)}%` : ''}
        </div>
      </div>
    `;
  }

  setProgress(percentage) {
    this.percentage = Math.min(100, Math.max(0, percentage));
    const fill = this.container.querySelector('.progress-fill');
    fill.style.width = `${this.percentage}%`;
    if (this.showLabel) {
      fill.textContent = `${this.percentage.toFixed(1)}%`;
    }
  }

  animate(targetPercentage, duration = 300) {
    const start = this.percentage;
    const diff = targetPercentage - start;
    const startTime = performance.now();

    const updateProgress = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const currentPercentage = start + diff * progress;

      this.setProgress(currentPercentage);

      if (progress < 1) {
        requestAnimationFrame(updateProgress);
      }
    };

    requestAnimationFrame(updateProgress);
  }
}
```

#### 4. FileUpload 文件上传组件

```javascript
// js/components/FileUpload.js
class FileUpload extends BaseComponent {
  constructor(container, options = {}) {
    super(container);
    this.accept = options.accept || '.xlsx,.xls';
    this.maxSize = options.maxSize || 100 * 1024 * 1024; // 100MB
    this.onFileSelect = options.onFileSelect;
    this.file = null;
  }

  render() {
    this.container.innerHTML = `
      <div class="file-upload" id="upload-zone">
        <div class="upload-placeholder">
          <svg class="upload-icon" viewBox="0 0 24 24">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
          </svg>
          <p class="upload-text">拖拽文件到这里或点击选择</p>
          <p class="upload-hint">支持: ${this.accept} | 最大: ${this.formatSize(this.maxSize)}</p>
        </div>
        <input type="file" id="file-input" accept="${this.accept}" style="display:none">
        <div class="upload-preview" id="upload-preview" style="display:none"></div>
      </div>
    `;

    this.attachEvents();
  }

  attachEvents() {
    const zone = this.container.querySelector('#upload-zone');
    const input = this.container.querySelector('#file-input');

    // 点击上传
    zone.addEventListener('click', () => input.click());

    // 文件选择
    input.addEventListener('change', (e) => this.handleFile(e.target.files[0]));

    // 拖拽上传
    zone.addEventListener('dragover', (e) => {
      e.preventDefault();
      zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', () => {
      zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', (e) => {
      e.preventDefault();
      zone.classList.remove('drag-over');
      this.handleFile(e.dataTransfer.files[0]);
    });
  }

  handleFile(file) {
    if (!file) return;

    // 验证文件类型
    const validTypes = this.accept.split(',').map(t => t.trim());
    const ext = '.' + file.name.split('.').pop();
    if (!validTypes.includes(ext)) {
      Toast.error(`不支持的文件类型: ${ext}`);
      return;
    }

    // 验证文件大小
    if (file.size > this.maxSize) {
      Toast.error(`文件过大: ${this.formatSize(file.size)} > ${this.formatSize(this.maxSize)}`);
      return;
    }

    this.file = file;
    this.showPreview(file);

    if (this.onFileSelect) {
      this.onFileSelect(file);
    }
  }

  showPreview(file) {
    const preview = this.container.querySelector('#upload-preview');
    preview.style.display = 'block';
    preview.innerHTML = `
      <div class="file-info">
        <svg class="file-icon" viewBox="0 0 24 24">
          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
        </svg>
        <div class="file-details">
          <p class="file-name">${file.name}</p>
          <p class="file-size">${this.formatSize(file.size)}</p>
        </div>
        <button class="btn-remove" onclick="this.closest('.file-upload').querySelector('input').value=''; this.parentElement.parentElement.style.display='none'">×</button>
      </div>
    `;
  }

  formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
  }

  getFile() {
    return this.file;
  }

  reset() {
    this.file = null;
    this.container.querySelector('#file-input').value = '';
    this.container.querySelector('#upload-preview').style.display = 'none';
  }
}
```

---

## 状态管理

使用简单的 **观察者模式** 实现全局状态管理

```javascript
// js/store.js
class Store {
  constructor() {
    this.state = {
      currentSession: null,
      sessionData: {},
      config: {},
      user: {}
    };
    this.listeners = new Map();
  }

  // 获取状态
  get(key) {
    return this.state[key];
  }

  // 设置状态
  set(key, value) {
    this.state[key] = value;
    this.notify(key, value);
    this.saveToLocalStorage();
  }

  // 订阅状态变化
  subscribe(key, callback) {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, []);
    }
    this.listeners.get(key).push(callback);

    // 返回取消订阅函数
    return () => {
      const callbacks = this.listeners.get(key);
      const index = callbacks.indexOf(callback);
      if (index > -1) callbacks.splice(index, 1);
    };
  }

  // 通知订阅者
  notify(key, value) {
    if (this.listeners.has(key)) {
      this.listeners.get(key).forEach(callback => callback(value));
    }
  }

  // 持久化到 LocalStorage
  saveToLocalStorage() {
    localStorage.setItem('translationHub', JSON.stringify(this.state));
  }

  // 从 LocalStorage 恢复
  loadFromLocalStorage() {
    const saved = localStorage.getItem('translationHub');
    if (saved) {
      this.state = JSON.parse(saved);
    }
  }

  // 清空状态
  clear() {
    this.state = {
      currentSession: null,
      sessionData: {},
      config: {},
      user: {}
    };
    localStorage.removeItem('translationHub');
  }
}

const store = new Store();
store.loadFromLocalStorage();
```

---

## API 集成

封装统一的 API 调用接口

```javascript
// js/api.js
class API {
  constructor(baseURL = 'http://localhost:8013') {
    this.baseURL = baseURL;
  }

  async request(method, endpoint, data = null, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    if (data && method !== 'GET') {
      if (data instanceof FormData) {
        delete config.headers['Content-Type']; // Let browser set
        config.body = data;
      } else {
        config.body = JSON.stringify(data);
      }
    }

    try {
      const response = await fetch(url, config);

      // 处理非 JSON 响应 (如文件下载)
      const contentType = response.headers.get('content-type');
      if (contentType && !contentType.includes('application/json')) {
        return response;
      }

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || result.message || 'Request failed');
      }

      return result;
    } catch (error) {
      console.error(`API Error [${method} ${endpoint}]:`, error);
      Toast.error(`请求失败: ${error.message}`);
      throw error;
    }
  }

  get(endpoint, options) {
    return this.request('GET', endpoint, null, options);
  }

  post(endpoint, data, options) {
    return this.request('POST', endpoint, data, options);
  }

  put(endpoint, data, options) {
    return this.request('PUT', endpoint, data, options);
  }

  delete(endpoint, options) {
    return this.request('DELETE', endpoint, null, options);
  }

  // 文件上传
  async uploadFile(endpoint, file, metadata = {}) {
    const formData = new FormData();
    formData.append('file', file);

    Object.entries(metadata).forEach(([key, value]) => {
      formData.append(key, JSON.stringify(value));
    });

    return this.post(endpoint, formData);
  }

  // 文件下载
  async downloadFile(endpoint, filename) {
    const response = await this.get(endpoint, {
      headers: { Accept: 'application/octet-stream' }
    });

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }
}

const api = new API();
```

---

## 交互流程

### 完整用户旅程流程图

```
┌──────────────────────────────────────────────────────────────┐
│ 入口: 访问应用                                                │
│   ↓                                                           │
│ index.html 加载                                               │
│   ↓                                                           │
│ main.js 初始化                                                │
│   ├─ 加载 CSS                                                │
│   ├─ 初始化 Router                                           │
│   ├─ 恢复 Store 状态                                         │
│   └─ 渲染全局组件 (Navbar, Sidebar, StatusBar)              │
│                                                               │
├───────────────────── 流程开始 ──────────────────────────────┤
│                                                               │
│ [页面1] 项目创建 (#/create)                                  │
│   ↓                                                           │
│   1. 用户拖拽/选择 Excel 文件                                │
│   2. 前端验证文件类型/大小                                   │
│   3. POST /api/analyze/upload                                │
│   4. 显示上传进度                                            │
│   5. 文件分析中 (Skeleton Loading)                          │
│   6. 分析完成,显示统计结果                                   │
│   7. Session ID 存入 Store                                   │
│   8. 点击"继续配置" → 跳转 #/config                         │
│                                                               │
│ [页面2] 任务配置 (#/config)                                  │
│   ↓                                                           │
│   1. 加载 Session 数据                                       │
│   2. 用户选择源语言/目标语言                                 │
│   3. 配置上下文提取选项                                      │
│   4. 实时计算预估 (前端计算)                                 │
│   5. 点击"开始拆解" → POST /api/tasks/split                  │
│   6. WebSocket 连接 /ws/split/:id                            │
│   7. 实时显示拆解进度                                        │
│   8. 拆解完成,显示任务统计                                   │
│   9. 点击"开始翻译" → 跳转 #/execute                        │
│                                                               │
│ [页面3] 翻译执行 (#/execute)                                 │
│   ↓                                                           │
│   1. 选择 LLM 引擎                                           │
│   2. 设置并发数                                              │
│   3. 点击"开始翻译" → POST /api/execute/start               │
│   4. WebSocket 连接 /ws/progress/:id                         │
│   5. 实时接收进度推送                                        │
│   6. 动态更新 UI (进度条/统计/任务列表)                     │
│   7. 用户可暂停/恢复/停止                                    │
│   8. 翻译完成 → 显示庆祝动画                                │
│   9. 3秒后自动跳转 #/result                                 │
│                                                               │
│ [页面4] 结果导出 (#/result)                                  │
│   ↓                                                           │
│   1. GET /api/download/:id/summary                           │
│   2. 渲染统计看板                                            │
│   3. 绘制数据图表 (Canvas)                                   │
│   4. 用户点击下载 → GET /api/download/:id                   │
│   5. 触发文件下载                                            │
│   6. 可查看历史 → 跳转 #/history                            │
│   7. 或开始新翻译 → 跳转 #/create                           │
│                                                               │
│ [页面5] 历史管理 (#/history)                                 │
│   ↓                                                           │
│   1. GET /api/sessions                                       │
│   2. 渲染会话列表表格                                        │
│   3. 支持搜索/筛选/排序                                      │
│   4. 单项操作: 查看/下载/删除/继续                          │
│   5. 批量操作: 批量下载/删除                                 │
│   6. 点击会话 → 跳转对应结果页                              │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 性能优化策略

### 1. 资源加载优化

```html
<!-- 关键 CSS 内联 -->
<style>
  /* Critical CSS: 首屏样式 */
  #app { display: grid; ... }
</style>

<!-- 异步加载非关键 CSS -->
<link rel="preload" href="css/components.css" as="style" onload="this.onload=null;this.rel='stylesheet'">

<!-- JS 使用 ES6 Module 按需加载 -->
<script type="module" src="js/main.js"></script>
```

### 2. 代码分割

```javascript
// 路由懒加载
router.register('/history', async () => {
  const { HistoryManager } = await import('./pages/HistoryManager.js');
  return new HistoryManager(container);
});
```

### 3. 虚拟滚动 (大列表优化)

```javascript
class VirtualList {
  constructor(container, items, rowHeight) {
    this.container = container;
    this.items = items;
    this.rowHeight = rowHeight;
    this.visibleCount = Math.ceil(container.clientHeight / rowHeight);
    this.startIndex = 0;

    this.render();
    this.attachScrollListener();
  }

  render() {
    const visibleItems = this.items.slice(
      this.startIndex,
      this.startIndex + this.visibleCount + 5 // Buffer
    );

    this.container.innerHTML = visibleItems.map((item, index) =>
      this.renderItem(item, this.startIndex + index)
    ).join('');

    this.container.style.paddingTop = `${this.startIndex * this.rowHeight}px`;
  }

  attachScrollListener() {
    this.container.addEventListener('scroll', () => {
      const newStartIndex = Math.floor(this.container.scrollTop / this.rowHeight);
      if (newStartIndex !== this.startIndex) {
        this.startIndex = newStartIndex;
        this.render();
      }
    });
  }
}
```

### 4. 防抖与节流

```javascript
// 防抖: 搜索输入
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

searchInput.addEventListener('input', debounce(async (e) => {
  const results = await api.get(`/api/search?q=${e.target.value}`);
  renderResults(results);
}, 300));

// 节流: 滚动事件
function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

window.addEventListener('scroll', throttle(() => {
  updateScrollIndicator();
}, 100));
```

---

## 开发规范

### 代码风格

```javascript
// 命名规范
const variableName = 'camelCase';        // 变量: 驼峰
const CONSTANT_VALUE = 'UPPER_SNAKE';    // 常量: 大写下划线
class ComponentName {}                   // 类: 帕斯卡
function functionName() {}               // 函数: 驼峰

// 注释规范
/**
 * 函数功能描述
 * @param {string} param1 - 参数1说明
 * @param {number} param2 - 参数2说明
 * @returns {boolean} 返回值说明
 */
function exampleFunction(param1, param2) {
  // 实现逻辑
}

// 文件头注释
/**
 * @file ProjectCreate.js
 * @description 项目创建页面组件
 * @author Translation Hub Team
 * @date 2025-10-03
 */
```

### Git 提交规范

```bash
# 格式: <type>(<scope>): <subject>

feat(pages): 实现项目创建页面
fix(api): 修复文件上传超时问题
docs(readme): 更新安装说明
style(css): 优化按钮样式
refactor(router): 重构路由管理器
perf(list): 优化历史列表渲染性能
test(api): 添加 API 单元测试
chore(deps): 更新依赖包
```

---

## 浏览器兼容性

### 目标浏览器

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### Polyfill 策略

仅在需要时引入最小 Polyfill:

```html
<!-- 仅对不支持 ES6 Module 的浏览器加载 -->
<script nomodule src="js/polyfills/es6-module.js"></script>
```

---

## 部署方案

### 静态托管

所有文件均为静态资源,可直接部署到:

- GitHub Pages
- Vercel
- Netlify
- Nginx
- Apache

### Nginx 配置示例

```nginx
server {
  listen 80;
  server_name translation-hub.com;
  root /var/www/translation-hub/frontend_v2;
  index index.html;

  # SPA 路由支持
  location / {
    try_files $uri $uri/ /index.html;
  }

  # 静态资源缓存
  location ~* \.(css|js|jpg|png|svg|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }

  # API 代理
  location /api/ {
    proxy_pass http://localhost:8013;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
  }

  # WebSocket 代理
  location /ws/ {
    proxy_pass http://localhost:8013;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_set_header Host $host;
  }
}
```

---

## 下一步实施计划

### Phase 1: 基础框架 (1-2天)
- [x] 完成设计文档
- [ ] 创建目录结构
- [ ] 实现 Router
- [ ] 实现 Store
- [ ] 实现 API 封装
- [ ] 设计系统 CSS (design-tokens.css)

### Phase 2: 公共组件 (2-3天)
- [ ] Navbar 导航栏
- [ ] Sidebar 侧边栏
- [ ] StatusBar 状态栏
- [ ] Toast 通知
- [ ] Modal 模态框
- [ ] ProgressBar 进度条
- [ ] FileUpload 文件上传

### Phase 3: 页面开发 (5-7天)
- [ ] ProjectCreate 项目创建页
- [ ] TaskConfig 任务配置页
- [ ] TranslationExec 翻译执行页
- [ ] ResultExport 结果导出页
- [ ] HistoryManager 历史管理页

### Phase 4: 集成测试 (2-3天)
- [ ] 端到端流程测试
- [ ] API 集成测试
- [ ] WebSocket 连接测试
- [ ] 响应式布局测试
- [ ] 浏览器兼容性测试

### Phase 5: 优化上线 (1-2天)
- [ ] 性能优化
- [ ] 代码压缩
- [ ] 文档完善
- [ ] 部署配置

---

## 附录

### A. CSS 变量命名规范

```css
/* 颜色 */
--color-primary
--color-secondary
--color-success
--color-error

/* 字体 */
--font-family-sans
--font-size-base
--font-weight-bold

/* 间距 */
--spacing-sm
--spacing-md
--spacing-lg

/* 阴影 */
--shadow-sm
--shadow-md
```

### B. 工具函数库

```javascript
// utils/format.js
export function formatDate(date) { ... }
export function formatFileSize(bytes) { ... }
export function formatCurrency(amount) { ... }
export function formatDuration(ms) { ... }

// utils/validate.js
export function validateEmail(email) { ... }
export function validateFileType(file, types) { ... }
export function validateFileSize(file, maxSize) { ... }

// utils/dom.js
export function createElement(tag, attrs, children) { ... }
export function addClass(el, className) { ... }
export function removeClass(el, className) { ... }
```

---

**文档版本**: 2.0
**最后更新**: 2025-10-03
**维护者**: Translation Hub Team
