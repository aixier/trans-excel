# Spec-Driven Development 正确实践指南

基于 Translation System 项目的实际经验总结

## 📚 核心概念理解

### 什么是 Spec-Driven Development？

Spec-Driven 是一种**文档先行、规范驱动**的开发方法，强调：
- 📝 **规范先于代码** - 先写文档，再写代码
- 🔄 **阶段式推进** - 需求→设计→任务→实现
- ✅ **验证驱动** - 每个阶段都需验证通过
- 📊 **可追溯性** - 代码与需求完全对应

## ⚠️ 常见误区与正确做法

### 误区1：直接创建代码实现

❌ **错误做法**：
```python
# 在specs目录下直接创建实现代码
.claude/specs/excel-processing/
├── requirements.md
├── design.md
├── tasks.md
└── implementation.py  # ❌ 不应该在这里
```

✅ **正确做法**：
```
.claude/specs/          # 只放规范文档
├── excel-processing/
│   ├── requirements.md # 需求文档
│   ├── design.md      # 设计文档
│   └── tasks.md       # 任务列表

backend_spec/          # 实现代码在项目根目录
├── api/              # 根据规范实现的代码
├── services/
└── models/
```

### 误区2：混淆项目状态

❌ **错误理解**：
- 把已完成的项目标记为"待实现"
- 把规范当作已实现的代码
- 在错误的项目中创建规范

✅ **正确理解**：

| 项目 | 目的 | 状态 | 内容 |
|------|------|------|------|
| backend_v2 | 参考实现 | ✅ 已完成 | 完整的代码实现 |
| backend_spec | 新项目 | 📝 规范阶段 | 规范文档+待实现 |

### 误区3：跳过规范阶段

❌ **错误做法**：
```bash
# 直接开始编码
mkdir api services models
# 开始写代码...
```

✅ **正确做法**：
```bash
# 1. 先创建规范
/spec-create excel-processing "Excel处理功能"

# 2. 完成三个文档
- requirements.md  # 需求
- design.md       # 设计
- tasks.md        # 任务

# 3. 审核通过后才开始实现
/spec-execute 1 excel-processing
```

## 🎯 正确的工作流程

### 第一步：理解项目结构

```
project/
├── .claude/           # Spec-Driven 配置目录
│   ├── specs/        # 规范文档（核心）
│   ├── steering/     # 项目指导
│   ├── agents/       # AI代理
│   ├── commands/     # 命令定义
│   └── spec-config.json  # 配置文件
│
├── api/              # 实际实现代码
├── services/         # 业务逻辑
├── models/          # 数据模型
└── tests/           # 测试代码
```

### 第二步：规范阶段（.claude/specs/）

#### 2.1 创建需求文档
```markdown
# requirements.md
- 用户故事
- 验收标准
- 非功能需求
```

#### 2.2 创建设计文档
```markdown
# design.md
- 架构设计
- 接口定义
- 数据模型
```

#### 2.3 创建任务列表
```markdown
# tasks.md
- [ ] Task 1: 基础架构
- [ ] Task 2: 核心功能
- [ ] Task 3: 测试验证
```

### 第三步：实现阶段（项目根目录）

```bash
# 按任务逐个实现
/spec-execute 1 excel-processing

# 在正确的位置创建代码
touch api/excel_api.py
touch services/excel_service.py
touch models/excel_model.py
```

## 📋 实际案例分析

### Case 1: Translation System 项目结构

```
translation_system/
├── backend_v2/        # ✅ 已完成的参考实现
│   ├── api/          # 实际运行的代码
│   ├── services/
│   └── models/
│
├── backend_spec/      # 📝 Spec-Driven 新项目
│   ├── .claude/      # 规范配置
│   │   └── specs/    # 规范文档
│   │       ├── excel-processing/
│   │       │   ├── requirements.md
│   │       │   ├── design.md
│   │       │   └── tasks.md
│   │       └── [其他模块规范]/
│   │
│   └── [待实现的代码目录]
```

### Case 2: 正确的 spec-config.json

```json
{
  "spec_workflow": {
    "project_status": "specification_phase",  // 明确状态
    "implementation_status": "not_started",   // 实现未开始
    "specifications": {
      "excel-processing": {
        "requirements": "defined",    // 需求已定义
        "design": "defined",          // 设计已定义
        "tasks": "defined",           // 任务已定义
        "implementation": "not_started" // 实现未开始
      }
    }
  }
}
```

## 🔧 最佳实践

### 1. 文档质量检查清单

- [ ] **需求文档**
  - 用户故事完整
  - 验收标准明确
  - 边界条件考虑

- [ ] **设计文档**
  - 架构图清晰（使用ASCII图）
  - 接口定义完整
  - 错误处理说明

