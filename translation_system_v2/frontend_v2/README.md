# Translation Hub - 前端应用

> 🌍 专业的 Excel 文件翻译系统前端应用
>
> 纯 HTML/CSS/JavaScript 实现，无框架依赖

---

## 📖 项目简介

Translation Hub 是一个为游戏本地化团队设计的专业翻译工作台，支持批量 Excel 文件翻译、实时进度监控、成本分析等功能。

### 核心特性

✅ **零依赖架构** - 纯原生 Web 技术，无需构建工具
✅ **单页应用** - Hash 路由实现流畅的页面切换
✅ **实时通信** - WebSocket 实时进度推送
✅ **响应式设计** - 适配桌面/平板/移动端
✅ **模块化组件** - ES6 Class 组件化开发
✅ **本地存储** - LocalStorage 状态持久化

---

## 🚀 快速开始

### 环境要求

- 现代浏览器（Chrome 90+ / Firefox 88+ / Safari 14+ / Edge 90+）
- 本地或远程后端服务（默认 `http://localhost:8013`）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd translation_system/frontend_v2
```

2. **直接运行**

由于是纯静态项目，可以通过以下任意方式运行：

**方式1: Python HTTP Server**
```bash
python -m http.server 8080
# 访问 http://localhost:8080
```

**方式2: Node.js HTTP Server**
```bash
npx http-server -p 8080
# 访问 http://localhost:8080
```

**方式3: VS Code Live Server**
- 安装 Live Server 插件
- 右键 `index.html` → "Open with Live Server"

**方式4: 直接打开**
```bash
# macOS/Linux
open index.html

# Windows
start index.html
```

3. **配置后端地址**

编辑 `js/api.js`，修改 `baseURL`:
```javascript
class API {
  constructor(baseURL = 'http://localhost:8013') {
    this.baseURL = baseURL;
  }
}
```

---

## 📁 项目结构

```
frontend_v2/
├── index.html                    # 主入口文件
├── README.md                     # 本文档
├── FRONTEND_DESIGN.md            # 详细设计文档
│
├── assets/                       # 静态资源
│   ├── images/                   # 图片
│   └── fonts/                    # 字体
│
├── css/                          # 样式文件
│   ├── design-tokens.css         # 设计变量
│   ├── base.css                  # 基础样式
│   ├── layout.css                # 布局
│   ├── components.css            # 组件样式
│   ├── pages.css                 # 页面样式
│   └── utilities.css             # 工具类
│
├── js/                           # JavaScript
│   ├── main.js                   # 主入口
│   ├── router.js                 # 路由管理
│   ├── store.js                  # 状态管理
│   ├── api.js                    # API 封装
│   │
│   ├── utils/                    # 工具函数
│   │   ├── dom.js
│   │   ├── format.js
│   │   ├── validate.js
│   │   └── animation.js
│   │
│   ├── components/               # 可复用组件
│   │   ├── Navbar.js
│   │   ├── Sidebar.js
│   │   ├── Toast.js
│   │   ├── Modal.js
│   │   ├── ProgressBar.js
│   │   └── FileUpload.js
│   │
│   └── pages/                    # 页面组件
│       ├── ProjectCreate.js      # 项目创建
│       ├── TaskConfig.js         # 任务配置
│       ├── TranslationExec.js    # 翻译执行
│       ├── ResultExport.js       # 结果导出
│       └── HistoryManager.js     # 历史管理
│
└── test_pages/                   # 测试页面（参考）
```

---

## 🎯 功能模块

### 1️⃣ 项目创建（#/create）

- 📤 拖拽/点击上传 Excel 文件
- 🔍 自动分析文件结构
- 📊 显示统计信息（Sheet 数量、任务类型分布）
- 🆔 生成 Session ID

### 2️⃣ 任务配置（#/config）

- 🌍 源语言/目标语言选择
- 🧠 上下文提取配置（游戏信息、注释、相邻单元格等）
- ⚡ 实时预估（任务数、耗时、成本）
- ✂️ 任务拆解与进度监控

### 3️⃣ 翻译执行（#/execute）

- 🤖 LLM 引擎选择
- 🚀 实时翻译执行
- 📈 WebSocket 实时进度推送
- ⏸️ 暂停/恢复/停止控制
- 📋 任务流视图（执行中/已完成/失败）

### 4️⃣ 结果导出（#/result）

- 📊 统计看板（任务/成本/性能）
- 📉 数据可视化（柱状图/饼图）
- 💰 成本分析（按语言/任务类型）
- 📥 下载翻译结果

### 5️⃣ 历史管理（#/history）

- 🔍 搜索/筛选会话
- 📋 会话列表表格
- 🗂️ 批量操作（下载/删除）
- 📈 月度统计概览

---

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| HTML5 | 页面结构，语义化标签 |
| CSS3 | 样式设计，Grid/Flexbox 布局 |
| JavaScript ES6+ | 业务逻辑，模块化开发 |
| Fetch API | HTTP 请求 |
| WebSocket API | 实时通信 |
| LocalStorage API | 状态持久化 |
| Canvas API | 数据可视化 |
| File API | 文件上传 |

**不使用**：React / Vue / Angular / jQuery / SASS / Webpack

---

## 🔌 API 集成

### 后端 API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/analyze/upload` | POST | 上传并分析文件 |
| `/api/analyze/status/:id` | GET | 获取分析状态 |
| `/api/tasks/split` | POST | 拆解翻译任务 |
| `/api/tasks/status/:id` | GET | 获取任务状态 |
| `/api/execute/start` | POST | 开始翻译 |
| `/api/execute/pause/:id` | POST | 暂停翻译 |
| `/api/execute/resume/:id` | POST | 恢复翻译 |
| `/api/execute/stop/:id` | POST | 停止翻译 |
| `/api/execute/status/:id` | GET | 获取执行状态 |
| `/api/download/:id` | GET | 下载结果 |
| `/api/download/:id/summary` | GET | 获取汇总 |
| `/api/sessions` | GET | 获取会话列表 |

