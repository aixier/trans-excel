# 工程师A - 基础架构与组件库开发任务

> **角色**: 基础架构工程师 + 组件库负责人
> **工期**: Week 1-4（重点：Week 1-3）
> **工作量**: 15天（120小时）
> **优先级**: 🔥 **最高** - 阻塞其他所有工程师

---

## 🎯 任务目标

### 核心目标

1. **Week 1**: 搭建项目基础架构，为全员提供开发环境
2. **Week 2**: 开发5个核心公共组件，支撑BCD业务开发
3. **Week 3**: 提供工具函数库，优化开发效率
4. **Week 4**: 完善文档、测试、代码Review

### 成功标准

- ✅ 路由系统完整可用，支持Hash路由和页面切换动画
- ✅ API封装层统一，错误处理完善
- ✅ WebSocket管理器稳定，支持断线重连
- ✅ 5个核心组件（StatCard、FilterBar、DataTable、EmptyState、Skeleton）可复用
- ✅ 工具函数库覆盖日期、图表、导出、性能优化
- ✅ 组件文档完整，有使用示例

---

## 📋 详细任务清单

### Week 1: 基础架构（必须在Week 1完成）⚡

#### 1.1 路由系统 (2天 - 优先级最高)

**目标**: 实现Hash路由，支持页面切换和路由守卫

**任务**:
- [ ] 实现Hash Router核心逻辑
  ```javascript
  // 文件: js/core/router.js
  class Router {
    constructor() {
      this.routes = {};
      this.currentRoute = null;
    }

    register(path, handler) { /* ... */ }
    navigate(path) { /* ... */ }
    init() { /* ... */ }
  }
  ```

- [ ] 注册所有路由
  ```javascript
  router.register('/', dashboardPage);
  router.register('/sessions', sessionsPage);
  router.register('/glossary', glossaryPage);
  router.register('/analytics', analyticsPage);
  router.register('/create', createPage);
  router.register('/config', configPage);
  router.register('/execute', executePage);
  router.register('/result', resultPage);
  router.register('/settings', settingsPage);
  ```

- [ ] 实现路由守卫（可选，如需权限控制）
- [ ] 实现页面切换动画（淡入淡出）
- [ ] 处理404页面

**参考文档**:
- 无特定文档，参考现有test_pages的路由逻辑

**交付标准**:
- 可以通过`router.navigate('/path')`切换页面
- URL hash变化时自动加载对应页面
- 页面切换有平滑动画

---

#### 1.2 状态管理 (1天)

**目标**: 实现SessionManager，封装LocalStorage

**任务**:
- [ ] 实现SessionManager静态方法
  ```javascript
  // 文件: js/core/session-manager.js
  class SessionManager {
    static getAllSessions() { /* ... */ }
    static getSession(sessionId) { /* ... */ }
    static saveSession(session) { /* ... */ }
    static deleteSession(sessionId) { /* ... */ }
    static updateSessionProgress(sessionId, progress) { /* ... */ }
  }
  ```

- [ ] 实现SessionManager实例方法（管理当前会话）
- [ ] 定义LocalStorage key规范
  ```javascript
  const STORAGE_KEYS = {
    SESSIONS: 'translation_hub_sessions',
    CURRENT_SESSION: 'translation_hub_current',
    USER_PREFS: 'translation_hub_preferences',
    GLOSSARIES: 'translation_hub_glossaries'
  };
  ```

**参考文档**:
- `docs/technical/FEATURE_SPEC.md` - 状态管理方案（1289-1455行）

**交付标准**:
- SessionManager可以增删改查会话
- 数据持久化到LocalStorage
- 页面刷新后数据不丢失

---

#### 1.3 API封装层 (2天)

**目标**: 统一的Fetch封装，处理所有HTTP请求

