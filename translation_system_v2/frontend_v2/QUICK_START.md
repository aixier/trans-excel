# Quick Start - 快速开始指南

> 🚀 工程师C开发的Glossary和Analytics模块测试指南

---

## 📁 文件结构

```
frontend_v2/
├── glossary.html              # 术语库管理测试页
├── analytics.html             # 数据分析测试页
├── js/
│   └── pages/
│       ├── glossary.js        # 术语库页面逻辑
│       └── analytics.js       # 数据分析页面逻辑
├── ENGINEER_C_PROGRESS.md     # 开发进度报告
└── QUICK_START.md             # 本文档
```

---

## 🚀 如何运行

### 方法1: 使用Python (推荐)

```bash
# 进入frontend_v2目录
cd frontend_v2

# 启动HTTP服务器
python -m http.server 8080

# 打开浏览器访问:
# - Glossary: http://localhost:8080/glossary.html
# - Analytics: http://localhost:8080/analytics.html
```

### 方法2: 使用Node.js

```bash
# 进入frontend_v2目录
cd frontend_v2

# 安装http-server (首次需要)
npm install -g http-server

# 启动服务器
npx http-server -p 8080

# 打开浏览器访问
```

### 方法3: 直接用浏览器打开

⚠️ **注意**: 由于浏览器安全限制，部分功能可能无法正常工作（如本地文件加载）。建议使用方法1或方法2。

```bash
# Windows
start glossary.html
start analytics.html

# Mac
open glossary.html
open analytics.html

# Linux
xdg-open glossary.html
xdg-open analytics.html
```

---

## 📖 功能测试清单

### Glossary页面 (术语库管理)

访问: `http://localhost:8080/glossary.html`

**可测试功能**:
- ✅ 左侧术语库列表展示
- ✅ 点击切换术语库
- ✅ 新建术语库（弹窗输入）
- ✅ 右侧术语条目表格展示
- ✅ 删除术语（二次确认）
- ⚠️ 搜索功能（UI完成，逻辑待实现）
- ⚠️ 语言筛选（UI完成，逻辑待实现）
- ❌ 术语编辑（待开发）
- ❌ Excel导入导出（待开发）

**Mock数据**:
- 3个术语库：游戏通用术语、UI专用术语、角色名称
- 每个术语库包含5-8条术语

**操作步骤**:
1. 打开页面，左侧显示3个术语库
2. 点击"游戏通用术语"，右侧显示5条术语
3. 点击"新建术语库"按钮，输入名称创建
4. 点击术语行的"🗑️"图标删除术语
5. 在搜索框输入关键词（功能待实现）
6. 选择语言筛选器（功能待实现）

---

### Analytics页面 (数据分析)

访问: `http://localhost:8080/analytics.html`

**可测试功能**:
- ✅ 4个统计卡片（总翻译量、总成本、平均速度、成功率）
- ✅ 时间范围切换（日/周/月/年）
- ✅ 翻译量趋势折线图（Chart.js）
- ✅ 语言分布饼图（Chart.js）
- ✅ 成本分析和预算进度条
- ✅ 按模型分组统计
- ✅ 主题切换（Light/Dark）
- ❌ 报表导出（待开发）

**Mock数据**:
- 4个完成的会话
- 模拟翻译量、成本、语言分布等数据

**操作步骤**:
1. 打开页面，顶部显示4个统计卡片
2. 点击"日/周/月/年"按钮切换时间范围
3. 查看折线图（翻译量趋势）
4. 查看饼图（语言分布）
5. 滚动查看成本分析卡片
6. 点击右上角月亮图标切换主题

---

## 🎨 UI效果预览

### Glossary页面