### WebSocket 端点

| 端点 | 功能 |
|------|------|
| `/ws/progress/:id` | 翻译进度实时推送 |
| `/ws/split/:id` | 任务拆解进度推送 |

---

## 🎨 设计系统

### 颜色规范

```css
/* 主色调 */
--color-primary: #4F46E5;      /* 靛蓝 */
--color-secondary: #10B981;    /* 绿色 */
--color-accent: #F59E0B;       /* 琥珀 */

/* 语义色 */
--color-success: #10B981;
--color-warning: #F59E0B;
--color-error: #EF4444;
--color-info: #3B82F6;

/* 中性色 */
--color-text-primary: #1F2937;
--color-text-secondary: #6B7280;
--color-background: #FFFFFF;
--color-border: #E5E7EB;
```

### 字体规范

```css
--font-family-sans: 'Inter', -apple-system, sans-serif;
--font-size-base: 16px;
--font-size-lg: 18px;
--font-size-xl: 24px;
```

### 间距规范

```css
--spacing-sm: 8px;
--spacing-md: 16px;
--spacing-lg: 24px;
--spacing-xl: 32px;
```

---

## 📱 响应式设计

### 断点

```css
/* 移动端 */
@media (max-width: 767px) { }

/* 平板端 */
@media (min-width: 768px) and (max-width: 1023px) { }

/* 桌面端 */
@media (min-width: 1024px) { }
```

### 布局适配

- **桌面端**：侧边栏 + 主内容区
- **平板端**：可折叠侧边栏
- **移动端**：全屏抽屉菜单 + 底部导航

---

## 🔧 开发指南

### 代码规范

```javascript
// 变量命名：camelCase
const userName = 'John';

// 常量命名：UPPER_SNAKE_CASE
const API_BASE_URL = 'http://localhost:8013';

// 类命名：PascalCase
class UserManager {}

// 文件命名：kebab-case
// project-create.js, task-config.js
```

