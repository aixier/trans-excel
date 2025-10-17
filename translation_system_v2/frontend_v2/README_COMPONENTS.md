# 前端组件库 - 快速开始

> **版本**: v1.0
> **工程师**: Engineer A
> **更新日期**: 2025-10-17

---

## 🚀 快速开始

### 1. 测试所有组件

打开测试页面，交互式体验所有组件：

```bash
cd frontend_v2
python -m http.server 8080
```

然后访问：http://localhost:8080/test-components.html

### 2. 引入组件到项目

```html
<!-- 核心模块 -->
<script src="js/core/router.js"></script>
<script src="js/services/api.js"></script>
<script src="js/services/websocket-manager.js"></script>

<!-- 组件库 -->
<script src="js/components/stat-card.js"></script>
<script src="js/components/filter-bar.js"></script>
<script src="js/components/data-table.js"></script>
```

### 3. 使用全局实例

系统自动创建以下全局实例：

```javascript
// 路由实例
router.navigate('/dashboard');

// API实例
const sessions = await api.getSessions();

// WebSocket实例
wsManager.connect(sessionId, callbacks);
```

---

## 📦 已完成的组件

| 组件 | 文件 | 功能 | 状态 |
|------|------|------|------|
| **Router** | `js/core/router.js` | Hash路由、页面切换动画、路由守卫 | ✅ |
| **API** | `js/services/api.js` | HTTP请求封装、错误处理、缓存 | ✅ |
| **WebSocket** | `js/services/websocket-manager.js` | 实时通信、心跳检测、断线重连 | ✅ |
| **StatCard** | `js/components/stat-card.js` | 统计卡片、数字动画、4种变体 | ✅ |
| **FilterBar** | `js/components/filter-bar.js` | 筛选栏、多种类型、搜索重置 | ✅ |
| **DataTable** | `js/components/data-table.js` | 数据表格、选择、排序、分页 | ✅ |

---

## 📚 文档

- **[COMPONENTS.md](./COMPONENTS.md)** - 完整的组件使用文档
  - Router API参考
  - API API参考
  - WebSocket API参考
  - StatCard使用指南
  - FilterBar使用指南
  - DataTable使用指南
  - FAQ常见问题

- **[ENGINEER_A_SUMMARY.md](./ENGINEER_A_SUMMARY.md)** - 工作总结报告
  - 完成任务清单
  - 核心特性说明
  - 代码质量分析
  - 技术栈总结

---

## 💡 常用代码片段

### Router - 路由

```javascript
// 注册路由
router.register('/', () => '<div>首页</div>');
router.register('/dashboard', dashboardPage);

// 初始化
router.init();

// 导航
router.navigate('/dashboard');
```

### API - 请求

```javascript
// 设置基础URL
api.setBaseURL('http://localhost:8013');

// 上传文件
const result = await api.uploadFile(file, {
  target_langs: ['EN', 'JP'],
  rule_set: 'translation'
});

// 获取会话列表
const sessions = await api.getSessions();
```

### WebSocket - 实时通信

```javascript
// 连接
wsManager.connect(sessionId, {
  onProgress: (data) => console.log(data.progress),
  onTaskUpdate: (data) => console.log(data),
  onError: (error) => console.error(error)
});

// 断开
wsManager.disconnect(sessionId);
```

### StatCard - 统计卡片

```javascript
// 创建卡片
const card = new StatCard({
  title: '今日待办',
  value: 3,
  icon: 'bi-clipboard-check',
  trend: { value: 2, direction: 'up' }
});

// 渲染
container.innerHTML = card.render();

// 更新（带动画）
card.update(10, 1000);
```

### FilterBar - 筛选栏

```javascript
const filterBar = new FilterBar({
  filters: [
    { type: 'search', placeholder: '搜索...' },
    { type: 'select', label: '状态', options: ['全部', '执行中', '已完成'] }
  ],
  onSearch: (values) => console.log(values),
  onReset: () => console.log('重置')
});

container.innerHTML = filterBar.render();
filterBar.init();  // 必须调用
```

### DataTable - 数据表格

```javascript
const table = new DataTable({
  columns: [
    { key: 'filename', label: '文件名', sortable: true },
    {
      key: 'status',
      label: '状态',
      render: (val) => `<span class="badge">${val}</span>`
    }
  ],
  data: sessions,
  selectable: true,
  pagination: { pageSize: 10 },
  onSelectionChange: (rows) => console.log(rows)
});

container.innerHTML = table.render();
table.init();  // 必须调用
```

---

## ⚠️ 重要提示

### 组件初始化

FilterBar和DataTable渲染后**必须调用`init()`**：

```javascript
// ❌ 错误 - 事件不会生效
container.innerHTML = filterBar.render();

// ✅ 正确
container.innerHTML = filterBar.render();
filterBar.init();
```

### 路由处理函数

路由处理函数**必须返回HTML**：

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

### API错误处理

所有API调用建议使用try-catch：

```javascript
try {
  const sessions = await api.getSessions();
  // 处理数据
} catch (error) {
  console.error('请求失败:', error.message);
}
```

---

## 🔗 相关链接

### 项目文档
- [任务文档](./docs/TASK_ENGINEER_A.md) - 工程师A任务清单
- [UI设计](./docs/design/UI_DESIGN.md) - UI设计规范
- [技术规范](./docs/technical/FEATURE_SPEC.md) - 技术实现规范

### 外部文档
- [DaisyUI](https://daisyui.com/) - UI组件库
- [Tailwind CSS](https://tailwindcss.com/) - CSS框架
- [Bootstrap Icons](https://icons.getbootstrap.com/) - 图标库

---

## 📞 联系方式

**工程师A**
- 负责：基础架构 + 组件库
- 状态：Week 1-2已完成 ✅
- 支持：可随时解答组件使用问题

**其他工程师**
- 工程师B：核心业务开发
- 工程师C：术语库与分析
- 工程师D：工作台与会话管理

---

## 🎯 下一步

1. ✅ **查看测试页面**: http://localhost:8080/test-components.html
2. ✅ **阅读组件文档**: [COMPONENTS.md](./COMPONENTS.md)
3. ✅ **开始使用组件**: 引入到你的页面
4. ⏳ **反馈问题**: 使用中遇到问题请反馈

---

**最后更新**: 2025-10-17
**版本**: v1.0
**状态**: ✅ 可以开始使用