```
┌──────────────────────────────────────────────┐
│ 📖 术语库管理                                │
├──────────────────────────────────────────────┤
│                                              │
│  术语库列表        术语条目                  │
│  ┌──────────┐    ┌──────────────────────┐  │
│  │+ 新建    │    │ 游戏通用术语 (500条) │  │
│  │          │    │ [导入▼] [导出] [+新增]│  │
│  │● 游戏通用│    │                       │  │
│  │  500条   │    │ 🔍 [搜索...] [语言▼] │  │
│  │  ✓激活中 │    │                       │  │
│  │          │    │ [表格展示区域]        │  │
│  │○ UI专用  │    │                       │  │
│  │  120条   │    └──────────────────────┘  │
│  └──────────┘                               │
└──────────────────────────────────────────────┘
```

### Analytics页面

```
┌──────────────────────────────────────────────┐
│ 📊 数据分析          [日][周][月▼][年]      │
├──────────────────────────────────────────────┤
│                                              │
│  [📋 2400] [💰 $12.50] [⚡ 120] [✅ 95.2%]  │
│                                              │
│  ┌─ 趋势图 ────┐  ┌─ 饼图 ─────┐          │
│  │   📈        │  │    🥧       │          │
│  └─────────────┘  └─────────────┘          │
│                                              │
│  ┌─ 成本分析 ────────────────────────────┐ │
│  │ $12.50 / $50.00                       │ │
│  │ ██████████░░░░░░░░░░ 25%              │ │
│  │ • qwen-plus: $5.20 (42%)              │ │
│  │ • gpt-4: $7.30 (58%)                  │ │
│  └───────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

---

## 🔧 技术栈

### 前端框架

- **无框架**: 纯Vanilla JavaScript (ES6+)
- **样式**: DaisyUI + Tailwind CSS
- **图标**: Bootstrap Icons
- **图表**: Chart.js 4.4.0

### 浏览器要求

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### CDN依赖

所有依赖通过CDN加载，无需本地安装：

```html
<!-- Tailwind CSS + DaisyUI -->
<link href="https://cdn.jsdelivr.net/npm/daisyui@4.4.19/dist/full.min.css" rel="stylesheet" />
<script src="https://cdn.tailwindcss.com"></script>

<!-- Bootstrap Icons -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">

<!-- Chart.js (仅Analytics页面) -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
```

---

## 🐛 常见问题

### Q1: 页面打开后没有显示内容

**A**: 检查浏览器控制台是否有错误。常见原因：
- JavaScript文件路径错误
- CDN资源加载失败（网络问题）
- 浏览器不支持ES6语法

**解决方法**:
```bash
# 确保使用HTTP服务器运行，而不是file://协议
python -m http.server 8080
```

### Q2: Chart.js图表不显示

**A**: 检查：
1. Chart.js CDN是否加载成功
2. Canvas元素是否存在
3. 打开浏览器控制台查看错误信息

**调试代码**:
```javascript
// 在浏览器控制台运行
console.log(typeof Chart); // 应该输出 "function"
```

### Q3: Mock数据不符合预期

**A**: Mock数据在JS文件底部定义：
- `glossary.js` - `getMockGlossaries()` 和 `getMockTerms()`
- `analytics.js` - `getMockSessions()`

可以直接修改这些方法来调整测试数据。

### Q4: 如何连接真实后端API

**A**: 修改JS文件中的API调用：

```javascript
// 当前（Mock）
// this.glossaries = await API.getGlossaries();
this.glossaries = this.getMockGlossaries();

// 连接真实API（取消注释）
this.glossaries = await API.getGlossaries();
// this.glossaries = this.getMockGlossaries(); // 注释掉mock
```

---

## 📞 反馈和问题

如遇到问题或有改进建议，请：

1. 查看浏览器控制台错误信息
2. 检查 `ENGINEER_C_PROGRESS.md` 中的已知问题
3. 联系工程师C

---

## 📚 相关文档

- **开发进度**: `ENGINEER_C_PROGRESS.md`
- **需求文档**: `docs/requirements/REQUIREMENTS.md`
- **UI设计**: `docs/design/UI_DESIGN.md`
- **技术规格**: `docs/technical/FEATURE_SPEC.md`

---

**更新时间**: 2025-10-17
**版本**: v1.0
**作者**: Engineer C

🎉 **祝测试愉快！**