### Git 提交规范

```
feat: 新功能
fix: 修复 Bug
docs: 文档更新
style: 代码格式调整
refactor: 重构代码
perf: 性能优化
test: 测试相关
chore: 构建/工具链相关

示例：
feat(pages): 实现项目创建页面
fix(api): 修复文件上传超时问题
```

### 添加新页面

1. 在 `js/pages/` 创建页面组件
2. 在 `router.js` 注册路由
3. 在 `pages.css` 添加页面样式
4. 在 `Sidebar.js` 添加导航链接

```javascript
// 1. 创建页面组件
class NewPage {
  constructor(container) {
    this.container = container;
  }

  render() {
    this.container.innerHTML = `<h1>New Page</h1>`;
  }

  destroy() {
    this.container.innerHTML = '';
  }
}

// 2. 注册路由
router.register('/new', NewPage);
```

---

## 🧪 测试

### 手动测试

1. **功能测试**：按照用户流程完整测试
2. **兼容性测试**：Chrome / Firefox / Safari / Edge
3. **响应式测试**：调整窗口大小测试布局
4. **性能测试**：检查加载速度和运行流畅度

### 测试页面

`test_pages/` 目录包含独立的测试页面：
- `1_upload_analyze.html` - 上传分析测试
- `2_task_split.html` - 任务拆解测试
- `3_execute_translation.html` - 翻译执行测试
- `4_download_export.html` - 下载导出测试

---

## 📦 部署

### 静态托管

所有文件均为静态资源，可部署到：

- **GitHub Pages**
  ```bash
  git push origin main
  # 在仓库设置中启用 GitHub Pages
  ```

- **Vercel**
  ```bash
  vercel deploy
  ```

- **Netlify**
  - 拖拽 `frontend_v2` 文件夹到 Netlify

- **Nginx**
  ```nginx
  server {
    listen 80;
    root /var/www/translation-hub/frontend_v2;
    index index.html;

    location / {
      try_files $uri $uri/ /index.html;
    }
  }
  ```

### 生产环境配置

1. 修改 `js/api.js` 中的 `baseURL` 为生产环境地址
2. 启用 HTTPS
3. 配置 CDN 加速静态资源
4. 启用 Gzip 压缩

---

## 🐛 常见问题

### Q1: 页面空白无法加载
**A**: 检查浏览器控制台是否有 CORS 错误，确保后端已配置 CORS

### Q2: WebSocket 连接失败
**A**: 检查后端 WebSocket 服务是否启动，确认端口号正确

### Q3: 文件上传失败
**A**: 检查文件大小是否超过限制（默认 100MB），检查文件格式是否为 .xlsx/.xls

### Q4: LocalStorage 数据丢失
**A**: 某些浏览器隐私模式会禁用 LocalStorage，请使用普通模式

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发流程

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 代码审查标准

- ✅ 符合代码规范
- ✅ 通过功能测试
- ✅ 无浏览器控制台错误
- ✅ 响应式布局正常
- ✅ 代码注释完整

---

## 📄 许可证

本项目采用 MIT 许可证

---

## 📞 联系方式

- **文档**: [FRONTEND_DESIGN.md](./FRONTEND_DESIGN.md)
- **后端仓库**: [backend_v2](../backend_v2)
- **问题反馈**: GitHub Issues

---

## 🗺️ 路线图

- [x] 设计文档
- [ ] 基础框架（Router / Store / API）
- [ ] 公共组件（Toast / Modal / ProgressBar）
- [ ] 页面1：项目创建
- [ ] 页面2：任务配置
- [ ] 页面3：翻译执行
- [ ] 页面4：结果导出
- [ ] 页面5：历史管理
- [ ] 性能优化
- [ ] 国际化支持
- [ ] 主题切换（暗色模式）

---

**Version**: 2.0
**Last Updated**: 2025-10-03
**Powered by**: Pure Web Technologies ❤️
