# 游戏本地化翻译系统 - 前端

## 📋 项目简介

基于纯HTML + 原生JavaScript的高效Web应用，为游戏本地化团队提供直观的Excel文件翻译服务。零依赖，即开即用。

## 🚀 超快速启动

### 方法1: Python HTTP服务器 (推荐)
```bash
python3 start-server.py
```

### 方法2: 任何HTTP服务器
```bash
# 使用Python内置服务器
python3 -m http.server 3000

# 或使用PHP
php -S localhost:3000

# 或直接打开HTML文件
open index.html
```

## 🌐 访问地址

- **主应用**: http://localhost:3000/index.html
- **调试工具**: http://localhost:3000/index-debug.html
- **后端API**: http://127.0.0.1:8101

## 📁 项目结构 (重构后)

```
frontend/
├── index.html              # 主应用 (单页面应用)
├── index-debug.html        # 调试工具页面
├── start-server.py         # Python HTTP服务器
├── public/                 # 静态资源
│   └── simple-test.html    # 基础API测试页面
├── FRONTEND_PRODUCT_DESIGN.md      # 产品设计方案
├── FRONTEND_DEVELOPMENT_TASKS.md   # 开发任务列表
└── README.md               # 项目说明
```

## 🎨 技术架构 (重构后)

- **前端**: 纯HTML + CSS + 原生JavaScript
- **UI样式**: CSS Variables + 响应式设计
- **HTTP客户端**: 原生 fetch API
- **状态管理**: 原生JavaScript对象
- **路由**: 基于锚点的SPA路由
- **调试工具**: 内置日志系统

## 📖 相关文档

- [前端产品设计方案](./FRONTEND_PRODUCT_DESIGN.md)
- [前端开发任务列表](./FRONTEND_DEVELOPMENT_TASKS.md)
- [后端API文档](../backend/API_DOCUMENTATION.md)