**任务**:
- [ ] 实现API基础类
  ```javascript
  // 文件: js/core/api.js
  class API {
    constructor() {
      this.baseURL = 'http://localhost:8013';
      this.token = null;
    }

    async request(endpoint, options = {}) { /* ... */ }

    // 任务拆分API
    async uploadFile(file, config) { /* ... */ }
    async getTaskStatus(sessionId) { /* ... */ }

    // 任务执行API
    async startExecution(sessionId, options) { /* ... */ }
    async pauseExecution(sessionId) { /* ... */ }
    async resumeExecution(sessionId) { /* ... */ }
    async stopExecution(sessionId) { /* ... */ }
    async getExecutionProgress(sessionId) { /* ... */ }

    // 下载API
    async downloadSession(sessionId) { /* ... */ }
    async getDownloadInfo(sessionId) { /* ... */ }

    // 会话管理API
    async getSessions() { /* ... */ }
    async getSessionDetail(sessionId) { /* ... */ }
    async deleteSession(sessionId) { /* ... */ }

    // 术语库API
    async getGlossaries() { /* ... */ }
    async getGlossary(id) { /* ... */ }
    async createGlossary(data) { /* ... */ }
    async updateGlossary(id, data) { /* ... */ }
    async deleteGlossary(id) { /* ... */ }
    async importTerms(glossaryId, terms) { /* ... */ }
    async getTerms(glossaryId, page, pageSize) { /* ... */ }
  }
  ```

- [ ] 实现请求/响应拦截器
- [ ] 实现统一错误处理
- [ ] 实现请求缓存机制（RequestCache）

**参考文档**:
- `docs/API.md` - 完整的API文档
- `docs/technical/FEATURE_SPEC.md` - API对接说明（1149-1286行）

**交付标准**:
- 所有API调用通过统一的API类
- 错误处理统一，返回友好错误信息
- 支持请求缓存（可配置TTL）

---

#### 1.4 WebSocket管理器 (1.5天)

**目标**: 实现WebSocket连接管理，支持实时进度推送

**任务**:
- [ ] 实现WebSocketManager
  ```javascript
  // 文件: js/core/websocket-manager.js
  class WebSocketManager {
    constructor() {
      this.connections = new Map();
    }

    connect(sessionId, callbacks) { /* ... */ }
    disconnect(sessionId) { /* ... */ }
    send(sessionId, message) { /* ... */ }

    // 内部方法
    _setupHeartbeat(ws) { /* ... */ }
    _handleReconnect(sessionId) { /* ... */ }
    _handleMessage(sessionId, event) { /* ... */ }
  }
  ```

- [ ] 实现心跳检测（30秒间隔）
- [ ] 实现断线重连（指数退避）
- [ ] 实现消息分发（progress、task_update、error等）

**参考文档**:
- `docs/API.md` - WebSocket API（646-863行）
- `backend_v2/api/websocket_api.py` - 后端实现参考

**交付标准**:
- 可以建立WebSocket连接
- 收到消息时正确分发到回调函数
- 断线后自动重连（最多3次）
- 心跳检测正常工作

---

#### 1.5 全局错误处理 (0.5天)

**目标**: 统一的错误处理机制

**任务**:
- [ ] 实现ErrorHandler
  ```javascript
  // 文件: js/core/error-handler.js
  class ErrorHandler {
    static handle(error, context = '') { /* ... */ }
    static classifyError(error) { /* ... */ }
    static getErrorMessage(error, type) { /* ... */ }
    static getErrorActions(type) { /* ... */ }
  }
  ```

- [ ] 定义错误类型
  ```javascript
  const ErrorTypes = {
    NETWORK_ERROR: 'network_error',
    API_ERROR: 'api_error',
    VALIDATION_ERROR: 'validation_error',
    AUTH_ERROR: 'auth_error',
    BUSINESS_ERROR: 'business_error',
    UNKNOWN_ERROR: 'unknown_error'
  };
  ```

- [ ] 实现全局错误监听
  ```javascript
  window.addEventListener('unhandledrejection', (event) => {
    ErrorHandler.handle(event.reason, 'UnhandledRejection');
  });
  ```

**参考文档**:
- `docs/technical/FEATURE_SPEC.md` - 错误处理策略（1459-1551行）

**交付标准**:
- 所有未捕获错误都能被ErrorHandler处理
- 错误分类正确
- 用户看到友好的错误提示

---

### Week 2: 公共组件库（BCD依赖）⚡

#### 2.1 StatCard 统计卡片 (1天)

**目标**: 实现4种变体的统计卡片

