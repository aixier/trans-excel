# 游戏本地化智能翻译系统 前端架构设计

本方案与后端文档 `translation_system/TRANSLATION_SYSTEM_ARCHITECTURE.md` 对齐，覆盖前端的目标、技术选型、信息架构、页面路由、关键组件、数据与状态、实时更新、性能与可访问性、配置与部署、MVP 范围与迭代计划。

## 1. 目标与范围
- 提供“上传 → 分析 → 翻译执行 → 进度监控 → 下载”的端到端闭环
- 对游戏本地化场景友好：占位符保护可视化、颜色标记识别、术语提示、区域化配置
- 面向三类角色：项目负责人、译员、审校
- 与后端 API/WS 稳定对接，并保持良好的可观测性（状态、日志、统计）

## 2. 技术选型与原则
- 框架：React 18 + TypeScript + Vite
- UI：Ant Design（表单、布局、上传、反馈）
- 表格：AG Grid Community（MIT，虚拟滚动、单元格自定义渲染、编辑）
- 数据：Axios + TanStack Query（请求、缓存、重试、错误边界）
- 路由：React Router v6
- 轻量状态：Zustand（全局 UI/偏好/临时会话状态）
- 国际化：react-i18next（中英起步，可扩）
- 实时：WebSocket 优先，SSE/轮询降级（统一订阅 Hook）
- 测试：Vitest + @testing-library/react、Playwright（关键流程 e2e）
- 原则：简洁、类型安全、隔离关注点（feature-first）、可扩展、可观测

## 3. 信息架构（IA）与导航
- 顶部主导航：Dashboard / Projects / Tasks / Workspace / Terminology / Settings
- 侧边上下文导航：项目详情内的 Versions / Files / Tasks / Metrics
- 面包屑反映层级：Projects > ProjectName > VersionName > Task

## 4. 路由与页面
- /dashboard
  - 概览卡片：任务状态统计（pending/analyzing/translating/…）
  - 指标：近 24h API 调用、平均响应时长、成功率
  - 最近任务列表（可跳转）
- /projects
  - 项目列表（搜索/筛选/分页），新建项目弹窗
- /projects/:projectId
  - 项目概览、版本列表（创建版本）、文件列表（source/terminology/completed）
  - 上传对话框：文件 + target_languages + batch_size + max_concurrent + region_code
- /tasks
  - 任务列表（状态/时间区间/用户筛选），支持取消/跳转
- /tasks/:taskId
  - 任务进度：total/translated/iteration/max/完成度/ETA
  - 实时日志摘要与错误提示，操作：取消、下载
- /workspace/:taskId（增强型工作台，可后置）
  - Excel 结构预览（Sheet/列类型/语言识别/可翻译行）
  - 翻译网格：源/目标列、颜色标记、占位符高亮与校验、术语建议侧栏
- /terminology/:projectId
  - 术语列表、导入 Excel 术语、搜索、分类与优先级管理
- /settings
  - 区域/语言偏好、UI 语言、下载格式、个性化

## 5. 目录结构（建议）
```
web/
  src/
    api/                   # axios 实例与 API 模块
    components/            # 通用 UI（UploadCard、TaskProgress、RegionSelector 等）
    features/              # 领域功能（ExcelAnalysis、TerminologySuggest、PlaceholderGuard）
    pages/                 # 路由页面
      Dashboard/
      Projects/
      ProjectDetail/
      Tasks/
      TaskDetail/
      Workspace/
      Terminology/
      Settings/
    hooks/                 # useTaskSubscription、usePagination 等
    store/                 # Zustand stores（ui、session、preferences）
    types/                 # 与后端对齐的 TS 类型
    utils/                 # 占位符/颜色/语言/下载 工具
    i18n/
  index.html
  vite.config.ts
```

## 6. 关键组件
- UploadCard
  - AntD Upload.Dragger + 表单项：目标语言、多并发、batch、region
  - 成功后跳转任务详情
- TaskProgress
  - 状态条、百分比、ETA、状态标签；接收订阅更新
- ExcelAnalysisPanel
  - 多 Sheet 切换、列类型/语言标识、可翻译行数
- TranslationGrid（AG Grid）
  - 单元格渲染：背景色映射（黄=modify/蓝=shorten/绿=completed/红=error）
  - 占位符高亮/校验：%s/%d/{}/<tag>/\n 等
  - 术语建议侧栏：来源术语库，一键应用
  - 大数据虚拟滚动、键盘导航、粘贴
- RegionSelector
  - 绑定 region_code 与语言（与后端地区模型一致）

