# Claude Code 项目配置

本目录包含Claude Code工作时的项目配置和架构指南。

## 📚 必读文档（按顺序）

### 1. 架构核心理念 ⭐⭐⭐
**文件**: `ARCHITECTURE_PRINCIPLES.md`

**必须首先阅读！** 包含所有开发必须遵循的核心原则：
- 数据状态的连续性
- 任务拆分表的定义
- 统一的转换流程
- 开发规范和禁止事项

### 2. Pipeline重构方案 ⭐⭐ (NEW)
**文件**: `PIPELINE_REFACTOR_PLAN.md`

**最新架构重构计划！** 基于核心理念的完整实施方案：
- Session-per-Transformation模型
- 配置驱动的Rules和Processors
- Parent-Child Session链接机制
- 完整的迁移指南和测试计划

### 3. 项目总览
**文件**: `../CLAUDE.md`

提供项目概览、命令、API文档等信息（已更新为新架构）。

### 💡 核心架构理念：DataFrame Pipeline

**重要理解**：整个系统就是一个 **DataFrame 的 Pipeline**！

```
DataFrame (状态0) → [处理] → DataFrame (状态1) → [处理] → DataFrame (状态2)
    ↓                          ↓                          ↓
 相同的格式               相同的格式               相同的格式
```

**关键点**：
- ✅ 所有数据状态都是**相同格式的 DataFrame**
- ✅ 包含数据列（key, CH, EN）+ 元数据列（color_CH, comment_CH）
- ✅ 每个处理器输入/输出格式完全一致
- ✅ 这样才能实现无限级联

**为什么元数据必须在 DataFrame 里？**
- 如果用单独的字典存储颜色/注释，格式就不一致了
- 状态1 = {df, colors}, 状态2 = processor(状态1) 返回什么？
- DataFrame Pipeline 要求输入输出格式完全一致

### 4. 详细架构设计

**简化架构** (推荐)
**文件**: `../backend_v2/SIMPLIFIED_ARCHITECTURE.md`

基于"数据状态流转"的简化架构设计，包含：
- 核心概念（数据状态、任务表）
- 组件定义（拆分器、转换器）
- 完整流程示例
- 代码实现指南

**管道架构** (高级)
**文件**: `../backend_v2/PIPELINE_ARCHITECTURE.md`

基于管道模式的完整架构设计，适合理解复杂编排场景。

## ⚠️ 开发前检查清单

在开始任何开发之前，请确认：

- [ ] 已阅读 `ARCHITECTURE_PRINCIPLES.md`
- [ ] 理解"数据状态连续性"原则
- [ ] 理解"任务表是唯一中间数据"概念
- [ ] 知道如何区分"拆分器"和"转换器"
- [ ] 知道什么是禁止的做法

## 🚫 常见错误

1. **在拆分时创建CAPS任务** ← 错误！CAPS依赖翻译结果，应该在翻译后拆分
2. **LLM转换器处理CAPS任务** ← 错误！CAPS不需要LLM，应该用独立处理器
3. **假设输入一定是原始文件** ← 错误！任何状态都可能是输入
4. **在任务表中存储完整数据** ← 错误！任务表只存储位置和操作

## 📋 文档结构

```
translation_system_v2/
├── .claude/
│   ├── README.md                        # 本文件
│   ├── ARCHITECTURE_PRINCIPLES.md       # 核心架构理念 ⭐
│   ├── PIPELINE_REFACTOR_PLAN.md        # Pipeline重构方案 ⭐ (NEW)
│   └── settings.local.json              # Claude设置
│
├── CLAUDE.md                            # 项目总览（已更新）
│
└── backend_v2/
    ├── config/
    │   ├── rules.yaml                   # 拆分规则配置 (NEW)
    │   └── processors.yaml              # 处理器配置 (NEW)
    ├── models/
    │   └── pipeline_session.py          # Pipeline Session模型 (NEW)
    ├── services/factories/
    │   ├── rule_factory.py              # 规则工厂 (NEW)
    │   └── processor_factory.py         # 处理器工厂 (NEW)
    ├── utils/
    │   └── pipeline_session_manager.py  # Session管理器 (NEW)
    ├── SIMPLIFIED_ARCHITECTURE.md       # 简化架构设计
    └── PIPELINE_ARCHITECTURE.md         # 管道架构设计
```