**任务**:
- [ ] 创建StatCard组件类
  ```javascript
  // 文件: js/components/StatCard.js
  class StatCard {
    constructor(config) {
      this.title = config.title;
      this.value = config.value;
      this.icon = config.icon;
      this.trend = config.trend;
      this.progress = config.progress;
    }

    render() { /* 返回HTML字符串 */ }
    update(newValue) { /* 更新值，带动画 */ }
  }
  ```

- [ ] 实现4种变体
  - 基础卡片（数字+描述）
  - 带图标卡片
  - 带趋势卡片（↑ ↓）
  - 带进度条卡片

- [ ] 实现数字滚动动画
  ```javascript
  function animateValue(element, start, end, duration) { /* ... */ }
  ```

**参考文档**:
- `docs/design/UI_DESIGN.md` - 组件库 - StatCard（656-693行）

**交付标准**:
- 4种变体都可以正常渲染
- 数字更新时有滚动动画
- 样式符合设计规范

**使用示例**:
```javascript
const card = new StatCard({
  title: '今日待办',
  value: 3,
  icon: 'bi-clipboard-check',
  trend: { value: 2, direction: 'up' }
});
document.getElementById('container').innerHTML = card.render();
```

---

#### 2.2 FilterBar 筛选栏 (1天)

**目标**: 实现通用的筛选栏组件

**任务**:
- [ ] 创建FilterBar组件
  ```javascript
  // 文件: js/components/FilterBar.js
  class FilterBar {
    constructor(config) {
      this.filters = config.filters; // 筛选项配置
      this.onSearch = config.onSearch; // 搜索回调
      this.onReset = config.onReset; // 重置回调
    }

    render() { /* ... */ }
    getValues() { /* 获取当前筛选值 */ }
    reset() { /* 重置所有筛选 */ }
  }
  ```

- [ ] 支持多种筛选类型
  - 搜索框（input）
  - 下拉选择（select）
  - 日期范围（date range）
  - 自定义筛选

**参考文档**:
- `docs/design/UI_DESIGN.md` - 组件库 - FilterBar（695-729行）
- `docs/technical/FEATURE_SPEC.md` - 筛选功能（270-339行）

**交付标准**:
- 可以配置多种筛选项
- 点击搜索/重置时触发回调
- 返回当前筛选值对象

**使用示例**:
```javascript
const filterBar = new FilterBar({
  filters: [
    { type: 'search', placeholder: '搜索文件名...' },
    { type: 'select', label: '时间范围', options: ['全部', '今天', '本周'] },
    { type: 'select', label: '状态', options: ['全部', '执行中', '已完成'] }
  ],
  onSearch: (values) => { /* 处理筛选 */ },
  onReset: () => { /* 重置 */ }
});
```

---

#### 2.3 DataTable 数据表格 (2天 - 最复杂)

**目标**: 实现功能完整的数据表格

**任务**:
- [ ] 创建DataTable组件
  ```javascript
  // 文件: js/components/DataTable.js
  class DataTable {
    constructor(config) {
      this.columns = config.columns; // 列配置
      this.data = config.data; // 数据
      this.selectable = config.selectable; // 是否可选
      this.sortable = config.sortable; // 是否可排序
      this.pagination = config.pagination; // 分页配置
      this.onRowClick = config.onRowClick;
      this.onSelectionChange = config.onSelectionChange;
    }

    render() { /* ... */ }
    updateData(newData) { /* ... */ }
    getSelectedRows() { /* ... */ }
    sort(columnKey, direction) { /* ... */ }
  }
  ```

- [ ] 实现功能
  - [x] 全选/单选
  - [x] 列排序（点击表头）
  - [x] 分页组件
  - [x] 行操作菜单
  - [x] 虚拟滚动（大数据优化，可选）

**参考文档**:
- `docs/design/UI_DESIGN.md` - 组件库 - DataTable（731-809行）
- `docs/technical/FEATURE_SPEC.md` - 虚拟滚动（1629-1693行）

**交付标准**:
- 可以渲染大量数据（1000+行）不卡顿
- 全选/单选功能正常
- 排序功能正常
- 分页功能正常