- [ ] **任务文档**
  - 任务原子化（2-4小时）
  - 依赖关系明确
  - 验收标准清晰

### 2. 命令使用顺序

```bash
# 1. 初始化项目
claude-code-spec-workflow

# 2. 设置项目指导
/spec-steering-setup

# 3. 创建功能规范
/spec-create feature-name "description"

# 4. 查看状态
/spec-status

# 5. 执行实现
/spec-execute task-id feature-name
```

### 3. 目录规范

| 目录 | 用途 | 内容 |
|------|------|------|
| .claude/specs/ | 规范文档 | 只放.md文档 |
| .claude/steering/ | 项目指导 | product.md, tech.md |
| .claude/agents/ | AI代理 | 验证器配置 |
| api/ | API实现 | Python代码 |
| services/ | 业务逻辑 | Python代码 |
| models/ | 数据模型 | Python代码 |

## ❌ 避免的错误

### 1. 错误的文件位置
```
❌ .claude/specs/feature/api.py
❌ .claude/specs/feature/service.py
✅ api/feature_api.py
✅ services/feature_service.py
```

### 2. 错误的状态理解
```
❌ "backend_v2 需要按规范实现"  # 它已经实现了
❌ "backend_spec 已经完成"      # 它还在规范阶段
✅ "backend_spec 基于规范待实现"
```

### 3. 错误的工作流
```
❌ 代码 → 文档
❌ 设计 → 需求
✅ 需求 → 设计 → 任务 → 代码
```

## 📊 状态管理矩阵

| 阶段 | 位置 | 产出 | 验证方式 |
|------|------|------|----------|
| 需求 | .claude/specs/*/requirements.md | 需求文档 | Agent验证 |
| 设计 | .claude/specs/*/design.md | 设计文档 | Agent验证 |
| 任务 | .claude/specs/*/tasks.md | 任务列表 | Agent验证 |
| 实现 | 项目根目录 | Python代码 | 单元测试 |

## 🎯 成功标志

✅ 项目成功实施 Spec-Driven 的标志：

1. **规范完整** - 所有功能都有完整的三个文档
2. **状态清晰** - spec-config.json 准确反映项目状态
3. **目录正确** - 规范与代码分离，位置正确
4. **流程规范** - 严格按照四阶段推进
5. **可追溯性** - 每行代码都能追溯到需求

## 💡 经验总结

### 从 Translation System 项目学到的

1. **明确区分规范与实现**
   - 规范在 .claude/specs/
   - 实现在项目根目录

2. **正确理解项目状态**
   - backend_v2 是参考
   - backend_spec 是新项目

3. **Agent 的价值**
   - 自动验证文档质量
   - 减少人为错误
   - 提高规范一致性

4. **配置文件的重要性**
   - spec-config.json 是项目状态的真实来源
   - 必须及时更新，准确反映实际状态

5. **ASCII图的优势**
   - 大模型理解更直接
   - 不需要额外渲染
   - 版本控制友好

## 🔄 持续改进

基于实践经验，建议：

1. **定期回顾** - 每周回顾规范执行情况
2. **及时调整** - 发现问题立即纠正
3. **经验沉淀** - 记录最佳实践
4. **工具优化** - 改进自动化工具

## 📝 实践中的关键点

### 1. 项目初始化时机
```bash
# ✅ 正确：在空项目或新项目中初始化
cd new-project
claude-code-spec-workflow

# ❌ 错误：在已完成的项目中初始化
cd completed-project
claude-code-spec-workflow  # 这会造成混淆
```

### 2. 规范文档的作用
```
需求文档 → 定义"做什么"
设计文档 → 定义"怎么做"
任务文档 → 定义"分步做"
```

### 3. 任务执行策略
```bash
# 小步快跑
/spec-execute 1 feature  # 完成第一个任务
git commit              # 提交
/spec-execute 2 feature  # 继续下一个
```

### 4. 验证的重要性
- 每个阶段都要验证
- 使用Agent自动验证
- 人工审核关键决策

## 🚀 高效工作流

### 1. 并行规范开发
```bash
# 可以同时定义多个模块的规范
/spec-create module-a "描述A"
/spec-create module-b "描述B"
```

### 2. 增量式实现
```bash
# 不需要等所有规范完成
# 可以先实现已定义的模块
/spec-execute 1 excel-processing
```

### 3. 迭代优化
```bash
# 实现过程中发现问题
# 可以回头修改规范
edit .claude/specs/feature/design.md
/spec-execute 5 feature  # 继续实现
```

---

*基于 Translation System Backend 项目实践总结*
*更新日期: 2025-01-29*
*版本: 2.0*