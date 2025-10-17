# 组件库使用文档

> **版本**: v1.0
> **最后更新**: 2025-10-17
> **工程师**: Engineer A

---

## 📋 目录

1. [核心架构](#核心架构)
2. [Router - 路由系统](#router---路由系统)
3. [API - 请求封装](#api---请求封装)
4. [WebSocketManager - 实时通信](#websocketmanager---实时通信)
5. [StatCard - 统计卡片](#statcard---统计卡片)
6. [FilterBar - 筛选栏](#filterbar---筛选栏)
7. [DataTable - 数据表格](#datatable---数据表格)

---

## 核心架构

### 目录结构

```
frontend_v2/
├── js/
│   ├── core/                 # 核心模块
│   │   └── router.js         # 路由系统
│   ├── services/             # 服务层
│   │   ├── api.js            # API封装
│   │   └── websocket-manager.js  # WebSocket管理
│   ├── components/           # 组件库
│   │   ├── stat-card.js      # 统计卡片
│   │   ├── filter-bar.js     # 筛选栏
│   │   └── data-table.js     # 数据表格
│   ├── utils/                # 工具函数
│   └── pages/                # 页面组件
├── test-components.html      # 组件测试页面
└── COMPONENTS.md             # 本文档
```

### 引入方式

```html
<!-- 核心模块 -->
<script src="js/core/router.js"></script>

<!-- 服务层 -->
<script src="js/services/api.js"></script>
<script src="js/services/websocket-manager.js"></script>

<!-- 组件库 -->
<script src="js/components/stat-card.js"></script>
<script src="js/components/filter-bar.js"></script>
<script src="js/components/data-table.js"></script>
```

### 全局实例

系统自动创建以下全局实例：

```javascript
// 路由实例
const router = new Router();

// API实例
const api = new API();

// WebSocket管理器实例
const wsManager = new WebSocketManager();
```

---

## Router - 路由系统

### 功能特性

- ✅ 基于Hash的SPA路由
- ✅ 页面切换动画（淡入淡出）
- ✅ 路由守卫（权限控制）
- ✅ 查询参数解析
- ✅ 404错误处理
- ✅ 浏览器前进/后退支持

### 基础使用

```javascript
// 1. 注册路由
router.register('/', () => {
  return '<div>首页内容</div>';
});

router.register('/dashboard', () => {
  return '<div>工作台内容</div>';
});

// 2. 初始化路由系统
router.init();

// 3. 导航到指定路径
router.navigate('/dashboard');
```

### 高级用法

#### 1. 异步路由处理

```javascript
router.register('/sessions', async () => {
  const sessions = await api.getSessions();
  return `<div>${renderSessionsList(sessions)}</div>`;
});
```

#### 2. 路由守卫

```javascript
router.setGuard((to, from, next) => {
  if (to === '/admin' && !isAdmin()) {
    next('/login');  // 重定向到登录页
  } else {
    next();  // 允许访问
  }
});
```

#### 3. 查询参数

```javascript
// URL: #/sessions?status=running&page=2
const params = router.getQueryParams();
// { status: 'running', page: '2' }
```

#### 4. 路由事件监听

```javascript
window.addEventListener('routechange', (e) => {
  console.log('路由变化:', e.detail.path);
  console.log('查询参数:', e.detail.params);
});
```

### API参考

| 方法 | 说明 | 参数 |
|------|------|------|
| `register(path, handler)` | 注册路由 | path: 路由路径<br>handler: 处理函数 |
| `navigate(path, replace)` | 导航到指定路径 | path: 目标路径<br>replace: 是否替换历史记录 |
| `init()` | 初始化路由系统 | - |
| `setGuard(guard)` | 设置路由守卫 | guard: 守卫函数 |
| `getCurrentPath()` | 获取当前路由 | - |
| `getQueryParams()` | 获取查询参数 | - |
| `back()` | 返回上一页 | - |
| `forward()` | 前进到下一页 | - |

---

## API - 请求封装

### 功能特性

- ✅ 统一的请求/响应处理
- ✅ 自动错误处理和分类
- ✅ 请求超时控制
- ✅ 请求缓存（GET请求）
- ✅ Token认证支持
- ✅ FormData自动处理

### 基础使用

```javascript
// 设置API基础URL
api.setBaseURL('http://localhost:8013');

// GET请求
const sessions = await api.getSessions();

// POST请求
const result = await api.startExecution(sessionId, {
  processor: 'llm_qwen',
  max_workers: 10
});
```

### 任务拆分API

```javascript
// 1. 上传文件并拆分
const file = document.getElementById('file-input').files[0];
const response = await api.uploadFile(file, {
  target_langs: ['EN', 'JP'],
  rule_set: 'translation',
  extract_context: true
});

// 2. 从Parent Session拆分
const response = await api.splitFromParent('parent-session-id', {
  rule_set: 'caps_only',
  target_langs: ['EN']
});

// 3. 获取拆分状态
const status = await api.getSplitStatus(sessionId);

// 4. 导出任务表
const blob = await api.exportTasks(sessionId, 'tasks');
```

### 任务执行API

```javascript
// 1. 开始执行
await api.startExecution(sessionId, {
  processor: 'llm_qwen',
  max_workers: 10
});

// 2. 暂停/恢复/停止
await api.pauseExecution(sessionId);
await api.resumeExecution(sessionId);
await api.stopExecution(sessionId);

// 3. 获取执行进度
const progress = await api.getExecutionProgress(sessionId);
```

### 下载API

```javascript
// 1. 下载结果文件
const blob = await api.downloadSession(sessionId);

// 2. 下载Input Excel
const blob = await api.downloadInput(sessionId);

// 3. 获取下载信息
const info = await api.getDownloadInfo(sessionId);

// 4. 获取翻译摘要
const summary = await api.getSummary(sessionId);
```

### 会话管理API

```javascript
// 1. 获取会话列表
const sessions = await api.getSessions();

// 2. 获取会话详情
const session = await api.getSessionDetail(sessionId);

// 3. 删除会话
await api.deleteSession(sessionId);
```

### 术语库API

```javascript
// 1. 获取术语库列表
const glossaries = await api.getGlossaries();

// 2. 创建术语库
const glossary = await api.createGlossary({
  name: '游戏通用术语',
  description: '游戏相关的通用翻译术语'
});

// 3. 导入术语
await api.importTerms(glossaryId, [
  { source: '攻击力', en: 'ATK', jp: '攻撃力' }
]);

// 4. 获取术语列表（分页）
const terms = await api.getTerms(glossaryId, page, pageSize);
```

### 错误处理

```javascript
try {
  const result = await api.getSessions();
} catch (error) {
  // error.message 包含友好的错误信息
  console.error('请求失败:', error.message);
}
```

### 缓存控制

```javascript
// GET请求默认不使用缓存
const sessions1 = await api.getSessions();

// 手动使用缓存（TTL默认60秒）
const sessions2 = await api.get('/api/sessions', true);

// 清除缓存
api.clearCache('/api/sessions');  // 清除指定缓存
api.clearCache();  // 清除所有缓存
```

---

## WebSocketManager - 实时通信

### 功能特性

- ✅ 自动心跳检测（30秒间隔）
- ✅ 断线重连（指数退避）
- ✅ 消息类型分发
- ✅ 多连接管理
- ✅ 连接状态查询

### 基础使用

```javascript
// 连接WebSocket
wsManager.connect(sessionId, {
  onProgress: (data) => {
    console.log(`进度: ${data.progress}%`);
  },
  onTaskUpdate: (data) => {
    console.log(`任务更新:`, data);
  },
  onComplete: (data) => {
    console.log('执行完成:', data);
  },
  onError: (error) => {
    console.error('错误:', error);
  }
});

// 断开连接
wsManager.disconnect(sessionId);
```

### 消息类型

WebSocket支持以下消息类型：

| 消息类型 | 说明 | 回调函数 |
|---------|------|---------|
| `progress` | 进度更新 | `onProgress(data)` |
| `task_update` | 任务更新 | `onTaskUpdate(data)` |
| `batch_complete` | 批次完成 | `onBatchComplete(data)` |
| `complete` | 全部完成 | `onComplete(data)` |
| `error` | 错误信息 | `onError(error)` |
| `status` | 状态更新 | `onStatus(data)` |

### 高级用法

#### 1. 发送消息

```javascript
wsManager.send(sessionId, {
  type: 'pause',
  reason: 'User requested'
});
```

#### 2. 检查连接状态

```javascript
const isConnected = wsManager.isConnected(sessionId);
const state = wsManager.getConnectionState(sessionId);
// 返回: 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED'
```

#### 3. 启用调试日志

```javascript
wsManager.setDebug(true);
```

#### 4. 断开所有连接

```javascript
// 页面卸载时断开所有连接
window.addEventListener('beforeunload', () => {
  wsManager.disconnectAll();
});
```

---

## StatCard - 统计卡片

### 功能特性

- ✅ 4种变体（基础、带图标、带趋势、带进度条）
- ✅ 数字滚动动画
- ✅ 多种主题色
- ✅ 3种尺寸

### 基础使用

```javascript
const card = new StatCard({
  title: '今日待办',
  value: 3,
  icon: 'bi-clipboard-check',
  color: 'primary'
});

container.innerHTML = card.render();
```

### 4种变体

#### 1. 基础卡片

```javascript
const card = StatCard.basic('今日待办', 3, 'primary');
```

#### 2. 带图标卡片

```javascript
const card = StatCard.withIcon('今日待办', 3, 'bi-clipboard-check', 'primary');
```

#### 3. 带趋势卡片

```javascript
const card = StatCard.withTrend('本月完成', 24, 15, 'up', 'success');
```

#### 4. 带进度条卡片

```javascript
const card = StatCard.withProgress('执行中任务', 1, 60, 'warning');
```

### 完整配置示例

```javascript
const card = new StatCard({
  title: '今日待办',              // 标题
  value: 3,                        // 值
  icon: 'bi-clipboard-check',      // Bootstrap Icon类名
  trend: {                         // 趋势（可选）
    value: 2,
    direction: 'up',               // 'up' | 'down'
    label: '较昨日'
  },
  progress: {                      // 进度（可选）
    value: 60,                     // 0-100
    label: '60% 完成'
  },
  color: 'primary',                // 主题色
  size: 'md',                      // 'sm' | 'md' | 'lg'
  containerId: 'my-card',          // 容器ID
  onClick: handleClick             // 点击回调
});
```

### 更新数值（带动画）

```javascript
// 创建卡片时指定containerId
const card = new StatCard({
  title: '今日待办',
  value: 3,
  containerId: 'stat-card-1'
});

// 渲染
document.getElementById('stat-card-1').innerHTML = card.render();

// 更新数值（1秒动画）
card.update(10, 1000);
```

### 主题色

支持的主题色：`primary` | `secondary` | `success` | `warning` | `error` | `info`

---

## FilterBar - 筛选栏

### 功能特性

- ✅ 多种筛选类型（搜索、下拉、日期范围、自定义）
- ✅ 回车搜索
- ✅ 一键重置
- ✅ 灵活布局

### 基础使用

```javascript
const filterBar = new FilterBar({
  filters: [
    {
      type: 'search',
      placeholder: '搜索文件名...',
      width: 'flex-1 min-w-[200px]'
    },
    {
      type: 'select',
      label: '状态',
      options: ['全部', '执行中', '已完成']
    }
  ],
  onSearch: (values) => {
    console.log('搜索:', values);
  },
  onReset: () => {
    console.log('重置');
  }
});

container.innerHTML = filterBar.render();
filterBar.init();  // 必须调用init()绑定事件
```

### 筛选类型

#### 1. 搜索框 (search)

```javascript
{
  type: 'search',
  placeholder: '搜索...',
  width: 'flex-1 min-w-[200px]'
}
```

#### 2. 下拉选择 (select)

```javascript
{
  type: 'select',
  label: '状态',
  options: [
    '全部状态',
    '执行中',
    '已完成'
  ]
}

// 或使用对象格式
{
  type: 'select',
  label: '状态',
  options: [
    { label: '全部状态', value: 'all' },
    { label: '执行中', value: 'running' }
  ],
  defaultValue: 'all'
}
```

#### 3. 日期范围 (dateRange)

```javascript
{
  type: 'dateRange',
  label: '日期范围'
}
```

#### 4. 自定义筛选 (custom)

```javascript
{
  type: 'custom',
  html: '<div>自定义HTML</div>',
  getValue: (filter) => {
    // 返回筛选值
    return document.getElementById('custom-input').value;
  },
  setValue: (filter, value) => {
    // 设置筛选值
    document.getElementById('custom-input').value = value;
  },
  reset: (filter) => {
    // 重置逻辑
    document.getElementById('custom-input').value = '';
  }
}
```

### 获取/设置筛选值

```javascript
// 获取当前筛选值
const values = filterBar.getValues();
console.log(values);
// {
//   'filter-xxx-0': '搜索关键词',
//   'filter-xxx-1': 'all'
// }

// 设置筛选值
filterBar.setValues({
  'filter-xxx-0': '新关键词',
  'filter-xxx-1': 'running'
});

// 重置筛选
filterBar.reset();
```

### 完整示例

```javascript
const filterBar = new FilterBar({
  filters: [
    {
      type: 'search',
      id: 'filename-search',
      placeholder: '搜索文件名...',
      width: 'flex-1 min-w-[200px]'
    },
    {
      type: 'select',
      id: 'time-range',
      label: '时间范围',
      options: ['全部时间', '今天', '本周', '本月'],
      defaultValue: '全部时间'
    },
    {
      type: 'select',
      id: 'status',
      label: '状态',
      options: [
        { label: '全部状态', value: 'all' },
        { label: '执行中', value: 'running' },
        { label: '已完成', value: 'completed' }
      ]
    }
  ],
  onSearch: (values) => {
    const { 'filename-search': keyword, 'status': status } = values;
    // 执行筛选逻辑
    filterData(keyword, status);
  },
  onReset: () => {
    // 重置数据
    loadAllData();
  },
  showResetButton: true
});

container.innerHTML = filterBar.render();
filterBar.init();
```

---

## DataTable - 数据表格

### 功能特性

- ✅ 全选/单选
- ✅ 列排序
- ✅ 分页
- ✅ 自定义列渲染
- ✅ 行点击事件
- ✅ 斑马纹/悬浮效果
- ✅ 空状态显示

### 基础使用

```javascript
const table = new DataTable({
  columns: [
    { key: 'filename', label: '文件名', sortable: true },
    { key: 'status', label: '状态' },
    { key: 'progress', label: '进度' }
  ],
  data: [
    { filename: 'game.xlsx', status: 'running', progress: 60 },
    { filename: 'ui.xlsx', status: 'completed', progress: 100 }
  ],
  selectable: true,
  pagination: { pageSize: 10 }
});

container.innerHTML = table.render();
table.init();  // 必须调用init()绑定事件
```

### 列配置

#### 基础列

```javascript
{
  key: 'filename',          // 数据字段名
  label: '文件名',          // 表头显示文本
  sortable: true,           // 是否可排序
  width: '200px',           // 列宽
  align: 'left'             // 对齐方式: 'left' | 'center' | 'right'
}
```

#### 自定义渲染

```javascript
{
  key: 'status',
  label: '状态',
  render: (value, row) => {
    const badges = {
      running: '<span class="badge badge-warning">执行中</span>',
      completed: '<span class="badge badge-success">已完成</span>'
    };
    return badges[value] || value;
  }
}
```

#### 嵌套属性

```javascript
// 支持点号访问嵌套属性
{
  key: 'user.name',  // 访问 row.user.name
  label: '用户名'
}
```

### 选择功能

```javascript
const table = new DataTable({
  selectable: true,
  onSelectionChange: (selectedRows) => {
    console.log('已选择:', selectedRows);
  },
  // ...其他配置
});

// 获取选中的行
const selected = table.getSelectedRows();
```

### 排序功能

```javascript
const table = new DataTable({
  sortable: true,
  columns: [
    { key: 'filename', label: '文件名', sortable: true },
    { key: 'updateTime', label: '更新时间', sortable: false }  // 禁用排序
  ],
  // ...其他配置
});

// 手动排序
table.sort('filename');
```

### 分页功能

```javascript
const table = new DataTable({
  pagination: {
    pageSize: 10  // 每页10条
  },
  // ...其他配置
});

// 跳转到指定页
table.goToPage(2);
```

### 行点击事件

```javascript
const table = new DataTable({
  onRowClick: (row, index) => {
    console.log('点击了行:', row, index);
    // 跳转到详情页
    router.navigate(`/session-detail?id=${row.sessionId}`);
  },
  // ...其他配置
});
```

### 更新数据

```javascript
// 更新表格数据（会清空选择和重置到第一页）
table.updateData(newDataArray);
```

### 完整示例

```javascript
const table = new DataTable({
  columns: [
    {
      key: 'filename',
      label: '文件名',
      sortable: true,
      render: (val) => `
        <div class="flex items-center gap-2">
          <i class="bi bi-file-earmark-excel text-success"></i>
          <span class="font-medium">${val}</span>
        </div>
      `
    },
    {
      key: 'status',
      label: '状态',
      sortable: true,
      render: (val) => {
        const badges = {
          pending: '<span class="badge badge-info">待配置</span>',
          running: '<span class="badge badge-warning">执行中</span>',
          completed: '<span class="badge badge-success">已完成</span>',
          failed: '<span class="badge badge-error">失败</span>'
        };
        return badges[val] || val;
      }
    },
    {
      key: 'progress',
      label: '进度',
      sortable: true,
      render: (val) => `
        <div class="flex items-center gap-2">
          <progress class="progress progress-${val === 100 ? 'success' : 'warning'} w-24"
                    value="${val}" max="100"></progress>
          <span class="text-sm">${val}%</span>
        </div>
      `
    },
    {
      key: 'updateTime',
      label: '更新时间',
      sortable: true
    }
  ],
  data: sessions,
  selectable: true,
  sortable: true,
  pagination: { pageSize: 10 },
  striped: true,
  hover: true,
  onSelectionChange: (selectedRows) => {
    console.log('已选择:', selectedRows);
  },
  onRowClick: (row) => {
    router.navigate(`/session/${row.sessionId}`);
  }
});

document.getElementById('table-container').innerHTML = table.render();
table.init();
```

---

## 常见问题 FAQ

### 1. 组件渲染后事件不生效？

**原因**：忘记调用`init()`方法绑定事件。

**解决**：
```javascript
const filterBar = new FilterBar({...});
container.innerHTML = filterBar.render();
filterBar.init();  // ⚠️ 必须调用
```

### 2. 路由切换后页面空白？

**原因**：路由处理函数没有返回HTML或返回了undefined。

**解决**：
```javascript
// ❌ 错误
router.register('/dashboard', () => {
  console.log('Dashboard');
});

// ✅ 正确
router.register('/dashboard', () => {
  return '<div>Dashboard</div>';
});
```

### 3. API请求超时？

**原因**：默认超时时间30秒，可能网络较慢。

**解决**：
```javascript
api.timeout = 60000;  // 设置为60秒
```

### 4. WebSocket连接失败？

**原因**：
- 后端服务未启动
- WebSocket URL错误
- Session ID不存在

**解决**：
```javascript
// 检查URL和Session ID
console.log('URL:', wsManager.baseURL);
console.log('Session ID:', sessionId);

// 启用调试日志
wsManager.setDebug(true);
```

### 5. StatCard数值更新无动画？

**原因**：创建卡片时没有指定`containerId`。

**解决**：
```javascript
const card = new StatCard({
  title: '今日待办',
  value: 3,
  containerId: 'my-card'  // ⚠️ 必须指定
});

document.getElementById('my-card').innerHTML = card.render();
card.update(10);  // 现在有动画了
```

---

## 测试页面

使用`test-components.html`验证所有组件功能：

```bash
# 1. 启动HTTP服务器
cd frontend_v2
python -m http.server 8080

# 2. 打开浏览器
http://localhost:8080/test-components.html
```

---

## 更新日志

### v1.0 (2025-10-17)

**Week 1完成：**
- ✅ Router路由系统
- ✅ API封装层
- ✅ WebSocket管理器

**Week 2完成：**
- ✅ StatCard组件
- ✅ FilterBar组件
- ✅ DataTable组件

**测试：**
- ✅ 组件测试页面
- ✅ 使用文档

---

**文档维护**: Engineer A
**联系方式**: 有问题请在项目中提Issue