**使用示例**:
```javascript
const table = new DataTable({
  columns: [
    { key: 'filename', label: '文件名', sortable: true },
    { key: 'status', label: '状态', render: (val) => `<span class="badge">${val}</span>` },
    { key: 'progress', label: '进度', render: (val) => `<progress value="${val}"></progress>` }
  ],
  data: sessions,
  selectable: true,
  pagination: { pageSize: 10 },
  onSelectionChange: (selectedRows) => { /* ... */ }
});
```

---

#### 2.4 EmptyState 空状态 (0.5天)

**目标**: 实现4种空状态场景

**任务**:
- [ ] 创建EmptyState组件
  ```javascript
  // 文件: js/components/EmptyState.js
  class EmptyState {
    constructor(config) {
      this.type = config.type; // first-time | no-results | search | error
      this.title = config.title;
      this.message = config.message;
      this.action = config.action; // 操作按钮
    }

    render() { /* ... */ }
  }
  ```

- [ ] 实现4种变体
  - 首次使用（带"新建"按钮）
  - 筛选无结果（带"清除筛选"按钮）
  - 搜索无结果（带"修改关键词"提示）
  - 错误状态（带"重试"按钮）

**参考文档**:
- `docs/design/UI_DESIGN.md` - 组件库 - EmptyState（850-883行）

**交付标准**:
- 4种变体都可以渲染
- 样式符合设计规范
- 操作按钮可以触发回调

---

#### 2.5 Skeleton 骨架屏 (0.5天)

**目标**: 实现3种骨架屏

**任务**:
- [ ] 创建Skeleton组件
  ```javascript
  // 文件: js/components/Skeleton.js
  class Skeleton {
    static text(lines = 3) { /* 返回文本骨架HTML */ }
    static card() { /* 返回卡片骨架HTML */ }
    static table(rows = 5) { /* 返回表格骨架HTML */ }
  }
  ```

**参考文档**:
- `docs/design/UI_DESIGN.md` - 组件库 - Skeleton（885-913行）

**交付标准**:
- 3种骨架屏可以渲染
- 使用DaisyUI的skeleton样式

---

### Week 3: 工具函数库

#### 3.1 日期工具 (0.5天)

**目标**: 实现日期格式化和相对时间

**任务**:
- [ ] 创建date-helper.js
  ```javascript
  // 文件: js/utils/date-helper.js

  // 相对时间 (5分钟前、2小时前、昨天)
  function formatTimeAgo(timestamp) { /* ... */ }

  // 日期格式化 (2025-10-17 15:30)
  function formatDate(timestamp, format = 'YYYY-MM-DD HH:mm') { /* ... */ }

  // 日期范围计算
  function getDateRange(range) { /* 'today' | 'week' | 'month' */ }
  ```

**参考文档**:
- `docs/technical/FEATURE_SPEC.md` - 日期工具（提及但无具体实现）

**交付标准**:
- formatTimeAgo返回正确的相对时间
- formatDate支持常用格式
- getDateRange返回正确的日期范围

---

#### 3.2 图表工具 (1天)

**目标**: 封装Chart.js，提供常用图表配置

**任务**:
- [ ] 创建chart-helper.js
  ```javascript
  // 文件: js/utils/chart-helper.js

  class ChartHelper {
    // 折线图
    static createLineChart(canvasId, data, options = {}) { /* ... */ }

    // 饼图
    static createPieChart(canvasId, data, options = {}) { /* ... */ }

    // 柱状图
    static createBarChart(canvasId, data, options = {}) { /* ... */ }

    // 销毁图表
    static destroyChart(chartInstance) { /* ... */ }
  }
  ```

**参考文档**:
- `docs/design/UI_DESIGN.md` - 图表组件（600-651行）
- `docs/technical/FEATURE_SPEC.md` - ChartRenderer（1048-1145行）
- Chart.js官方文档

**交付标准**:
- 可以创建3种类型图表
- 配置符合设计规范（颜色、样式）
- 提供默认配置，可自定义覆盖

---

#### 3.3 导出工具 (1天)

**目标**: 实现Excel、CSV导出和ZIP打包

**任务**:
- [ ] 创建export-helper.js
  ```javascript
  // 文件: js/utils/export-helper.js

  class ExportHelper {
    // Excel导出 (使用SheetJS)
    static exportToExcel(data, filename) { /* ... */ }

    // CSV导出
    static exportToCSV(data, filename) { /* ... */ }

    // ZIP打包 (使用JSZip)
    static createZip(files) { /* ... */ }

    // 触发下载
    static download(blob, filename) { /* ... */ }
  }
  ```

