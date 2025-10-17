# Pipeline可视化与交互设计
## StringLock - 无限级联Pipeline的UX方案

> **文档版本**: v2.0
> **最后更新**: 2025-10-17
> **设计师**: UX Team
> **状态**: 设计方案（基于经典案例分析优化）

---

## 📋 目录

1. [背景和挑战](#背景和挑战)
2. [经典案例分析](#经典案例分析)
3. [核心设计原则 - 三易原则](#核心设计原则---三易原则)
4. [核心概念](#核心概念)
5. [Phase 1: 基础继承功能 (Zapier风格)](#phase-1-基础继承功能-zapier风格)
6. [Phase 1.5: 智能检测与建议](#phase-15-智能检测与建议)
7. [Phase 2: Pipeline可视化 (n8n风格)](#phase-2-pipeline可视化-n8n风格)
8. [Phase 3: 高级功能](#phase-3-高级功能)
9. [技术实现建议](#技术实现建议)

---

## 🎯 背景和挑战

### 系统特性

本系统采用**无限级联的DataFrame Pipeline**架构：

```
数据状态0 → [处理1] → 数据状态1 → [处理2] → 数据状态2 → ...
                          ↓
                       [分支处理]
                          ↓
                      数据状态3
```

**核心特性**:
- ✅ 任何输出状态都可以作为新的输入
- ✅ 支持分支处理（一个状态派生多个处理）
- ✅ 支持循环处理（迭代优化）
- ✅ 可复用流程（保存为模板）

### 用户价值

**真实场景**（游戏本地化编辑）:
```
阶段1: 原始Excel → 翻译（EN/JP） → 翻译版
阶段2: 翻译版 → CAPS转换 → CAPS版
阶段3: CAPS版 → 质量检查 → 标记问题
阶段4: 问题标记版 → 重新翻译 → 最终版
```

**用户痛点**（现状）:
- ❌ 每次都要下载、手动处理、再上传
- ❌ 无法看到完整的处理链路
- ❌ 无法从中间状态重新开始
- ❌ 无法保存和复用流程

**设计目标**:
- ✅ 可视化完整的数据流转
- ✅ 一键从任意状态继续处理
- ✅ 保存和复用常用流程
- ✅ 追溯数据来源和变化

### 设计挑战

1. **复杂性管理** - 如何让用户理解多阶段流程？
2. **操作便捷性** - 如何简化继承和分支操作？
3. **可视化方案** - 如何清晰展示Pipeline拓扑？
4. **性能问题** - 如何处理大规模Pipeline图？

---

## 🔍 开源前端UX案例参考

**设计目标**: 参考开源产品的成熟交互模式，设计适合游戏本地化团队的界面

### 参考案例

#### 案例1: VS Code扩展管理界面

**参考价值**: **列表视图 + 智能推荐** 🌟推荐

```
特点：
- 垂直列表展示已安装扩展
- 智能推荐相关扩展
- 一键安装推荐包
- 卡片式信息展示

适用场景：80%的标准流程
```

**为什么选择**:
- ✅ 零学习成本，用户都用过VS Code
- ✅ 列表 + 卡片组合，适合非技术人员
- ✅ 智能推荐降低选择成本

#### 案例2: n8n工作流编辑器

**参考价值**: **可视化流程图** (开源MIT协议)

```
特点：
- 节点式流程编排
- 可视化连线
- 支持分支和循环

适用场景：20%的复杂流程
```

**为什么选择**:
- ✅ 开源可参考
- ✅ 适合展示复杂依赖关系
- ⚠️ 需简化，只用于查看而非编辑

#### 案例3: Trello看板

**参考价值**: **状态流转可视化**

```
特点：
- 横向看板布局
- 卡片拖拽
- 状态清晰（待办→进行中→完成）

适用场景：会话列表的状态展示
```

#### 案例4: Notion数据库

**参考价值**: **多视图切换**

```
特点：
- 列表/看板/日历视图切换
- 卡片式详情展开
- 灵活的筛选和排序

适用场景：会话管理的多维度查看
```

### 设计决策

**我们的选择**: **混合式设计**
- **Phase 1 (80%场景)**: 参考**VS Code扩展管理**的列表式 - 易操作、易理解
- **Phase 2 (20%场景)**: 参考**n8n简化版**的可视化画布 - 支持复杂查看

**关键原因**:
1. ✅ 游戏本地化团队非技术背景，列表模式学习成本最低（<30分钟）
2. ✅ 80%的任务是标准流程（上传→翻译→下载），不需要复杂编排
3. ✅ 20%的高级需求（查看完整链路）可通过简化的流程图满足
4. ✅ 垂直列表符合翻译工作的线性思维模式

---

## 🎯 核心设计原则 - 三易原则

### 1️⃣ 易操作 (Easy to Operate)

**设计目标**: 最小化点击次数，突出主操作

**具体实施**:
```
默认流程 = 3步完成
  上传文件 → 点击[开始翻译] → 点击[下载]

复杂流程 = 5步完成
  上传文件 → 点击[开始翻译] → 勾选建议操作 → 点击[应用] → 点击[下载]
```

**设计细节**:
- 🔵 **大按钮**: 主要操作（开始、应用、下载）使用`btn-lg`大尺寸
- 🔵 **默认选项**: 系统推荐的后续操作默认勾选
- 🔵 **一键应用**: 多个后续操作一键批量执行，无需逐个点击
- 🔵 **快捷键**: 支持Enter快速确认，Esc取消

### 2️⃣ 易管理 (Easy to Manage)

**设计目标**: 清晰的状态指示，便捷的批量操作

**具体实施**:
- 📊 **状态可视化**: 用颜色区分（🟢绿色=成功，🟡橙色=进行中，🔴红色=失败）
- 📊 **快速筛选**: 顶部筛选栏（今天、本周、我的、团队的）
- 📊 **批量操作**: 批量暂停/继续/删除
- 📊 **权限控制**: 普通用户只看自己，主管可看全部

**管理视角示例**（翻译主管）:
```
会话列表 → 筛选"进行中" → 勾选多个会话 → 批量暂停
```

### 3️⃣ 易理解 (Easy to Understand)

**设计目标**: 使用业务术语，避免技术黑话

**术语统一**:
| ❌ 避免使用 | ✅ 应该使用 | 说明 |
|-------------|-------------|------|
| Pipeline | 翻译流程 | 降低技术门槛 |
| DAG | 处理步骤 | 更直观 |
| Node | 阶段 | 业务语言 |
| Edge | 数据流转 | 易于理解 |
| Execute | 开始处理 | 动作明确 |

**设计细节**:
- 🎨 **图标辅助**: 每个步骤配图标（📁文件、🤖翻译、📥下载）
- 🎨 **进度可视化**: 用进度条而非百分比数字
- 🎨 **智能提示**: 关键操作提供"这是什么？"悬浮提示
- 🎨 **示例引导**: 首次使用时显示交互式教程

---

## 🧩 核心概念

### Session vs Pipeline

| 概念 | 定义 | 生命周期 | 用途 |
|------|------|----------|------|
| **Session** | 一次转换（状态N→状态N+1） | 短期（完成后可删除） | 管理单个处理阶段 |
| **Pipeline** | 多个Session的组合 | 长期（可复用） | 描述完整流程 |

**关系**:
```
Pipeline "游戏文本翻译流程"
  ├─ Session-1: 原始 → 翻译 → 翻译版
  ├─ Session-2: 翻译版 → CAPS → CAPS版
  └─ Session-3: CAPS版 → 质检 → 最终版
```

### Pipeline数据结构（概念说明）

**Pipeline包含的信息**:
- **基本信息**: Pipeline名称、创建时间
- **节点（Nodes）**:
  - 数据状态节点：显示Excel文件的某个版本（如"状态0-原始"）
  - 处理阶段节点：显示正在执行的操作（如"翻译EN/JP"）
- **连线（Edges）**: 显示数据流向（顺序、分支、循环）
- **元数据**: 总阶段数、已完成阶段数、当前阶段

⚠️ **数据结构具体实现由前端工程师设计**

### 节点状态颜色规范

| 状态 | 颜色 | 图标 | 说明 |
|------|------|------|------|
| Completed | 🟢 绿色 | ✅ | 已完成 |
| Running | 🟡 黄色 | ⚡ | 执行中（显示进度） |
| Pending | ⚪ 灰色 | ⏸️ | 待处理 |
| Failed | 🔴 红色 | ❌ | 失败 |

---

## 🚀 Phase 1: 基础继承功能 (Zapier风格)

**目标**: 最小化实现，解决80%用户痛点，采用**垂直步骤列表**交互模式

**优先级**: P0（必须有）

**设计风格**: 参考Zapier的低代码列表式交互
- ✅ 垂直步骤列表，清晰展示处理流程
- ✅ 每个步骤可点击展开详情
- ✅ 所见即所得的配置界面
- ✅ 支持任意步骤下载中间结果

### 1.1 Session详情页 - 显示继承关系

**现有设计**（需要增强）:
```html
<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <h2 class="card-title">game.xlsx</h2>
    <div class="divider"></div>

    <!-- ⭐ 新增：流程位置 -->
    <div class="mb-4">
      <h3 class="font-semibold mb-2">📍 流程位置</h3>
      <div class="bg-base-200 p-3 rounded-lg">
        <div class="flex items-center gap-2 text-sm">
          <span class="badge badge-sm">状态0</span>
          <i class="bi bi-arrow-right"></i>
          <span class="badge badge-sm">翻译</span>
          <i class="bi bi-arrow-right"></i>
          <span class="badge badge-sm badge-primary">当前: CAPS</span>
        </div>
      </div>
    </div>

    <!-- ⭐ 新增：相关Session -->
    <div class="mb-4">
      <h3 class="font-semibold mb-2">🔗 相关Session</h3>
      <div class="space-y-2">
        <!-- 父Session -->
        <div class="flex items-center justify-between bg-base-200 p-2 rounded">
          <div class="flex items-center gap-2">
            <i class="bi bi-arrow-up-circle text-info"></i>
            <span class="text-sm">父Session: session-001 (翻译)</span>
          </div>
          <button class="btn btn-xs btn-ghost">查看</button>
        </div>

        <!-- 子Session -->
        <div class="flex items-center justify-between bg-base-200 p-2 rounded">
          <div class="flex items-center gap-2">
            <i class="bi bi-arrow-down-circle text-success"></i>
            <span class="text-sm">子Session: session-003 (质检)</span>
          </div>
          <button class="btn btn-xs btn-ghost">查看</button>
        </div>
      </div>
    </div>

    <!-- ⭐ 新增：快速操作 -->
    <div class="card-actions justify-end">
      <button class="btn btn-primary">
        <i class="bi bi-download"></i>
        下载结果
      </button>
      <button class="btn btn-secondary" onclick="showContinueDialog()">
        <i class="bi bi-plus-circle"></i>
        继续处理
      </button>
    </div>
  </div>
</div>
```

### 1.2 "继续处理"对话框

**交互流程**:
```
点击"继续处理" → 显示Modal → 选择处理类型 → 配置参数 → 开始新Session
```

**UI设计**:
```html
<div class="modal modal-open">
  <div class="modal-box w-11/12 max-w-2xl">
    <h3 class="font-bold text-lg mb-4">
      <i class="bi bi-plus-circle"></i>
      创建新的处理阶段
    </h3>

    <!-- 步骤1: 选择输入源 -->
    <div class="form-control mb-4">
      <label class="label">
        <span class="label-text font-semibold">从哪个状态开始</span>
      </label>
      <div class="space-y-2">
        <label class="label cursor-pointer justify-start gap-3">
          <input type="radio" name="inputSource" class="radio radio-primary" checked/>
          <div>
            <div class="font-medium">session-abc123 的输出（CAPS版）</div>
            <div class="text-xs text-base-content/60">使用上一阶段的处理结果</div>
          </div>
        </label>

        <label class="label cursor-pointer justify-start gap-3">
          <input type="radio" name="inputSource" class="radio"/>
          <div>
            <div class="font-medium">上传新文件</div>
            <div class="text-xs text-base-content/60">从其他文件开始新流程</div>
          </div>
        </label>
      </div>
    </div>

    <!-- 步骤2: 选择处理类型 -->
    <div class="form-control mb-4">
      <label class="label">
        <span class="label-text font-semibold">处理类型</span>
      </label>

      <!-- 快捷选项 -->
      <div class="grid grid-cols-2 gap-2 mb-3">
        <button class="btn btn-outline btn-sm justify-start">
          <i class="bi bi-check-circle"></i>
          质量检查
        </button>
        <button class="btn btn-outline btn-sm justify-start">
          <i class="bi bi-file-earmark-code"></i>
          格式转换
        </button>
        <button class="btn btn-outline btn-sm justify-start">
          <i class="bi bi-translate"></i>
          重新翻译
        </button>
        <button class="btn btn-outline btn-sm justify-start btn-active">
          <i class="bi bi-gear"></i>
          自定义处理
        </button>
      </div>
    </div>

    <!-- 步骤3: 配置参数（自定义处理时显示） -->
    <div class="form-control mb-4">
      <label class="label">
        <span class="label-text font-semibold">配置参数</span>
      </label>

      <div class="space-y-3">
        <!-- 规则集选择 -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">拆分规则集</span>
            <span class="label-text-alt text-info">
              <i class="bi bi-info-circle"></i>
              决定如何识别需要处理的单元格
            </span>
          </label>
          <select class="select select-bordered select-sm">
            <option>translation - 翻译规则</option>
            <option selected>caps_only - CAPS规则</option>
            <option>quality_check - 质检规则</option>
          </select>
        </div>

        <!-- 处理器选择 -->
        <div class="form-control">
          <label class="label">
            <span class="label-text">处理器</span>
            <span class="label-text-alt text-info">
              <i class="bi bi-info-circle"></i>
              决定如何处理任务
            </span>
          </label>
          <select class="select select-bordered select-sm">
            <option>llm_qwen - LLM翻译</option>
            <option selected>uppercase - 大写转换</option>
            <option>format_check - 格式检查</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 底部操作 -->
    <div class="modal-action">
      <button class="btn btn-ghost">取消</button>
      <button class="btn btn-primary">
        <i class="bi bi-play-fill"></i>
        开始处理
      </button>
    </div>
  </div>
</div>
```

### 1.3 会话列表 - 显示继承链路

**增强现有表格**:
```html
<table class="table table-zebra">
  <thead>
    <tr>
      <th>文件名</th>
      <th>状态</th>
      <th>流程位置</th> <!-- ⭐ 新增列 -->
      <th>操作</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <div class="flex items-center gap-2">
          <i class="bi bi-file-earmark-excel text-success"></i>
          <span>game.xlsx</span>
        </div>
      </td>
      <td>
        <span class="badge badge-success">已完成</span>
      </td>
      <td>
        <!-- ⭐ 流程位置指示器 -->
        <div class="flex items-center gap-1">
          <div class="tooltip" data-tip="原始文件">
            <div class="w-2 h-2 bg-success rounded-full"></div>
          </div>
          <i class="bi bi-arrow-right text-xs"></i>
          <div class="tooltip" data-tip="翻译">
            <div class="w-2 h-2 bg-success rounded-full"></div>
          </div>
          <i class="bi bi-arrow-right text-xs"></i>
          <div class="tooltip" data-tip="CAPS（当前）">
            <div class="w-3 h-3 bg-primary rounded-full ring-2 ring-primary ring-offset-1"></div>
          </div>
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
            <li><a><i class="bi bi-plus-circle"></i> 继续处理</a></li>
            <li class="divider"></li>
            <li><a><i class="bi bi-diagram-3"></i> 查看完整Pipeline</a></li>
          </ul>
        </div>
      </td>
    </tr>
  </tbody>
</table>
```

### 1.4 简单链路追溯

**"查看完整Pipeline"弹窗**:
```html
<div class="modal modal-open">
  <div class="modal-box w-11/12 max-w-4xl">
    <h3 class="font-bold text-lg mb-4">
      <i class="bi bi-diagram-3"></i>
      Pipeline: game.xlsx 处理链路
    </h3>

    <!-- 简单列表视图（Phase 1） -->
    <div class="space-y-3">
      <!-- Stage 1 -->
      <div class="card bg-base-200">
        <div class="card-body p-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="avatar placeholder">
                <div class="bg-success text-success-content rounded-full w-10">
                  <span class="text-xs">1</span>
                </div>
              </div>
              <div>
                <h4 class="font-semibold">翻译阶段</h4>
                <p class="text-sm text-base-content/60">
                  session-001 | 2025-10-15 14:30
                </p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="badge badge-success">已完成</span>
              <button class="btn btn-sm btn-ghost">
                <i class="bi bi-eye"></i>
              </button>
            </div>
          </div>
          <div class="text-sm mt-2">
            <span class="text-base-content/60">处理器:</span> llm_qwen<br/>
            <span class="text-base-content/60">任务数:</span> 800 / 800<br/>
            <span class="text-base-content/60">耗时:</span> 25分钟
          </div>
        </div>
      </div>

      <div class="flex justify-center">
        <i class="bi bi-arrow-down text-2xl text-base-content/30"></i>
      </div>

      <!-- Stage 2 -->
      <div class="card bg-base-200">
        <div class="card-body p-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="avatar placeholder">
                <div class="bg-primary text-primary-content rounded-full w-10">
                  <span class="text-xs">2</span>
                </div>
              </div>
              <div>
                <h4 class="font-semibold">CAPS转换</h4>
                <p class="text-sm text-base-content/60">
                  session-002 | 2025-10-15 15:00
                </p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="badge badge-warning">执行中</span>
              <button class="btn btn-sm btn-ghost">
                <i class="bi bi-eye"></i>
              </button>
            </div>
          </div>
          <div class="text-sm mt-2">
            <span class="text-base-content/60">处理器:</span> uppercase<br/>
            <span class="text-base-content/60">任务数:</span> 120 / 200<br/>
            <span class="text-base-content/60">进度:</span>
            <progress class="progress progress-warning w-32 ml-2" value="60" max="100"></progress>
            60%
          </div>
        </div>
      </div>

      <div class="flex justify-center">
        <i class="bi bi-arrow-down text-2xl text-base-content/30"></i>
      </div>

      <!-- Stage 3 (Pending) -->
      <div class="card bg-base-200 opacity-50">
        <div class="card-body p-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="avatar placeholder">
                <div class="bg-base-300 text-base-content rounded-full w-10">
                  <span class="text-xs">3</span>
                </div>
              </div>
              <div>
                <h4 class="font-semibold">质量检查</h4>
                <p class="text-sm text-base-content/60">等待上一阶段完成</p>
              </div>
            </div>
            <span class="badge badge-ghost">待处理</span>
          </div>
        </div>
      </div>
    </div>

    <div class="modal-action">
      <button class="btn btn-ghost">关闭</button>
      <button class="btn btn-primary">
        <i class="bi bi-diagram-3"></i>
        查看图形化Pipeline（Phase 2）
      </button>
    </div>
  </div>
</div>
```

---

## 💡 Phase 1.5: 智能检测与建议

**目标**: 自动识别后续处理需求，减少用户配置负担

**优先级**: P0（必须有）- 这是Zapier模式的核心优势

**设计理念**: **智能推荐 > 手动配置**
- 系统主动检测可能的后续操作
- 以卡片形式展示建议（而非复杂的规则配置）
- 用户只需勾选 + 一键应用
- 降低"Filter"等抽象概念的理解成本

### 1.5.1 智能检测卡片（核心创新）

**Zapier风格的垂直步骤流（带智能建议）**:

```html
┌──────────────────────────────────────────────────────┐
│  📄 会话详情 - session_20250117_001                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ 1️⃣ 数据输入                          ✅ 已完成│   │
│  │    📁 game_text_v2.5.xlsx                    │   │
│  │    ⏱️ 2025-01-17 14:30                       │   │
│  │    [📥 下载原始文件]                         │   │
│  └─────────────────────────────────────────────┘   │
│           │                                          │
│           ▼                                          │
│  ┌─────────────────────────────────────────────┐   │
│  │ 2️⃣ 翻译处理                          ✅ 已完成│   │
│  │    🤖 Qwen-plus                              │   │
│  │    🌏 CH → EN, JP, TH                        │   │
│  │    ✅ 1,234 / 1,234 任务                     │   │
│  │    ⏱️ 用时 15分钟                            │   │
│  │    [📊 查看详情] [📥 下载此版本]             │   │
│  └─────────────────────────────────────────────┘   │
│           │                                          │
│           ▼                                          │
│  ┌─────────────────────────────────────────────┐   │
│  │ 💡 需要继续处理吗？                          │   │
│  │                                              │   │
│  │  系统检测到：                                │   │
│  │  • 包含CAPS工作表 (45个单元格)              │   │
│  │  • 包含术语标记 (12处)                      │   │
│  │                                              │   │
│  │  ⭐ 建议操作：                               │   │
│  │                                              │   │
│  │  ┌─────────────────────────────────────┐   │   │
│  │  │ ☑️ CAPS全大写转换                    │   │   │
│  │  │ 自动识别CAPS工作表并转为大写         │   │   │
│  │  │ 📊 预计处理: 45个单元格 | ⏱️ 约2分钟  │   │   │
│  │  │ [详细配置 ▼]                         │   │   │
│  │  └─────────────────────────────────────┘   │   │
│  │                                              │   │
│  │  ┌─────────────────────────────────────┐   │   │
│  │  │ ☑️ 术语库替换                        │   │   │
│  │  │ 使用术语库替换标记的文本             │   │   │
│  │  │ 📊 预计处理: 12处 | ⏱️ 约1分钟        │   │   │
│  │  │ [详细配置 ▼]                         │   │   │
│  │  └─────────────────────────────────────┘   │   │
│  │                                              │   │
│  │  [⏭️ 跳过，直接导出]  [🚀 应用选中操作]    │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 1.5.2 智能检测逻辑（用户视角）

**系统会自动检测哪些情况？**

**检测场景1: CAPS工作表**
- **触发条件**: 用户看到：翻译完成后，如果Excel中存在名为"CAPS"的工作表，且有已翻译的单元格
- **建议卡片显示**:
  - 标题："CAPS全大写转换"
  - 说明："自动识别CAPS工作表并转为大写"
  - 预估："45个单元格 | 约2分钟"
  - 优先级：**高**（默认勾选）

**检测场景2: 术语标记**
- **触发条件**: Excel中有特殊标记（如`{TERM:xxx}`）的单元格
- **建议卡片显示**:
  - 标题："术语库替换"
  - 说明："使用术语库替换标记的文本"
  - 预估："12处 | 约1分钟"
  - 优先级：**中**（默认勾选）

**检测场景3: 格式错误**
- **触发条件**: 发现占位符缺失、标点符号错误等问题
- **建议卡片显示**:
  - 标题："格式修复"
  - 说明："修复占位符、标点符号等格式问题"
  - 预估："8处 | 约3分钟"
  - 优先级：**低**（不默认勾选）

⚠️ **检测逻辑的技术实现由后端工程师开发**

### 1.5.3 建议卡片交互

**默认状态**（高优先级自动勾选）:
```html
<!-- High Priority - 默认勾选 -->
<div class="card bg-base-100 border-2 border-primary">
  <div class="card-body p-4">
    <label class="label cursor-pointer justify-start gap-3">
      <input type="checkbox" class="checkbox checkbox-primary checkbox-lg" checked/>
      <div class="flex-1">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-2xl">🔠</span>
          <h4 class="font-semibold text-lg">CAPS全大写转换</h4>
          <span class="badge badge-primary badge-sm">推荐</span>
        </div>
        <p class="text-sm text-base-content/70">
          自动识别CAPS工作表并转为大写
        </p>
        <div class="flex items-center gap-3 mt-2 text-xs text-base-content/60">
          <span>📊 预计处理: 45个单元格</span>
          <span>⏱️ 约2分钟</span>
        </div>
      </div>
    </label>

    <!-- 折叠的详细配置 -->
    <div class="collapse collapse-arrow" id="config-caps">
      <input type="checkbox" />
      <div class="collapse-title text-sm font-medium">
        详细配置（可选）
      </div>
      <div class="collapse-content">
        <div class="form-control">
          <label class="label">
            <span class="label-text">处理器</span>
          </label>
          <select class="select select-bordered select-sm">
            <option selected>uppercase - 大写转换</option>
            <option>lowercase - 小写转换</option>
          </select>
        </div>
      </div>
    </div>
  </div>
</div>
```

**底部操作按钮**:
```html
<div class="flex items-center justify-between p-4 bg-base-200 rounded-lg mt-4">
  <div class="text-sm">
    <span class="font-semibold">已选择 2 项操作</span>
    <span class="text-base-content/60">（预计 3 分钟）</span>
  </div>

  <div class="flex gap-2">
    <button class="btn btn-ghost btn-sm">
      ⏭️ 跳过，直接导出
    </button>
    <button class="btn btn-primary btn-lg">
      🚀 应用选中操作
    </button>
  </div>
</div>
```

### 1.5.4 一键应用流程

**用户操作流程**:
```
翻译完成 → 自动显示建议卡片 → 勾选需要的操作 → 点击[应用] → 自动创建并启动Session → 完成
```

**关键优势**:
1. ✅ **零学习成本** - 不需要理解"规则集"、"处理器"等概念
2. ✅ **所见即所得** - 卡片直接显示会做什么
3. ✅ **智能默认** - 系统根据优先级自动勾选
4. ✅ **可扩展** - 可随时添加新的检测规则

### 1.5.5 批量处理流程（用户体验）

**用户操作流程**:
```
1. 翻译完成
   ↓
2. 系统自动显示建议卡片（2-3张）
   ↓
3. 用户勾选需要的操作（默认已勾选高优先级项）
   ↓
4. 点击 [🚀 应用选中操作] 按钮
   ↓
5. 系统同时创建并启动多个处理任务
   ↓
6. 实时显示每个任务的进度
   ↓
7. 全部完成后显示下载按钮
```

**用户看到的反馈**:
- 点击"应用"后立即显示进度卡片
- 每个任务独立显示进度条（如："CAPS转换 60%"）
- 完成的任务显示绿色勾选标记
- 全部完成后按钮变为"下载结果"

⚠️ **后端批量创建逻辑由后端工程师实现**

### 1.5.6 与三易原则的对应

**易操作**:
- 勾选卡片 → 点击[应用] = 2次操作即可
- 无需手动选择规则集、处理器

**易管理**:
- 建议卡片清晰显示"会做什么"、"需要多久"
- 支持批量应用，无需逐个创建

**易理解**:
- "CAPS全大写转换" > "caps_only + uppercase processor"
- "术语库替换" > "term_markers + term_replacer"
- 用业务语言描述，避免技术术语

---

## 🎨 Phase 2: Pipeline可视化 (参考n8n)

**目标**: 图形化展示复杂流程，主要用于**查看和理解**（非编辑）

**优先级**: P1（应该有）

**设计理念**:
- ✅ 只读模式为主 - 用户主要需要"看懂"流程，不是"编辑"流程
- ✅ 自动布局 - 系统自动排列节点，无需手动拖拽
- ✅ 简化展示 - 只显示核心信息，隐藏技术细节
- ⚠️ 技术实现由前端工程师单独选型

### 2.1 流程图界面原型

**界面布局**:
```
┌─────────────────────────────────────────────────────────────┐
│ Pipeline: game.xlsx 翻译流程                    [保存模板] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   │
│  │ 状态0   │──>│ 翻译    │──>│ 状态1   │──>│ CAPS    │   │
│  │ 原始    │   │ EN/JP   │   │ 已翻译  │   │ 转换    │   │
│  │         │   │         │   │         │   │         │   │
│  │ 🟢100%  │   │ 🟢100%  │   │ 🟢100%  │   │ 🟡60%   │   │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   │
│                                  │                         │
│                                  │ (分支)                  │
│                                  ↓                         │
│                              ┌─────────┐   ┌─────────┐    │
│                              │ 格式    │──>│ 状态3   │    │
│                              │ 检查    │   │ 修复版  │    │
│                              │ ⚪待处理 │   │ ⚪待处理 │    │
│                              └─────────┘   └─────────┘    │
│                                                             │
│  [缩放: 100%] [自动布局] [居中] [导出PNG]                 │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 节点交互

**鼠标悬浮**:
```
┌─────────────────────────┐
│ 节点: 状态1（已翻译）   │
├─────────────────────────┤
│ Session: session-001    │
│ 状态: ✅ 已完成         │
│ 文件: game_translated   │
│ 大小: 2.8 MB            │
│ 完成时间: 2小时前       │
└─────────────────────────┘
```

**右键菜单**:
```
右键点击节点 →
  ┌──────────────────────┐
  │ 📥 下载此状态        │
  │ 🔍 查看详情          │
  ├──────────────────────┤
  │ ➕ 创建分支：        │
  │   • CAPS转换         │
  │   • 质量检查         │
  │   • 格式转换         │
  │   • 自定义...        │
  ├──────────────────────┤
  │ 🔗 复制Session ID    │
  │ 🗑️ 删除此节点        │
  └──────────────────────┘
```

**双击节点**:
- 数据状态节点 → 跳转到Session详情页
- 处理阶段节点 → 显示任务执行详情

### 2.3 连线类型

| 类型 | 样式 | 说明 | 示例 |
|------|------|------|------|
| 顺序 | 实线箭头 → | 顺序执行 | 翻译 → CAPS |
| 分支 | 虚线箭头 ⇢ | 从一个状态派生多个处理 | 状态1 ⇢ CAPS、质检 |
| 循环 | 弧线箭头 ↻ | 循环处理 | 质检失败 ↻ 重译 |

### 2.4 自动布局

**布局规则**（UX需求）:
- 从左到右展示时间顺序
- 分支向下展开
- 节点间距保持一致
- 避免连线交叉

⚠️ **技术实现**: 前端工程师选择合适的布局算法

### 2.5 缩放和导航

**控制按钮**:
```html
<div class="absolute bottom-4 right-4 flex gap-2">
  <button class="btn btn-sm" onclick="zoomIn()">
    <i class="bi bi-zoom-in"></i>
  </button>
  <button class="btn btn-sm" onclick="zoomOut()">
    <i class="bi bi-zoom-out"></i>
  </button>
  <button class="btn btn-sm" onclick="fitView()">
    <i class="bi bi-arrows-fullscreen"></i>
    适应画布
  </button>
  <button class="btn btn-sm" onclick="exportPNG()">
    <i class="bi bi-download"></i>
    导出PNG
  </button>
</div>
```

**小地图（Minimap）**:
```
┌─────────────────┐
│ 小地图          │
│ ┌───────────┐   │
│ │ ▪️ ▪️      │   │
│ │    ▪️ ▪️   │   │
│ │       ▪️   │   │
│ └───────────┘   │
└─────────────────┘
```

---

## 🚀 Phase 3: 高级功能

**目标**: 流程复用和智能编排

**优先级**: P2（可以有）

### 3.1 流程模板保存

**保存模板对话框**:
```html
<div class="modal modal-open">
  <div class="modal-box">
    <h3 class="font-bold text-lg mb-4">
      <i class="bi bi-save"></i>
      保存为模板
    </h3>

    <div class="form-control mb-3">
      <label class="label">
        <span class="label-text">模板名称</span>
      </label>
      <input type="text" placeholder="例如：游戏文本标准流程" class="input input-bordered"/>
    </div>

    <div class="form-control mb-3">
      <label class="label">
        <span class="label-text">描述</span>
      </label>
      <textarea class="textarea textarea-bordered" placeholder="说明此模板的用途"></textarea>
    </div>

    <div class="form-control mb-3">
      <label class="label">
        <span class="label-text">包含的阶段</span>
      </label>
      <div class="space-y-2">
        <label class="label cursor-pointer justify-start gap-2">
          <input type="checkbox" class="checkbox checkbox-sm" checked/>
          <span class="text-sm">翻译（EN/JP）</span>
        </label>
        <label class="label cursor-pointer justify-start gap-2">
          <input type="checkbox" class="checkbox checkbox-sm" checked/>
          <span class="text-sm">CAPS转换</span>
        </label>
        <label class="label cursor-pointer justify-start gap-2">
          <input type="checkbox" class="checkbox checkbox-sm" checked/>
          <span class="text-sm">格式检查</span>
        </label>
      </div>
    </div>

    <div class="modal-action">
      <button class="btn btn-ghost">取消</button>
      <button class="btn btn-primary">
        <i class="bi bi-save"></i>
        保存模板
      </button>
    </div>
  </div>
</div>
```

**应用模板**:
```html
<div class="card bg-base-100 shadow-md">
  <div class="card-body">
    <h3 class="card-title">
      <i class="bi bi-folder"></i>
      我的模板
    </h3>

    <div class="space-y-2">
      <div class="flex items-center justify-between p-3 bg-base-200 rounded-lg">
        <div>
          <h4 class="font-semibold">游戏文本标准流程</h4>
          <p class="text-sm text-base-content/60">翻译 → CAPS → 质检</p>
          <p class="text-xs text-base-content/50">创建于 2025-10-10</p>
        </div>
        <div class="flex gap-2">
          <button class="btn btn-sm btn-primary">
            <i class="bi bi-play-fill"></i>
            应用
          </button>
          <button class="btn btn-sm btn-ghost">
            <i class="bi bi-pencil"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 3.2 拖拽式编排

**拖拽组件库**:
```
┌─────────────────────────────────────────────┐
│ 🧩 组件库                                   │
├─────────────────────────────────────────────┤
│                                             │
│ 📦 处理器                                   │
│ ├─ 🤖 LLM翻译                               │
│ ├─ 🔠 大写转换                              │
│ ├─ ✅ 质量检查                              │
│ └─ 📝 格式转换                              │
│                                             │
│ 🎯 规则                                     │
│ ├─ 🟡 黄色单元格                            │
│ ├─ 🔵 蓝色单元格                            │
│ └─ ⚪ 空单元格                              │
│                                             │
│ 🔧 控制流                                   │
│ ├─ 🔀 条件分支                              │
│ └─ 🔄 循环                                  │
└─────────────────────────────────────────────┘

拖拽到画布 →

┌─────────────────────────────────────────────┐
│ Pipeline 编排画布                           │
├─────────────────────────────────────────────┤
│                                             │
│  [开始]                                     │
│    ↓                                        │
│  [LLM翻译]                                  │
│    ↓                                        │
│  {条件分支: CAPS Sheet存在?}                │
│    ├─ Yes → [大写转换]                      │
│    └─ No  → [跳过]                          │
│    ↓                                        │
│  [质量检查]                                 │
│    ↓                                        │
│  [结束]                                     │
│                                             │
└─────────────────────────────────────────────┘
```

### 3.3 条件分支

**条件分支节点**:
```html
<div class="node node-branch">
  <div class="node-header bg-warning">
    <i class="bi bi-diagram-2"></i>
    条件分支
  </div>
  <div class="node-body">
    <div class="text-sm mb-2">条件:</div>
    <select class="select select-sm select-bordered w-full">
      <option>存在CAPS Sheet</option>
      <option>任务数 > 100</option>
      <option>自定义脚本...</option>
    </select>
  </div>
  <div class="node-footer">
    <div class="flex justify-between text-xs">
      <span class="text-success">✓ True</span>
      <span class="text-error">✗ False</span>
    </div>
  </div>
</div>
```

### 3.4 循环控制

**循环节点**:
```html
<div class="node node-loop">
  <div class="node-header bg-info">
    <i class="bi bi-arrow-repeat"></i>
    循环
  </div>
  <div class="node-body">
    <div class="text-sm mb-2">循环条件:</div>
    <select class="select select-sm select-bordered w-full mb-2">
      <option>质检未通过</option>
      <option>固定次数</option>
      <option>自定义条件...</option>
    </select>

    <div class="text-sm mb-1">最大次数:</div>
    <input type="number" class="input input-sm input-bordered w-full" value="3"/>
  </div>
  <div class="node-footer text-xs text-base-content/60">
    当前循环: 2 / 3
  </div>
</div>
```

---

## 📊 前端技术选型会议议题

⚠️ **注意**: 以下内容需要由前端工程师专门讨论决定，不属于UX设计范围

### Phase 2 流程图技术选型（待讨论）

**需要讨论的问题**:
1. 选择哪个图形库（开源）？
2. 使用Canvas还是SVG渲染？
3. 如何实现自动布局？
4. 如何优化大规模节点性能？

**技术选型要求**:
- ✅ 必须开源且免费
- ✅ 支持自定义节点样式
- ✅ 支持自动布局算法
- ✅ 性能良好（支持100+节点）

**参考方向**（供前端评估）:
- D3.js（完全自定义，学习曲线陡）
- mermaid.js（简单但功能有限）
- 或其他前端工程师推荐的方案

---

## 💻 技术实现（非UX范围）

⚠️ **重要**: 技术实现细节不属于本UX文档范围，应由前端工程师单独讨论选型。

**本文档专注于**:
- ✅ 用户体验描述
- ✅ 交互行为设计
- ✅ 界面原型展示
- ✅ 开源UX案例参考

**技术实现应包含在单独的文档**（待创建）:
- 📄 `FRONTEND_TECH_SPEC.md` - 前端技术选型和实现方案
  - 图形库选择（D3.js / mermaid.js / 其他）
  - 渲染方式（Canvas / SVG）
  - 自动布局算法
  - 数据加载和状态管理
  - 性能优化方案

---


## 📊 功能对比表

| 功能 | Phase 1 | Phase 1.5 | Phase 2 | Phase 3 |
|------|---------|-----------|---------|---------|
| Session继承 | ✅ 基础支持 | ✅ 完善 | ✅ 完善 | ✅ 完善 |
| 链路追溯 | ✅ 列表视图 | ✅ 列表视图 | ✅ 图形化 | ✅ 交互式图形 |
| 快速继续 | ✅ 对话框 | ✅ 对话框 | ✅ 右键菜单 | ✅ 拖拽创建 |
| **智能建议** | ❌ 无 | ✅ **卡片式建议** | ✅ 完善 | ✅ 完善 |
| **一键应用** | ❌ 无 | ✅ **批量创建Session** | ✅ 完善 | ✅ 完善 |
| 流程模板 | ❌ 无 | ❌ 无 | ⚠️ 基础 | ✅ 完整 |
| 可视化编排 | ❌ 无 | ❌ 无 | ❌ 无 | ✅ 拖拽式 |
| 条件分支 | ❌ 无 | ❌ 无 | ❌ 无 | ✅ 支持 |
| 循环控制 | ❌ 无 | ❌ 无 | ❌ 无 | ✅ 支持 |

---

## ✅ 开发检查清单

### Phase 1（2周）- Zapier风格基础

- [ ] Session数据模型增加parent_session_id字段
- [ ] API支持从parent继承创建Session
- [ ] Session详情页显示继承关系
- [ ] Session详情页垂直步骤列表UI
- [ ] "继续处理"对话框
- [ ] 会话列表显示流程位置指示器
- [ ] 简单链路追溯列表视图

### Phase 1.5（1周）- 智能检测与建议 ⭐核心创新

- [ ] **后端SmartDetectionService开发**
  - [ ] 检测CAPS工作表
  - [ ] 检测术语标记
  - [ ] 检测格式错误
  - [ ] 生成建议卡片数据结构
- [ ] **前端智能建议UI**
  - [ ] 建议卡片组件开发
  - [ ] 勾选/取消勾选交互
  - [ ] 预估时间和任务数显示
  - [ ] 详细配置折叠面板
- [ ] **API端点**
  - [ ] `GET /api/sessions/{id}/suggestions`
  - [ ] `POST /api/sessions/{id}/apply-suggestions`
- [ ] **批量Session创建逻辑**
  - [ ] 一键创建多个子Session
  - [ ] 自动启动所有子Session
  - [ ] 进度监控

### Phase 2（3周）- Pipeline可视化

- [ ] 选择Pipeline可视化库（ReactFlow / GoJS）
- [ ] Pipeline数据模型设计
- [ ] 节点和边的渲染
- [ ] 自动布局算法集成
- [ ] 节点交互（悬浮、右键、双击）
- [ ] 缩放和小地图
- [ ] 实时进度更新

### Phase 3（4周）

- [ ] 流程模板CRUD
- [ ] 模板应用逻辑
- [ ] 拖拽式编排画布
- [ ] 条件分支节点
- [ ] 循环控制节点
- [ ] Pipeline执行引擎
- [ ] 性能优化（大规模Pipeline）

---

## 🎉 设计总结

本文档经过**两轮深度设计迭代**，最终形成了基于经典案例分析的混合式设计方案：

### 核心创新点

**Phase 1.5 智能检测与建议** - 这是本次设计的最大亮点：
- ✅ **借鉴Zapier的零代码理念**，但避免其灵活性不足的问题
- ✅ **智能推荐 > 手动配置**，降低用户认知负担
- ✅ **卡片式交互**，符合游戏编辑的直觉思维
- ✅ **一键批量应用**，支持多个后续操作同时执行

### 三易原则贯穿始终

| 原则 | 实现方式 | 验收标准 |
|------|----------|----------|
| **易操作** | 垂直步骤列表 + 智能建议 | 新人<30分钟上手 |
| **易管理** | 状态颜色 + 批量操作 | 主管快速定位问题 |
| **易理解** | 业务术语 + 图标辅助 | 无需阅读技术文档 |

### 设计决策对比

| 对比维度 | 初版设计 | 优化后设计 |
|----------|----------|-----------|
| 继续处理方式 | 手动配置规则集+处理器 | 智能检测 + 勾选建议 |
| 用户学习成本 | 需要理解YAML配置 | 零代码，所见即所得 |
| 操作步骤 | 7步（选择→配置→创建→启动） | 3步（勾选→应用→完成） |
| 扩展性 | 依赖文档说明 | 卡片自描述，可随时添加新检测 |

### 实施优先级（更新）

| Phase | 功能 | 优先级 | 预计工作量 | 价值 |
|-------|------|--------|-----------|------|
| Phase 1 | Zapier风格基础 | **P0** | 2周 | 解决80%场景 |
| **Phase 1.5** | **智能检测与建议** | **P0** | **1周** | **核心差异化竞争力** |
| Phase 2 | n8n风格可视化 | P1 | 3周 | 满足20%复杂场景 |
| Phase 3 | 模板与编排 | P2 | 4周 | 提升复用效率 |

---

**文档状态**: ✅ 设计完成（基于经典案例分析优化v2.0）
**下一步**:
1. 团队Review设计方案（1天）
2. 开始Phase 1开发（2周）
3. 开始Phase 1.5开发（1周）- **优先级最高**

**设计讨论参与者**:
- Alice (游戏编辑) - 用户需求提供
- Carol (UX设计师) - 交互设计
- 经典案例参考：Zapier, n8n, Jenkins, Airflow, GitHub Actions

**设计师签名**: UX Team
**日期**: 2025-10-17
**版本**: v2.0 (经典案例分析优化版)