## 🔄 开发流程 (新架构)

```
需求分析
    ↓
是拆分逻辑还是转换逻辑？
    ↓
    ├─→ 拆分逻辑:
    │   1. 创建Rule类 (services/splitter/rules/)
    │   2. 添加到 config/rules.yaml
    │   3. 添加到 rule_sets (如需要)
    │   4. 测试规则
    │
    └─→ 转换逻辑:
        1. 创建Processor类 (services/processors/)
        2. 添加到 config/processors.yaml
        3. 测试处理器
    ↓
通过API使用（配置驱动）
    ↓
更新文档
```

**示例：添加新的拆分规则**
```yaml
# config/rules.yaml
rules:
  my_custom:
    class: services.splitter.rules.my_custom.MyCustomRule
    priority: 5
    enabled: true

rule_sets:
  my_workflow:
    - my_custom
    - empty
```

**示例：添加新的处理器**
```yaml
# config/processors.yaml
processors:
  my_processor:
    class: services.processors.my_processor.MyProcessor
    type: custom
    enabled: true
```

## 💡 快速参考

### 判断是拆分器还是转换器

**拆分器 (Splitter)**：
- 分析数据，找出需要处理的位置
- 示例：找空单元格、找黄色单元格、找CAPS sheet

**转换器 (Transformer)**：
- 修改数据内容
- 示例：LLM翻译、大写转换、去空格

### 典型的两阶段流程 (新架构API)

```python
# 阶段1: 翻译
# Step 1: Split (包含analyze)
POST /api/tasks/split
Body: {
    "file": <upload>,
    "source_lang": "CH",
    "target_langs": ["EN"],
    "rule_set": "translation"
}
Response: {"session_id": "session-1"}

# Step 2: Execute
POST /api/execute/start
Body: {
    "session_id": "session-1",
    "processor": "llm_qwen"
}

# Step 3: Download (optional)
GET /api/download/session-1

# 阶段2: CAPS（依赖阶段1）
# Step 1: Split with parent
POST /api/tasks/split
Body: {
    "parent_session_id": "session-1",  # 继承翻译结果
    "rule_set": "caps_only"
}
Response: {"session_id": "session-2", "parent_session_id": "session-1"}

# Step 2: Execute
POST /api/execute/start
Body: {
    "session_id": "session-2",
    "processor": "uppercase"
}

# Step 3: Download final result
GET /api/download/session-2
```

**旧架构（代码级）vs 新架构（代码级）**
```python
# 旧架构（内部代码）
state_0 = load_excel("input.xlsx")
tasks_1 = splitter.split(state_0, rules=[Empty, Yellow])
state_1 = transformer.execute(state_0, tasks_1, processor=LLM)

# 新架构（内部代码 - Session-per-Transformation）
session_1 = PipelineSession()
session_1.input_state = load_excel("input.xlsx")
session_1.rules = ["empty", "yellow"]
session_1.tasks = splitter.split(session_1.input_state, session_1.rules)
session_1.output_state = transformer.execute(session_1.input_state, session_1.tasks, "llm_qwen")

# 阶段2通过parent_session_id链接
session_2 = PipelineSession(parent_session_id=session_1.session_id)
session_2.input_state = session_1.output_state  # 继承
session_2.rules = ["caps"]
session_2.tasks = splitter.split(session_2.input_state, session_2.rules)
session_2.output_state = transformer.execute(session_2.input_state, session_2.tasks, "uppercase")
```

## 🆘 遇到问题？

1. 检查是否违反了架构原则
2. 查看 `ARCHITECTURE_PRINCIPLES.md` 中的"禁止做法"
3. 参考 `SIMPLIFIED_ARCHITECTURE.md` 中的示例
4. 确保理解"数据状态连续性"概念

---

**记住核心理念：数据状态是连续的，任务表是唯一的中间数据！**