**参考文档**:
- `docs/technical/FEATURE_SPEC.md` - 导出功能（提及但无具体实现）
- SheetJS文档
- JSZip文档

**交付标准**:
- 可以导出Excel文件
- 可以导出CSV文件
- 可以打包多个文件为ZIP

---

#### 3.4 性能优化工具 (0.5天)

**目标**: 提供防抖、节流、懒加载、缓存工具

**任务**:
- [ ] 创建performance-helper.js
  ```javascript
  // 文件: js/utils/performance-helper.js

  // 防抖
  function debounce(func, delay = 300) { /* ... */ }

  // 节流
  function throttle(func, limit = 100) { /* ... */ }

  // 懒加载
  function setupLazyLoading(selector = 'img[data-src]') { /* ... */ }

  // 请求缓存
  class RequestCache {
    constructor(ttl = 60000) { /* ... */ }
    async get(key, fetcher) { /* ... */ }
    clear(key) { /* ... */ }
  }
  ```

**参考文档**:
- `docs/technical/FEATURE_SPEC.md` - 性能优化方案（1555-1737行）

**交付标准**:
- 防抖和节流函数正常工作
- 懒加载使用Intersection Observer
- 请求缓存支持TTL

---

### Week 4: 文档与测试

#### 4.1 组件文档 (1天)

**目标**: 为每个组件编写使用文档

**任务**:
- [ ] 创建COMPONENTS.md
  - StatCard使用说明和示例
  - FilterBar使用说明和示例
  - DataTable使用说明和示例
  - EmptyState使用说明和示例
  - Skeleton使用说明和示例

**交付标准**:
- 每个组件有完整的API文档
- 每个组件有代码示例
- 有常见问题FAQ

---

#### 4.2 单元测试 (1天)

**目标**: 为关键函数编写单元测试

**任务**:
- [ ] 创建test/目录
- [ ] 测试工具函数
  - date-helper测试
  - performance-helper测试（防抖、节流）
- [ ] 测试组件（可选）
  - StatCard测试
  - FilterBar测试

**交付标准**:
- 关键函数有单元测试
- 测试覆盖率 > 60%

---

## 📚 参考文档清单

### 必读文档（按优先级）

1. **`docs/design/UI_DESIGN.md`** ⭐⭐⭐
   - 设计系统（色彩、字体、间距、图标）
   - 组件库详细设计
   - 页面原型

2. **`docs/technical/FEATURE_SPEC.md`** ⭐⭐⭐
   - 技术实现规范
   - 状态管理方案
   - 错误处理策略
   - 性能优化方案

3. **`docs/API.md`** ⭐⭐⭐
   - 完整的后端API文档
   - WebSocket API文档
   - 数据模型

### 选读文档

4. **`docs/requirements/REQUIREMENTS.md`**
   - 了解业务需求（帮助理解为什么这样设计）

5. **`docs/design/PIPELINE_UX_DESIGN.md`**
   - 了解Pipeline概念（如果有疑问）

6. **外部文档**
   - DaisyUI文档: https://daisyui.com/
   - Chart.js文档: https://www.chartjs.org/
   - SheetJS文档: https://docs.sheetjs.com/

---

## 🎯 交付标准

### Week 1 交付（必须完成）

- [ ] ✅ 路由系统可用，可切换页面
- [ ] ✅ API封装层完成，可调用后端API
- [ ] ✅ WebSocket管理器完成，可接收实时消息
- [ ] ✅ SessionManager完成，可管理会话数据
- [ ] ✅ ErrorHandler完成，可处理全局错误

**验收方式**:
- 创建简单的测试页面，验证路由、API、WebSocket都能正常工作
- 提供API调用示例代码给BCD工程师

---

### Week 2 交付（必须完成）

- [ ] ✅ StatCard组件完成，4种变体都可用
- [ ] ✅ FilterBar组件完成，支持多种筛选类型
- [ ] ✅ DataTable组件完成，支持选择、排序、分页
- [ ] ✅ EmptyState组件完成，4种场景都可用
- [ ] ✅ Skeleton组件完成，3种骨架屏都可用

