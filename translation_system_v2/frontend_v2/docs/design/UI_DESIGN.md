# UI设计方案
## StringLock - 界面设计与交互规范

> **文档版本**: v1.0
> **最后更新**: 2025-10-17
> **设计师**: UX Team
> **设计系统**: 基于DaisyUI + Tailwind CSS

---

## 📋 目录

1. [设计理念](#设计理念)
2. [设计系统](#设计系统)
3. [页面原型](#页面原型)
4. [组件库](#组件库)
5. [交互动效](#交互动效)
6. [响应式设计](#响应式设计)

---

## 🎨 设计理念

### 核心原则

1. **简洁高效** - 减少认知负担，突出核心操作
2. **数据可视化** - 用图表和进度条代替冗长文字
3. **即时反馈** - 所有操作都有明确的视觉反馈
4. **一致性** - 统一的视觉语言和交互模式
5. **可访问性** - 支持键盘操作，良好的对比度

### 设计参考

**对标产品**:
- **RuoYi** - 侧边栏布局、表格样式
- **Ant Design Pro** - 工作台卡片、数据统计
- **Vercel Dashboard** - 现代感、微动效

### 视觉风格

**风格定位**: 现代、专业、科技感

**设计关键词**:
- 扁平化（Flat Design）
- 卡片式（Card-based）
- 数据驱动（Data-driven）
- 响应式（Responsive）

---

## 🎨 设计系统

### 1. 色彩规范

#### 主题色

```css
/* Light Mode (默认) */
--primary: #4F46E5;        /* 靛蓝 - 主要操作 */
--secondary: #10B981;      /* 绿色 - 次要操作 */
--accent: #F59E0B;         /* 琥珀 - 强调 */

/* 语义色 */
--success: #10B981;        /* 成功 */
--warning: #F59E0B;        /* 警告 */
--error: #EF4444;          /* 错误 */
--info: #3B82F6;           /* 信息 */

/* 中性色 */
--base-100: #FFFFFF;       /* 背景 */
--base-200: #F9FAFB;       /* 次级背景 */
--base-300: #E5E7EB;       /* 边框 */
--base-content: #1F2937;   /* 文字 */
```

#### 暗色主题

```css
/* Dark Mode */
--primary: #6366F1;
--base-100: #1F2937;
--base-200: #111827;
--base-300: #374151;
--base-content: #F9FAFB;
```

#### 状态色使用规范

| 状态 | 颜色 | 使用场景 |
|------|------|----------|
| 待配置 | `info` (蓝色) | 会话状态Badge |
| 执行中 | `warning` (黄色) | 进度中状态 |
| 已完成 | `success` (绿色) | 成功状态 |
| 失败 | `error` (红色) | 错误状态 |
| 暂停 | `base-300` (灰色) | 暂停状态 |

### 2. 字体规范

#### 字体族

```css
/* 主字体：无衬线字体 */
--font-sans: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont,
             'Segoe UI', 'Microsoft YaHei', sans-serif;

/* 等宽字体：代码、Session ID */
--font-mono: 'Fira Code', 'Consolas', 'Monaco', monospace;

/* 数字字体：统计数据 */
--font-number: 'SF Mono', 'Roboto Mono', monospace;
```

#### 字号规范

| 用途 | 字号 | 行高 | 权重 |
|------|------|------|------|
| 页面标题 | 24px | 32px | 700 (Bold) |
| 卡片标题 | 18px | 24px | 600 (Semibold) |
| 正文 | 14px | 20px | 400 (Regular) |
| 辅助文字 | 12px | 16px | 400 (Regular) |
| 大数字 | 32px | 40px | 700 (Bold) |

### 3. 间距规范

**8px栅格系统**:

```css
--spacing-0: 0px;
--spacing-1: 4px;     /* 0.5 × 8 */
--spacing-2: 8px;     /* 1 × 8 */
--spacing-3: 12px;    /* 1.5 × 8 */
--spacing-4: 16px;    /* 2 × 8 */
--spacing-6: 24px;    /* 3 × 8 */
--spacing-8: 32px;    /* 4 × 8 */
--spacing-12: 48px;   /* 6 × 8 */
--spacing-16: 64px;   /* 8 × 8 */
```

**使用规范**:
- 卡片内边距: `spacing-6` (24px)
- 卡片间距: `spacing-4` (16px)
- 表单字段间距: `spacing-4` (16px)
- 按钮内边距: `spacing-3` × `spacing-6` (12px × 24px)

### 4. 圆角规范

```css
--rounded-sm: 4px;    /* 小圆角 - Badge */
--rounded-md: 8px;    /* 中圆角 - 按钮、输入框 */
--rounded-lg: 12px;   /* 大圆角 - 卡片 */
--rounded-xl: 16px;   /* 超大圆角 - Modal */
```

### 5. 阴影规范

```css
/* 卡片阴影 */
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);

/* 悬浮阴影 */
--shadow-hover: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
```

### 6. 图标规范

**图标库**: Bootstrap Icons (已使用)

**尺寸规范**:
- 小图标: 16px (按钮内)
- 中图标: 20px (菜单项)
- 大图标: 24px (页面标题)
- 超大图标: 48px (空状态)

**常用图标映射**:
```javascript
const ICONS = {
  // 功能图标
  create: 'bi-plus-circle',
  upload: 'bi-cloud-upload',
  download: 'bi-download',
  delete: 'bi-trash',
  edit: 'bi-pencil',
  search: 'bi-search',
  filter: 'bi-funnel',

  // 状态图标
  success: 'bi-check-circle-fill',
  error: 'bi-x-circle-fill',
  warning: 'bi-exclamation-triangle-fill',
  info: 'bi-info-circle-fill',

  // 导航图标
  dashboard: 'bi-grid-3x3-gap',
  sessions: 'bi-folder',
  glossary: 'bi-book',
  analytics: 'bi-bar-chart',
  settings: 'bi-gear',
}
```

---

## 📱 页面原型

### 1️⃣ 智能工作台（Dashboard）

#### 布局结构

```
┌────────────────────────────────────────────────────────────┐
│ 📊 工作台                                         [@头像 ▼] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────┬──────────┬──────────┬──────────┐           │
│  │📋 今日待办│⚡ 执行中 │✅ 本月完成│💰 本月成本│           │
│  │   3 个   │   1 个   │  24 个   │ $12.50   │           │
│  │  ↑ 2     │  60% ▬▬  │  ↑ 15%   │ 25% 预算 │           │
│  └──────────┴──────────┴──────────┴──────────┘           │
│                                                            │
│  ┌─ 最近项目 ─────────────────── [查看全部 →] ┐           │
│  │                                              │           │
│  │  ┌─┬──────────┬────────┬────────┬──────┐  │           │
│  │  │☐│ 文件名   │ 状态   │ 进度   │ 操作 │  │           │
│  │  ├─┼──────────┼────────┼────────┼──────┤  │           │
│  │  │☐│game.xlsx │⚠️执行中│████ 60%│ 查看 │  │           │
│  │  │☐│ui.xlsx   │✅已完成│████100%│ 下载 │  │           │
│  │  │☐│skill.xlsx│📝待配置│──── 0% │ 继续 │  │           │
│  │  └─┴──────────┴────────┴────────┴──────┘  │           │
│  └──────────────────────────────────────────┘           │
│                                                            │
│  ┌─ 快速操作 ────────────────────────────────┐           │
│  │  [➕ 新建翻译]  [📖 术语库]  [📊 统计]    │           │
│  └──────────────────────────────────────────┘           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

#### 详细设计

**核心指标卡片**:
```html
<div class="stats shadow-md bg-base-100 rounded-lg">
  <div class="stat">
    <div class="stat-figure text-primary">
      <i class="bi bi-clipboard-check text-4xl"></i>
    </div>
    <div class="stat-title">今日待办</div>
    <div class="stat-value text-primary">3</div>
    <div class="stat-desc">
      <span class="text-success">↑ 2</span> 较昨日
    </div>
  </div>

  <!-- 其他3个stat -->
</div>
```

**项目列表表格**:
```html
<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <div class="flex items-center justify-between mb-4">
      <h2 class="card-title">最近项目</h2>
      <a href="#/sessions" class="link link-primary">
        查看全部 <i class="bi bi-arrow-right"></i>
      </a>
    </div>

    <table class="table table-zebra">
      <thead>
        <tr>
          <th><input type="checkbox" class="checkbox checkbox-sm"/></th>
          <th>文件名</th>
          <th>状态</th>
          <th>进度</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><input type="checkbox" class="checkbox checkbox-sm"/></td>
          <td>
            <div class="flex items-center gap-2">
              <i class="bi bi-file-earmark-excel text-success"></i>
              <span class="font-medium">game.xlsx</span>
            </div>
          </td>
          <td>
            <span class="badge badge-warning gap-2">
              <i class="bi bi-lightning-fill"></i>
              执行中
            </span>
          </td>
          <td>
            <div class="flex items-center gap-2">
              <progress class="progress progress-warning w-20" value="60" max="100"></progress>
              <span class="text-sm">60%</span>
            </div>
          </td>
          <td>
            <button class="btn btn-sm btn-ghost">
              <i class="bi bi-eye"></i>
              查看
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

---

### 2️⃣ 会话管理（Sessions）

#### 布局结构

```
┌────────────────────────────────────────────────────────────┐
│ 📁 会话管理                                                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─ 筛选工具栏 ─────────────────────────────────────┐     │
│  │ 🔍 [搜索文件名...] │ [时间范围▼] [状态▼] [搜索] │     │
│  └───────────────────────────────────────────────────┘     │
│                                                            │
│  ┌─ 批量操作栏（选中时显示） ──────────────────────┐     │
│  │ 已选 2 个  [批量下载] [批量删除] [取消选择]     │     │
│  └───────────────────────────────────────────────────┘     │
│                                                            │
│  ┌─ 会话列表 ─────────────────────────────────────┐     │
│  │  ┌─┬──────────┬────────┬────────┬──────────┐  │     │
│  │  │☑│ 文件名   │ 状态   │ 进度   │ 更新时间 │  │     │
│  │  ├─┼──────────┼────────┼────────┼──────────┤  │     │
│  │  │☑│game.xlsx │⚠️执行中│████ 60%│ 5分钟前  │  │     │
│  │  │☐│ui.xlsx   │✅已完成│████100%│ 2小时前  │  │     │
│  │  │☑│skill.xlsx│❌失败  │████ 85%│ 昨天     │  │     │
│  │  └─┴──────────┴────────┴────────┴──────────┘  │     │
│  │                                                │     │
│  │  [← 上一页]  1 / 10  [下一页 →]               │     │
│  └───────────────────────────────────────────────┘     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

#### 筛选栏设计

```html
<div class="card bg-base-100 shadow-md mb-4">
  <div class="card-body p-4">
    <div class="flex flex-wrap gap-2 items-center">
      <!-- 搜索框 -->
      <div class="form-control flex-1 min-w-[200px]">
        <div class="input-group">
          <span><i class="bi bi-search"></i></span>
          <input
            type="text"
            placeholder="搜索文件名..."
            class="input input-bordered input-sm w-full"
          />
        </div>
      </div>

      <!-- 时间范围 -->
      <select class="select select-bordered select-sm">
        <option>全部时间</option>
        <option>今天</option>
        <option>本周</option>
        <option>本月</option>
        <option>自定义</option>
      </select>

      <!-- 状态筛选 -->
      <select class="select select-bordered select-sm">
        <option>全部状态</option>
        <option>待配置</option>
        <option>执行中</option>
        <option>已完成</option>
        <option>失败</option>
      </select>

      <!-- 搜索按钮 -->
      <button class="btn btn-primary btn-sm">
        <i class="bi bi-search"></i>
        搜索
      </button>

      <!-- 重置按钮 -->
      <button class="btn btn-ghost btn-sm">
        <i class="bi bi-arrow-clockwise"></i>
        重置
      </button>
    </div>
  </div>
</div>
```

#### 会话详情侧边栏

```
┌────────────────────────┐
│ 会话详情          [✕] │
├────────────────────────┤
│                        │
│ 📁 基本信息            │
│ ─────────────────────  │
│ 文件名: game.xlsx      │
│ Session ID: abc123...  │
│ 上传时间: 2025-10-17   │
│ 文件大小: 2.5 MB       │
│                        │
│ ⚙️ 配置信息            │
│ ─────────────────────  │
│ 源语言: CH             │
│ 目标语言: EN, JP       │
│ LLM模型: qwen-plus     │
│ 术语库: 游戏通用术语   │
│                        │
│ 📊 执行统计            │
│ ─────────────────────  │
│ 总任务: 1200           │
│ 已完成: 720 (60%)      │
│ 处理中: 80             │
│ 待处理: 380            │
│ 失败: 20               │
│                        │
│ 💰 成本统计            │
│ ─────────────────────  │
│ LLM调用: 45次          │
│ Token消耗: 125K        │
│ 预估成本: $2.30        │
│                        │
│ ⏱️ 操作日志            │
│ ─────────────────────  │
│ ✓ 15:30 翻译完成       │
│ ⚡ 15:15 开始执行       │
│ ⚙️ 15:10 配置完成       │
│ 📤 15:05 上传完成       │
│                        │
│ [查看详情] [下载结果]  │
│                        │
└────────────────────────┘
```

---

### 3️⃣ 术语库管理（Glossary）

#### 布局结构

```
┌────────────────────────────────────────────────────────────┐
│ 📖 术语库管理                                              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─ 术语库列表 ─┐  ┌─ 术语条目 ────────────────────────┐  │
│  │              │  │                                    │  │
│  │ [+ 新建]     │  │ 游戏通用术语  (500条) [导入▼] [导出] │
│  │              │  │                                    │  │
│  │ ● 游戏通用   │  │ 🔍 [搜索术语...]  [+ 新增术语]    │  │
│  │   500 条     │  │                                    │  │
│  │   ✓ 激活中   │  │ ┌──────┬────┬────┬────┬─────┐    │  │
│  │              │  │ │源术语│ EN │ JP │ TH │ 操作│    │  │
│  │ ○ UI专用     │  │ ├──────┼────┼────┼────┼─────┤    │  │
│  │   120 条     │  │ │攻击力│ ATK│攻撃力│พลัง│[编辑]│    │  │
│  │              │  │ │防御力│ DEF│防御力│ป้องกัน│[编辑]│  │
│  │ ○ 角色名称   │  │ │生命值│ HP │体力 │HP  │[编辑]│    │  │
│  │   80 条      │  │ └──────┴────┴────┴────┴─────┘    │  │
│  │              │  │                                    │  │
│  │              │  │ [1] [2] [3] ... [50]  [下一页→]  │  │
│  │              │  │                                    │  │
│  └──────────────┘  └────────────────────────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

#### 术语编辑Modal

```html
<div class="modal modal-open">
  <div class="modal-box w-11/12 max-w-3xl">
    <h3 class="font-bold text-lg mb-4">
      <i class="bi bi-pencil"></i>
      编辑术语
    </h3>

    <div class="grid grid-cols-1 gap-4">
      <!-- 源术语 -->
      <div class="form-control">
        <label class="label">
          <span class="label-text">源术语 (中文) <span class="text-error">*</span></span>
        </label>
        <input
          type="text"
          placeholder="例如：攻击力"
          class="input input-bordered"
          value="攻击力"
        />
      </div>

      <!-- 目标语言（多语言标签页） -->
      <div class="form-control">
        <label class="label">
          <span class="label-text">目标语言翻译</span>
        </label>

        <div class="tabs tabs-boxed mb-2">
          <a class="tab tab-active">English</a>
          <a class="tab">日本語</a>
          <a class="tab">ไทย</a>
          <a class="tab">Português</a>
        </div>

        <input
          type="text"
          placeholder="英文翻译"
          class="input input-bordered"
          value="ATK"
        />
      </div>

      <!-- 备注 -->
      <div class="form-control">
        <label class="label">
          <span class="label-text">备注</span>
        </label>
        <textarea
          class="textarea textarea-bordered"
          placeholder="使用说明、注意事项等"
        >属性名称，常用于角色面板</textarea>
      </div>

      <!-- 适用范围（标签） -->
      <div class="form-control">
        <label class="label">
          <span class="label-text">适用范围</span>
        </label>
        <div class="flex flex-wrap gap-2">
          <span class="badge badge-primary">属性</span>
          <span class="badge badge-outline">通用</span>
          <button class="btn btn-xs btn-ghost">
            <i class="bi bi-plus"></i> 添加标签
          </button>
        </div>
      </div>
    </div>

    <div class="modal-action">
      <button class="btn btn-ghost">取消</button>
      <button class="btn btn-primary">保存</button>
    </div>
  </div>
</div>
```

---

### 4️⃣ 数据分析（Analytics）

#### 布局结构

```
┌────────────────────────────────────────────────────────────┐
│ 📊 数据分析                     [日▼] [周] [月▼] [自定义] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────┬──────────┬──────────┬──────────┐           │
│  │📋 总翻译量│💰 总成本 │⚡ 平均速度│✅ 成功率 │           │
│  │  2400    │ $12.50   │ 120/分钟 │  95.2%   │           │
│  │ ↑ 15.2%  │ ↓ 8.3%   │ ↑ 5.1%   │ ↑ 2.1%   │           │
│  └──────────┴──────────┴──────────┴──────────┘           │
│                                                            │
│  ┌─ 翻译量趋势 ───────────────────────────────┐           │
│  │                                            │           │
│  │     📈 折线图                              │           │
│  │   1500┤                          ●──●     │           │
│  │   1000┤             ●──●──●──●──●         │           │
│  │    500┤    ●──●──●─●                      │           │
│  │      0└────────────────────────────────   │           │
│  │       10/10 10/12 10/14 10/16 10/18      │           │
│  │                                            │           │
│  └────────────────────────────────────────────┘           │
│                                                            │
│  ┌─ 语言分布 ─────┐  ┌─ 成本分析 ────────────┐           │
│  │                │  │                       │           │
│  │   🥧 饼图      │  │  模型      成本  占比 │           │
│  │                │  │  qwen-plus $5.2  42% │           │
│  │  EN 45%        │  │  gpt-4     $7.3  58% │           │
│  │  JP 30%        │  │                       │           │
│  │  TH 25%        │  │  [查看详情]           │           │
│  │                │  │                       │           │
│  └────────────────┘  └───────────────────────┘           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

#### 图表组件（基于Chart.js）

```javascript
// 折线图配置
const lineChartConfig = {
  type: 'line',
  data: {
    labels: ['10/10', '10/12', '10/14', '10/16', '10/18'],
    datasets: [{
      label: '翻译量',
      data: [500, 800, 1100, 1350, 1420],
      borderColor: '#4F46E5',
      backgroundColor: 'rgba(79, 70, 229, 0.1)',
      tension: 0.4
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index',
        intersect: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { stepSize: 500 }
      }
    }
  }
};

// 饼图配置
const pieChartConfig = {
  type: 'doughnut',
  data: {
    labels: ['EN', 'JP', 'TH'],
    datasets: [{
      data: [45, 30, 25],
      backgroundColor: ['#4F46E5', '#10B981', '#F59E0B']
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { position: 'bottom' }
    }
  }
};
```

---

## 🧩 组件库

### 1. 统计卡片（StatCard）

**用途**: 显示关键指标

**变体**:
- 基础卡片（数字+描述）
- 带图标卡片
- 带趋势卡片
- 带进度条卡片

**代码示例**:
```html
<!-- 基础统计卡片 -->
<div class="stat bg-base-100 rounded-lg shadow-md p-4">
  <div class="stat-figure text-primary">
    <i class="bi bi-clipboard-check text-3xl"></i>
  </div>
  <div class="stat-title text-sm">今日待办</div>
  <div class="stat-value text-3xl text-primary">3</div>
  <div class="stat-desc">
    <span class="text-success">
      <i class="bi bi-arrow-up"></i> 2
    </span>
    较昨日
  </div>
</div>

<!-- 带进度条卡片 -->
<div class="stat bg-base-100 rounded-lg shadow-md p-4">
  <div class="stat-title text-sm">执行中任务</div>
  <div class="stat-value text-3xl text-warning">1</div>
  <div class="stat-desc">
    <progress class="progress progress-warning w-full" value="60" max="100"></progress>
    <span class="text-sm">60% 完成</span>
  </div>
</div>
```

### 2. 筛选栏（FilterBar）

**用途**: 多维度数据筛选

**组成**:
- 搜索框
- 下拉选择器
- 日期范围选择器
- 操作按钮

**代码示例**:
```html
<div class="card bg-base-100 shadow-md">
  <div class="card-body p-4">
    <div class="flex flex-wrap gap-2 items-center">
      <!-- 搜索 -->
      <div class="form-control flex-1">
        <div class="input-group">
          <span><i class="bi bi-search"></i></span>
          <input type="text" placeholder="搜索..." class="input input-bordered input-sm"/>
        </div>
      </div>

      <!-- 筛选器 -->
      <select class="select select-bordered select-sm">
        <option>全部时间</option>
      </select>

      <!-- 按钮 -->
      <button class="btn btn-primary btn-sm">搜索</button>
      <button class="btn btn-ghost btn-sm">重置</button>
    </div>
  </div>
</div>
```

### 3. 数据表格（DataTable）

**功能**:
- 全选/单选
- 排序
- 分页
- 行操作

**代码示例**:
```html
<div class="overflow-x-auto">
  <table class="table table-zebra w-full">
    <thead>
      <tr>
        <th>
          <input type="checkbox" class="checkbox checkbox-sm" id="selectAll"/>
        </th>
        <th>
          <div class="flex items-center gap-1">
            文件名
            <button class="btn btn-ghost btn-xs">
              <i class="bi bi-arrow-down-up"></i>
            </button>
          </div>
        </th>
        <th>状态</th>
        <th>进度</th>
        <th>操作</th>
      </tr>
    </thead>
    <tbody>
      <tr class="hover">
        <td><input type="checkbox" class="checkbox checkbox-sm"/></td>
        <td>
          <div class="flex items-center gap-2">
            <i class="bi bi-file-earmark-excel text-success"></i>
            <span>game.xlsx</span>
          </div>
        </td>
        <td>
          <span class="badge badge-warning gap-1">
            <i class="bi bi-lightning-fill"></i>
            执行中
          </span>
        </td>
        <td>
          <div class="flex items-center gap-2">
            <progress class="progress progress-warning w-24" value="60" max="100"></progress>
            <span class="text-sm">60%</span>
          </div>
        </td>
        <td>
          <div class="dropdown dropdown-end">
            <button class="btn btn-ghost btn-sm">
              <i class="bi bi-three-dots-vertical"></i>
            </button>
            <ul class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
              <li><a><i class="bi bi-eye"></i> 查看详情</a></li>
              <li><a><i class="bi bi-download"></i> 下载</a></li>
              <li><a class="text-error"><i class="bi bi-trash"></i> 删除</a></li>
            </ul>
          </div>
        </td>
      </tr>
    </tbody>
  </table>
</div>

<!-- 分页 -->
<div class="flex justify-center mt-4">
  <div class="btn-group">
    <button class="btn btn-sm">«</button>
    <button class="btn btn-sm btn-active">1</button>
    <button class="btn btn-sm">2</button>
    <button class="btn btn-sm">3</button>
    <button class="btn btn-sm">»</button>
  </div>
</div>
```

### 4. 步骤条（Stepper）

**用途**: 显示流程进度

**状态**:
- 已完成: 绿色勾选
- 进行中: 蓝色高亮
- 待处理: 灰色

**代码示例**:
```html
<ul class="steps w-full">
  <li class="step step-primary">
    <div class="flex flex-col items-center">
      <i class="bi bi-check-circle-fill text-xl"></i>
      <span class="text-sm mt-1">上传</span>
    </div>
  </li>
  <li class="step step-primary">
    <div class="flex flex-col items-center">
      <i class="bi bi-check-circle-fill text-xl"></i>
      <span class="text-sm mt-1">配置</span>
    </div>
  </li>
  <li class="step step-primary">
    <div class="flex flex-col items-center">
      <i class="bi bi-lightning-fill text-xl"></i>
      <span class="text-sm mt-1">执行</span>
    </div>
  </li>
  <li class="step">
    <div class="flex flex-col items-center">
      <i class="bi bi-circle text-xl"></i>
      <span class="text-sm mt-1">完成</span>
    </div>
  </li>
</ul>
```

### 5. 空状态（EmptyState）

**用途**: 无数据时的占位

**变体**:
- 首次使用
- 筛选无结果
- 搜索无结果
- 错误状态

**代码示例**:
```html
<!-- 首次使用 -->
<div class="flex flex-col items-center justify-center py-16">
  <i class="bi bi-inbox text-6xl text-base-content/30"></i>
  <h3 class="text-xl font-semibold mt-4">暂无翻译记录</h3>
  <p class="text-base-content/60 mt-2">上传Excel文件开始翻译吧</p>
  <button class="btn btn-primary mt-6">
    <i class="bi bi-plus-circle"></i>
    新建翻译
  </button>
</div>

<!-- 搜索无结果 -->
<div class="flex flex-col items-center justify-center py-16">
  <i class="bi bi-search text-6xl text-base-content/30"></i>
  <h3 class="text-xl font-semibold mt-4">未找到匹配结果</h3>
  <p class="text-base-content/60 mt-2">尝试使用其他关键词搜索</p>
  <button class="btn btn-ghost mt-6">
    <i class="bi bi-arrow-clockwise"></i>
    清除筛选
  </button>
</div>
```

### 6. 加载骨架屏（Skeleton）

**用途**: 数据加载中占位

**类型**:
- 文本骨架
- 卡片骨架
- 表格骨架

**代码示例**:
```html
<!-- 卡片骨架 -->
<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <div class="skeleton h-4 w-1/2 mb-2"></div>
    <div class="skeleton h-4 w-full mb-2"></div>
    <div class="skeleton h-4 w-3/4"></div>
    <div class="skeleton h-32 w-full mt-4"></div>
  </div>
</div>

<!-- 表格骨架 -->
<div class="space-y-2">
  <div class="skeleton h-12 w-full"></div>
  <div class="skeleton h-12 w-full"></div>
  <div class="skeleton h-12 w-full"></div>
</div>
```

---

## 🎬 交互动效

### 1. 微动效

**按钮悬浮**:
```css
.btn-hover {
  transition: all 0.2s ease-in-out;
}
.btn-hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
}
```

**卡片悬浮**:
```css
.card-hover {
  transition: all 0.3s ease-in-out;
}
.card-hover:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}
```

### 2. 页面过渡

**路由切换动画**:
```css
/* 淡入淡出 */
.page-enter {
  opacity: 0;
  transform: translateY(20px);
}
.page-enter-active {
  opacity: 1;
  transform: translateY(0);
  transition: all 0.3s ease-out;
}
.page-exit {
  opacity: 1;
}
.page-exit-active {
  opacity: 0;
  transition: all 0.2s ease-in;
}
```

### 3. 加载动画

**进度条脉冲**:
```css
.progress-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

### 4. 数字滚动

**统计数字增长动画**:
```javascript
function animateValue(element, start, end, duration) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    element.textContent = Math.floor(progress * (end - start) + start);
    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  };
  window.requestAnimationFrame(step);
}

// 使用
animateValue(document.getElementById('taskCount'), 0, 2400, 1000);
```

---

## 📱 响应式设计

### 1. 断点系统

```css
/* Tailwind CSS 断点 */
/* sm: 640px */
/* md: 768px */
/* lg: 1024px */
/* xl: 1280px */
/* 2xl: 1536px */
```

### 2. 布局适配

**桌面端（≥1024px）**:
```html
<div class="grid grid-cols-4 gap-4">
  <div class="stat">...</div>
  <div class="stat">...</div>
  <div class="stat">...</div>
  <div class="stat">...</div>
</div>
```

**平板端（768px - 1023px）**:
```html
<div class="grid grid-cols-2 gap-4">
  <div class="stat">...</div>
  <div class="stat">...</div>
  <div class="stat">...</div>
  <div class="stat">...</div>
</div>
```

**移动端（<768px）**:
```html
<div class="grid grid-cols-1 gap-4">
  <div class="stat">...</div>
  <div class="stat">...</div>
  <div class="stat">...</div>
  <div class="stat">...</div>
</div>
```

**响应式工具类**:
```html
<!-- 桌面端显示，移动端隐藏 -->
<div class="hidden lg:block">...</div>

<!-- 移动端显示，桌面端隐藏 -->
<div class="block lg:hidden">...</div>

<!-- 响应式间距 -->
<div class="p-4 lg:p-8">...</div>

<!-- 响应式字体 -->
<h1 class="text-2xl lg:text-4xl">...</h1>
```

### 3. 表格响应式

**移动端表格转卡片**:
```html
<!-- 桌面端：表格 -->
<table class="table hidden lg:table">
  <thead>...</thead>
  <tbody>...</tbody>
</table>

<!-- 移动端：卡片列表 -->
<div class="space-y-4 lg:hidden">
  <div class="card bg-base-100 shadow-md">
    <div class="card-body p-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="font-semibold">game.xlsx</h3>
          <p class="text-sm text-base-content/60">5分钟前</p>
        </div>
        <span class="badge badge-warning">执行中</span>
      </div>
      <progress class="progress progress-warning mt-2" value="60" max="100"></progress>
      <div class="card-actions justify-end mt-2">
        <button class="btn btn-sm btn-ghost">查看</button>
        <button class="btn btn-sm btn-primary">下载</button>
      </div>
    </div>
  </div>
</div>
```

---

## ✅ 设计检查清单

### 设计完成度

- [x] 色彩系统定义
- [x] 字体规范定义
- [x] 间距规范定义
- [x] 组件库设计
- [x] 页面原型设计
- [x] 交互动效规范
- [x] 响应式方案
- [ ] 高保真原型（Figma/Sketch）
- [ ] 设计走查（Design Review）

### 可访问性

- [ ] 色彩对比度检查（WCAG AA标准）
- [ ] 键盘导航支持
- [ ] 屏幕阅读器支持（ARIA标签）
- [ ] 焦点状态可见
- [ ] 错误提示清晰

### 性能优化

- [ ] 图片优化（WebP格式）
- [ ] 懒加载实现
- [ ] 骨架屏占位
- [ ] 动画性能优化（GPU加速）

---

## 📦 交付物

1. **设计规范文档** ✅ (本文档)
2. **组件库代码** (待开发)
3. **页面原型代码** (待开发)
4. **Figma/Sketch设计稿** (可选)
5. **设计资源包**:
   - 图标库 (.svg)
   - 示例图片 (.webp)
   - 字体文件 (.woff2)

---

**文档状态**: ✅ 已完成
**下一步**: 开始前端组件开发

**设计师签名**: UX Team
**日期**: 2025-10-17
