# Translation System Frontend V2

## 🎯 项目概述

Translation System的前端项目，采用**纯 React 18 + Vite + TypeScript**技术栈，提供Excel文件翻译的完整用户界面。

## 🚀 技术栈

- **框架**: React 18.2
- **构建工具**: Vite 5.0
- **语言**: TypeScript 5.0
- **路由**: React Router 6
- **状态管理**: Zustand 4.4
- **UI组件**: Ant Design 5.12
- **HTTP客户端**: Axios
- **样式**: CSS Modules + Tailwind CSS

## ⚡ 快速开始

### 1. 项目已初始化完成 ✅

项目结构已创建完成，包含：
- ✅ React 18 + Vite + TypeScript 配置
- ✅ 路由系统（React Router 6）
- ✅ 状态管理（Zustand）
- ✅ UI组件库（Ant Design 5）
- ✅ 模块化架构
- ✅ 上传模块示例

### 2. 安装依赖

```bash
# 安装所有依赖
npm install

# 或使用 yarn
yarn install

# 或使用 pnpm
pnpm install
```

### 3. 启动开发服务器

```bash
# 确保后端服务已启动（在 backend_v2 目录）
cd ../backend_v2
python main.py

# 在新终端启动前端开发服务器
cd frontend_v2
npm run dev

# 项目将运行在 http://localhost:3000
```

### 4. 构建部署

```bash
# 构建生产版本
npm run build

# 预览生产版本
npm run preview

# 构建产物在 dist/ 目录
```

## 📁 项目结构

```
frontend_v2/
├── src/
│   ├── modules/          # 业务模块（完全独立）
│   │   ├── upload/       # 上传模块
│   │   ├── analysis/     # 分析模块
│   │   ├── translation/  # 翻译模块
│   │   ├── monitor/      # 监控模块
│   │   └── export/       # 导出模块
│   │
│   ├── shared/           # 共享资源
│   │   ├── components/   # 通用组件
│   │   ├── hooks/        # 通用Hooks
│   │   ├── utils/        # 工具函数
│   │   └── types/        # 类型定义
│   │
│   ├── core/             # 核心配置
│   │   ├── api/          # API客户端
│   │   ├── router/       # 路由配置
│   │   └── constants/    # 常量定义
│   │
│   ├── pages/            # 页面组件
│   ├── styles/           # 全局样式
│   ├── App.tsx           # 根组件
│   └── main.tsx          # 入口文件
│
├── public/               # 静态资源
├── tests/                # 测试文件
├── quick_test.html       # API快速测试工具
├── API验证清单.md        # API接口文档
├── 项目实施方案.md       # 详细开发计划
└── README.md            # 本文件
```

## 🎯 核心功能模块

### 1. 上传模块（Upload）
- 支持拖拽上传Excel文件
- 文件格式和大小验证
- 上传进度实时显示
- 会话ID自动管理

### 2. 分析模块（Analysis）
- Excel内容预览
- 颜色识别和标记
- 语言自动检测
- 任务统计展示

### 3. 翻译模块（Translation）
- LLM配置管理
- 批量翻译执行
- 暂停/恢复功能
- 错误重试机制

### 4. 监控模块（Monitor）
- 实时进度展示（WebSocket）
- 性能指标监控
- 成本实时计算
- 系统资源监控

### 5. 导出模块（Export）
- 翻译结果预览
- Excel格式保持
- 批量下载支持
- 历史记录管理

## 🛠️ 开发模式说明

### 模块化开发原则
1. **独立性**: 每个模块包含自己的 api、store、hooks、components
2. **单向依赖**: 严格遵循 pages → modules → shared → core 的依赖方向
3. **接口导出**: 模块只通过 index.ts 导出公共接口
4. **避免耦合**: 模块间通过事件或公共状态通信，不直接引用

### 状态管理策略
- **局部状态**: useState（组件内部）
- **模块状态**: Zustand store（模块内部）
- **全局状态**: 尽量避免，必要时使用共享store

### 开发工作流
```bash
# 1. 启动后端服务
cd ../backend_v2 && python main.py

# 2. 启动前端开发
npm run dev

# 3. 打开浏览器
http://localhost:3000
```

## 🧪 测试策略

### 使用快速测试工具
1. 打开 `quick_test.html` 在浏览器中
2. 配置后端地址（默认 http://localhost:8000）
3. 按顺序测试各个API接口
4. 在API验证清单中记录测试结果

### 测试Excel文件要求
- 包含多个Sheet页
- 黄色单元格：需要翻译的中文文本
- 蓝色单元格：需要翻译的术语
- 文件大小：建议 < 10MB

## 📊 性能优化

- **代码分割**: 路由级别懒加载
- **虚拟滚动**: 大数据列表展示
- **请求缓存**: 避免重复请求
- **防抖节流**: 优化频繁操作
- **Web Worker**: 处理大量数据

## 🚀 部署指南

```bash
# 1. 构建生产版本
npm run build

# 2. 测试生产版本
npm run preview

# 3. 部署到Nginx
cp -r dist/* /usr/share/nginx/html/

# 4. 配置Nginx反向代理
location /api {
    proxy_pass http://localhost:8000;
}
```

## 📝 开发进度

- [x] 技术方案确定
- [x] 项目结构设计
- [x] API文档整理
- [x] 测试工具完成
- [ ] 项目初始化
- [ ] 核心模块开发
- [ ] 功能集成测试
- [ ] 性能优化
- [ ] 生产部署

## 💡 注意事项

1. **React 18 + Vite** 方案已确定，不使用Next.js
2. **模块化架构**确保代码可维护性
3. **TypeScript**提供类型安全
4. **Zustand**轻量级状态管理
5. **Ant Design**提供完整UI组件

---

*技术栈: React 18 + Vite + TypeScript + Zustand + Ant Design*