**验收方式**:
- 每个组件有独立的demo页面
- 提供组件使用示例给BCD工程师
- BCD工程师可以直接引入使用

---

### Week 3 交付

- [ ] ✅ 日期工具函数完成
- [ ] ✅ 图表工具完成（Chart.js封装）
- [ ] ✅ 导出工具完成（Excel、CSV、ZIP）
- [ ] ✅ 性能优化工具完成（防抖、节流、缓存）

**验收方式**:
- 每个工具函数有使用示例
- 图表工具可以渲染3种图表

---

### Week 4 交付

- [ ] ✅ 组件文档完成（COMPONENTS.md）
- [ ] ✅ 单元测试完成（覆盖率 > 60%）
- [ ] ✅ 代码Review完成（Review BCD的代码）

---

## 🤝 协作接口

### 提供给其他工程师的接口

#### 1. 路由接口
```javascript
// 导航到指定页面
router.navigate('/sessions');

// 获取当前路由
const currentPath = router.getCurrentPath();
```

#### 2. API接口
```javascript
// 全局API实例
const api = new API();

// 调用API
const sessions = await api.getSessions();
const progress = await api.getExecutionProgress(sessionId);
```

#### 3. WebSocket接口
```javascript
// 连接WebSocket
const ws = wsManager.connect(sessionId, {
  onProgress: (data) => { /* 更新进度 */ },
  onTaskUpdate: (data) => { /* 更新任务 */ },
  onError: (error) => { /* 处理错误 */ }
});

// 断开连接
wsManager.disconnect(sessionId);
```

#### 4. 组件接口
```javascript
// 使用组件
import StatCard from './components/StatCard.js';
const card = new StatCard({ title: '今日待办', value: 3 });
document.getElementById('container').innerHTML = card.render();
```

#### 5. 工具函数接口
```javascript
// 使用工具函数
import { formatTimeAgo, debounce } from './utils/date-helper.js';
const relativeTime = formatTimeAgo(timestamp);

const search = debounce((text) => { /* 搜索 */ }, 500);
```

---

## 🚨 注意事项

### 开发优先级

1. **Week 1必须完成**：路由、API、WebSocket是最高优先级，否则阻塞所有人
2. **Week 2必须完成**：组件库是次高优先级，BCD在Week 2开始依赖组件
3. **Week 3可以弹性**：工具函数库重要但不阻塞，可以边开发边提供
4. **Week 4可以并行**：文档和测试可以和BCD的开发并行进行

### 质量标准

- **代码规范**：严格遵守命名规范（camelCase / PascalCase）
- **注释完整**：每个公共函数都要有注释（参数、返回值、用途）
- **错误处理**：所有异步函数都要有try-catch
- **可复用性**：组件和工具函数要高度可复用，避免耦合

### 沟通要点

- **每天更新**：在站会上告知进度，是否有阻塞
- **及时通知**：Week 1的任务完成后，立即通知BCD可以开始
- **主动Review**：主动Review BCD的代码，确保组件使用正确

---

## ✅ 自检清单

### Week 1结束前
- [ ] 路由系统可以切换页面
- [ ] API可以调用后端接口（至少测试3个接口）
- [ ] WebSocket可以接收消息（测试进度推送）
- [ ] SessionManager可以保存和读取数据
- [ ] ErrorHandler可以捕获全局错误
- [ ] 已通知BCD工程师可以开始使用

### Week 2结束前
- [ ] 5个组件都有demo页面
- [ ] 每个组件有使用示例
- [ ] BCD工程师已经在使用组件
- [ ] 收集了BCD的反馈并优化

### Week 3结束前
- [ ] 工具函数都有使用示例
- [ ] Chart.js可以渲染图表
- [ ] 导出功能可以下载文件

### Week 4结束前
- [ ] 组件文档完成
- [ ] 单元测试覆盖率 > 60%
- [ ] Review了BCD的所有代码

---

**开始时间**: Week 1 Day 1
**预计完成**: Week 4 Day 5
**总工作量**: 15天（120小时）

**祝开发顺利！有问题随时沟通。** 🚀
