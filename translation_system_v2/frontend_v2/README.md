# StringLock - 前端应用

> 🌍 专业的 Excel 文件翻译系统前端应用
>
> 纯 HTML/CSS/JavaScript 实现，无框架依赖

---

## 📖 项目简介

StringLock 是一个为游戏本地化团队设计的专业翻译工作台，支持批量 Excel 文件翻译、实时进度监控、成本分析等功能。

### 核心特性

✅ **零依赖架构** - 纯原生 Web 技术，无需构建工具
✅ **单页应用** - Hash 路由实现流畅的页面切换
✅ **实时通信** - WebSocket 实时进度推送
✅ **响应式设计** - 适配桌面/平板/移动端
✅ **模块化组件** - ES6 Class 组件化开发
✅ **本地存储** - LocalStorage 状态持久化

---

## 🚀 快速开始

### 当前状态

**📚 文档阶段完成** - 需求、设计、技术规格文档已完成
**💻 代码开发** - 待开始

### 查看文档

所有设计文档位于 `docs/` 目录：

```bash
# 查看完整文档导航
cat docs/README.md

# 在浏览器中查看文档
# 可以使用任意 Markdown 查看器或 IDE
```

### 测试页面

测试页面位于 `test_pages/` 目录，可独立运行：

```bash
cd test_pages
python -m http.server 8080
# 访问 http://localhost:8080
```

---

## 📚 文档导航

完整的文档体系请查看 **[docs/README.md](docs/README.md)**

**快速链接**:
- [功能需求](docs/requirements/REQUIREMENTS.md) - 产品功能和用户需求
- [界面设计](docs/design/UI_DESIGN.md) - 设计系统和UI原型
- [Pipeline可视化设计](docs/design/PIPELINE_UX_DESIGN.md) - Pipeline UX设计
- [功能规格](docs/technical/FEATURE_SPEC.md) - 详细技术实现规范
- [后端配置确认](docs/technical/BACKEND_CONFIG_CONFIRMATION.md) - 后端对接说明

---

## 📁 项目结构

```
frontend_v2/
├── README.md                     # 本文档
├── .gitignore                    # Git 忽略规则
│
├── docs/                         # 📚 完整文档体系
│   ├── README.md                 # 文档导航总览
│   ├── requirements/             # 需求文档
│   │   └── REQUIREMENTS.md
│   ├── design/                   # 设计文档
│   │   ├── UI_DESIGN.md
│   │   └── PIPELINE_UX_DESIGN.md
│   └── technical/                # 技术文档
│       ├── FEATURE_SPEC.md
│       └── BACKEND_CONFIG_CONFIRMATION.md
│
├── test_pages/                   # 🧪 测试页面
│   ├── index.html                # 测试页面入口
│   ├── 1_upload_and_split.html
│   ├── 2_execute_transformation.html
│   ├── 4_caps_transformation.html
│   ├── README.md
│   └── docs/                     # 测试相关文档
│       ├── ARCHITECTURE_COMPLIANCE_UPDATE.md
│       └── GLOSSARY_USAGE.md
│
└── nginx.conf                    # Nginx 配置示例
```

**注意**：
- 当前为文档阶段，正式前端代码待开发
- 测试页面可独立运行用于后端API测试

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

### 开发新功能

**参考文档**：
- [功能规格](docs/technical/FEATURE_SPEC.md) - 详细的功能实现说明
- [UI设计](docs/design/UI_DESIGN.md) - 组件库和页面设计
- [需求文档](docs/requirements/REQUIREMENTS.md) - 功能需求和优先级

**开发流程**：
1. 阅读相关需求和设计文档
2. 实现页面组件（参考 FEATURE_SPEC.md 中的代码示例）
3. 编写单元测试
4. 集成到主应用

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

### 当前阶段

**前端代码尚未开发完成**，当前可部署的内容：

1. **文档站点** - 将 `docs/` 目录部署为文档网站
2. **测试页面** - 将 `test_pages/` 部署用于后端API测试

### 未来部署方案

完整前端应用开发完成后，可部署到：
- GitHub Pages
- Vercel
- Netlify
- Nginx/Apache

详细部署配置参考 `nginx.conf.example`

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

- **完整文档**: [docs/README.md](./docs/README.md)
- **后端仓库**: [backend_v2](../backend_v2)
- **问题反馈**: GitHub Issues

---

## 🗺️ 路线图

### Phase 1: 文档阶段 ✅（已完成）

- [x] 功能需求文档（REQUIREMENTS.md）
- [x] UI设计方案（UI_DESIGN.md）
- [x] Pipeline UX设计（PIPELINE_UX_DESIGN.md）
- [x] 功能规格说明（FEATURE_SPEC.md）
- [x] 后端配置确认（BACKEND_CONFIG_CONFIRMATION.md）
- [x] 文档重组和归档

### Phase 2: 基础框架（待开始）

- [ ] 路由系统（Hash Router）
- [ ] 状态管理（LocalStorage）
- [ ] API封装层
- [ ] WebSocket管理器
- [ ] 公共组件库

### Phase 3: 核心页面开发（待开始）

- [ ] 智能工作台（Dashboard）
- [ ] 会话管理（Sessions）
- [ ] 术语库管理（Glossary）
- [ ] 数据分析（Analytics）
- [ ] 翻译流程页面

### Phase 4: 优化与发布（待开始）

- [ ] 性能优化
- [ ] 响应式适配
- [ ] 浏览器兼容性测试
- [ ] 生产环境部署

---

**Version**: 2.0 (文档阶段)
**Last Updated**: 2025-10-17
**Status**: 📚 文档完成，代码开发待启动