## 7. 类型与 API 契约（与后端对齐）
```ts
// types/task.ts
export type TaskStatus =
  | 'pending'
  | 'uploading'
  | 'analyzing'
  | 'translating'
  | 'iterating'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface TaskResponse {
  task_id: string;
  status: TaskStatus;
  message: string;
  created_at: string; // ISO
}

export interface TaskProgress {
  total_rows: number;
  translated_rows: number;
  current_iteration: number;
  max_iterations: number;
  completion_percentage: number;
  estimated_time_remaining?: number; // seconds
}

export interface TaskStatusResponse {
  task_id: string;
  status: TaskStatus;
  progress: TaskProgress;
  error_message?: string;
  created_at: string;
  updated_at: string;
  download_url?: string;
}
```

- 上传与任务
  - POST `/api/v1/translation/upload`（multipart/form-data）
  - GET `/api/v1/translation/task/{task_id}/status`
  - GET `/api/v1/translation/task/{task_id}/download`
  - POST `/api/v1/translation/task/{task_id}/cancel`
  - GET `/api/v1/translation/tasks`
- 项目与版本（建议按后端项目管理器补齐 REST）
  - POST/GET `/api/v1/projects`
  - GET `/api/v1/projects/{project_id}`（含版本与统计）
  - POST `/api/v1/projects/{project_id}/versions`
  - POST `/api/v1/projects/{project_id}/versions/{version_id}/files`
- 术语（与 TerminologyManager 对齐）
  - GET/POST `/api/v1/projects/{project_id}/terminology`
  - POST `/api/v1/projects/{project_id}/terminology/import`

## 8. 实时更新策略
- 优先 WebSocket：`/ws/tasks/{task_id}`（建议后端提供）；消息体对齐 `TaskStatusResponse`
- 回退策略：SSE 其次，最终退化到轮询（2–5s）
- 统一 Hook：`useTaskSubscription(taskId)` 封装 WS/SSE/轮询，向外暴露最新状态与错误

## 9. 数据与状态管理
- Axios 实例：拦截器注入 `Authorization`，统一错误码处理
- TanStack Query：以 `['task', taskId]`、`['project', id]` 等为 key；开启重试与缓存失效策略
- Zustand：UI 偏好（主题/尺寸/语言）、面板开合、
- 错误边界：页面级与区块级，支持“复制诊断信息”

## 10. 性能与可访问性
- 大列表分页与懒加载；Grid 虚拟滚动与惰性渲染
- 编辑防抖（300ms），批量操作分片提交（后续）
- 占位符校验在提交与导出前强制通过
- a11y：键盘导航、ARIA 标签、颜色对比度达标；状态变化播报（live region）

## 11. 安全与权限
- 认证：从存储读取 Token 注入请求头
- 下载：后端返回受控 `download_url`（含签名/有效期）
- 权限：仅任务创建者/项目成员可取消/下载/查看敏感信息

## 12. 配置与环境
- `.env`
  - `VITE_API_BASE_URL=https://api.example.com`
  - `VITE_WS_BASE_URL=wss://api.example.com`
- 不同环境（dev/staging/prod）通过环境变量切换

## 13. 开发、测试与质量
- 脚本
  - `dev`: Vite 本地开发
  - `build`: 生产构建
  - `test`: 单测
  - `e2e`: 端到端关键流程（上传 → 进度 → 下载）
- Lint/Format：ESLint + Prettier，commit hook 校验
- 视觉回归（可选）：Playwright 截图比对关键界面

## 14. 部署与运维
- 构建产物静态托管（OSS/CDN）；网关代理 API 与 WS
- 缓存策略：HTML 不缓存、静态资源长缓存（带 content hash）
- 监控：埋点（上传开始/失败、任务完成、下载），前端错误上报

## 15. MVP 范围（建议 2 周）
- 上传 → 任务创建 → 状态轮询/订阅 → 下载闭环
- 项目/版本/文件基础视图
- 任务列表与详情页（取消/错误提示）
- Excel 结构只读预览 + 颜色/占位符高亮（编辑后置）

## 16. 后续迭代
- 工作台可编辑、增量保存、服务端分页
- 术语管理全流程与建议一键应用
- 审校流（标注/评论/历史），多角色权限
- 高级性能：断点续传、批量并发控制 UI、离线草稿

## 17. 风险与回退
- WebSocket 不可用：自动退化到轮询
- 大文件预览性能：限制首屏加载与分片渲染；必要时仅提供下载与离线处理
- AG Grid 替代：若需更轻量，可切换 TanStack Table + react-virtual（功能减少）

---

与后端方案 `translation_system/TRANSLATION_SYSTEM_ARCHITECTURE.md` 的接口、任务状态模型保持一一对应，前端在显示与交互层面强化游戏本地化特性（占位符保护、颜色标记、术语建议与区域化上下文），确保交付稳定、可扩展、可观测的产品体验。
