# 📁 .claude 目录结构深度解析

## 概述

`.claude` 目录是 Spec-Driven Development 的核心控制中心，包含了项目开发的所有规范、工作流程、配置和工具。它是 Claude Code 与项目交互的入口点，决定了 AI 如何理解和开发你的项目。

## 🏗️ 完整目录结构

```
.claude/
├── 📁 agents/                  # AI 专家代理系统
├── 📁 bugs/                   # Bug 修复工作流
├── 📁 commands/               # Slash 命令定义
├── 📁 specs/                  # 功能规范文档
│   ├── 📁 excel-processing/   # Excel处理规范
│   ├── 📁 translation-engine/ # 翻译引擎规范
│   ├── 📁 task-management/    # 任务管理规范
│   └── 📁 api-gateway/        # API网关规范
├── 📁 steering/               # 项目指导文档
├── 📁 templates/              # 文档模板
├── 📄 spec-config.json       # 项目配置
└── 📄 settings.local.json    # 本地设置
```

---

## 📂 各目录详细说明

### 1. `/agents/` - AI 专家代理系统

**作用**: 包含专门的 AI 代理，每个代理负责特定的开发任务

**核心理念**: 不同的开发任务需要不同的专业知识，通过专门的代理来处理

**典型代理类型**:
```
agents/
├── code-reviewer/        # 代码审查专家
├── test-writer/         # 测试编写专家
├── performance-optimizer/ # 性能优化专家
└── security-auditor/    # 安全检查专家
```

**实际意义**:
- 代码审查代理确保代码质量
- 测试代理自动生成完整测试
- 性能代理识别瓶颈并优化
- 安全代理检查漏洞和风险

### 2. `/bugs/` - Bug 修复工作流

**作用**: 存储所有 Bug 报告、分析、修复方案和验证记录

**核心理念**: 系统化的 Bug 处理流程，确保问题得到完整解决

**目录结构**:
```
bugs/
└── {bug-name}/          # 每个Bug一个目录
    ├── report.md        # Bug报告（现象、复现步骤）
    ├── analysis.md      # 根因分析（为什么发生）
    ├── fix.md          # 修复方案（如何解决）
    └── verification.md  # 验证记录（确认修复）
```

**工作流程**:
1. `/bug-create` → 生成 `report.md`
2. `/bug-analyze` → 生成 `analysis.md`
3. `/bug-fix` → 生成 `fix.md` + 实际修复
4. `/bug-verify` → 生成 `verification.md`

**实际价值**:
- 建立完整的问题解决知识库
- 避免同类问题重复出现
- 为团队提供问题解决经验

### 3. `/commands/` - Slash 命令定义

**作用**: 定义所有可用的 slash 命令，这是 Claude Code 的操作入口

**核心理念**: 通过结构化命令驱动开发，而不是自由对话

**命令分类**:

#### 功能开发命令
- `spec-create.md` - 创建新功能规范
- `spec-execute.md` - 执行具体任务
- `spec-status.md` - 查看项目进度
- `spec-list.md` - 列出所有功能
- `spec-steering-setup.md` - 项目初始化

#### Bug 修复命令
- `bug-create.md` - 报告新 Bug
- `bug-analyze.md` - 分析 Bug 原因
- `bug-fix.md` - 实施修复
- `bug-verify.md` - 验证修复
- `bug-status.md` - 查看 Bug 状态

**每个命令文件包含**:
- 命令语法和参数
- 执行逻辑和工作流
- 输出格式和规范
- 错误处理机制

### 4. `/specs/` - 功能规范文档

**作用**: 这是 Spec-Driven Development 的核心，包含所有功能的完整规范

**核心理念**: 每个功能都有完整的三阶段文档：需求→设计→任务

#### 单个功能规范结构
```
specs/excel-processing/
├── requirements.md    # 需求规范
├── design.md         # 技术设计
└── tasks.md          # 任务分解
```

#### 示例：excel-processing 规范

**requirements.md** - 回答"做什么"
```markdown
# Excel 处理需求规范

## 核心需求
- 支持 xlsx/xls 格式文件上传
- 自动识别需要翻译的文本内容
- 提取单元格格式和样式信息
- 支持多工作表处理

## 用户故事
作为翻译项目经理，我希望上传Excel文件后
系统能自动识别哪些内容需要翻译，
以便快速启动翻译任务。

## 验收标准
1. WHEN 用户上传Excel文件 THEN 系统 SHALL 在30秒内完成分析
2. IF 文件包含中文内容 THEN 系统 SHALL 标记为需翻译
3. WHEN 分析完成 THEN 系统 SHALL 返回可翻译内容统计
```

**design.md** - 回答"怎么做"
```markdown
# Excel 处理技术设计

## 架构设计
- 使用 pandas + openpyxl 处理Excel文件
- DataFrame作为内部数据结构
- 异步处理支持大文件

## 核心组件
- ExcelLoader: 文件加载和验证
- ContentAnalyzer: 内容识别和分类
- FormatExtractor: 样式和格式提取

## 数据流
Excel文件 → 解析器 → DataFrame → 内容分析 → 任务生成
```

**tasks.md** - 回答"分几步做"
```markdown
# Excel 处理任务分解

## Task 1: 创建文件上传接口
- Priority: High
- Dependencies: None
- 实现 POST /api/excel/upload
- 文件验证和大小限制
- 返回上传成功确认

## Task 2: 实现Excel解析器
- Priority: High
- Dependencies: Task 1
- 使用 pandas 读取Excel
- 提取所有工作表数据
- 生成 DataFrame 结构

## Task 3: 开发内容分析器
- Priority: Medium
- Dependencies: Task 2
- 识别文本类型（中文/英文/数字）
- 标记需要翻译的内容
- 提取上下文信息
```

### 5. `/steering/` - 项目指导文档

**作用**: 为 AI 提供项目的整体指导和约束，确保开发方向正确

**核心理念**: AI 需要了解项目的背景、目标和约束才能做出正确决策

#### 三个核心文件

**product.md** - 产品愿景
```markdown
# 产品愿景

## 项目使命
构建企业级Excel翻译管理系统

## 目标用户
- 游戏本地化团队
- 翻译项目经理
- 内容管理人员

## 核心价值
- 批量处理效率提升10倍
- 翻译成本降低50%
- 项目管理自动化
```

**tech.md** - 技术标准
```markdown
# 技术标准

## 技术栈
- Framework: FastAPI 0.104+
- Data: pandas 2.0+ + openpyxl
- Database: MySQL 8.0
- Cache: Redis 4.0+

## 代码规范
- Type hints for all functions
- Google style docstrings
- 80%+ test coverage
- Black code formatting

## 性能要求
- API response < 100ms P95
- 支持100MB Excel文件
- 1000+ 并发用户
```

**structure.md** - 项目结构
```markdown
# 项目结构

## 目录组织
api/        # API接口层
services/   # 业务逻辑层
models/     # 数据模型层
database/   # 数据访问层

## 命名规范
- 文件: snake_case.py
- 类: PascalCase
- 函数: snake_case
- 常量: UPPER_CASE
```

### 6. `/templates/` - 文档模板

**作用**: 标准化所有文档的格式和结构

**核心理念**: 一致的文档格式提高可读性和可维护性

**模板类型**:
- `requirements-template.md` - 需求文档模板
- `design-template.md` - 设计文档模板
- `tasks-template.md` - 任务文档模板
- `bug-report-template.md` - Bug报告模板

---

## 📄 配置文件说明

### `spec-config.json` - 项目配置

这是项目的核心配置文件，定义了：

```json
{
  "spec_workflow": {
    "version": "2.0.0",
    "project_type": "backend",
    "project_name": "Translation System Backend Spec",
    "project_status": "specification_phase",

    // 工作流配置
    "enforce_approval_workflow": true,  // 每阶段需要确认
    "auto_reference_requirements": true, // 自动引用需求

    // 架构信息
    "architecture": {
      "type": "dataframe-centric",
      "layers": ["api", "service", "model", "infrastructure"],
      "core_tech": ["fastapi", "pandas", "mysql", "redis"]
    },

    // 规范状态追踪
    "specifications": {
      "defined": ["excel-processing", "translation-engine"],
      "status": {
        "excel-processing": {
          "requirements": "defined",
          "design": "defined",
          "tasks": "defined",
          "implementation": "not_started"
        }
      }
    }
  }
}
```

### `settings.local.json` - 本地设置

开发者个人的本地配置，如：
- 编辑器偏好
- 调试设置
- 个人快捷命令

---

## 🔄 Spec-Driven Development 工作流体现

### 阶段1：规范定义
```bash
/spec-create excel-processor "Excel文件处理功能"
```
系统自动：
1. 创建 `specs/excel-processor/` 目录
2. 生成 `requirements.md` （需求规范）
3. 等待用户确认

### 阶段2：技术设计
确认需求后，系统：
1. 生成 `design.md` （技术设计）
2. 包含架构图、API设计、数据模型
3. 等待用户确认

### 阶段3：任务分解
确认设计后，系统：
1. 生成 `tasks.md` （任务清单）
2. 分解为可执行的小任务
3. 询问是否生成任务命令

### 阶段4：执行实现
```bash
/excel-processor-task-1  # 执行第一个任务
/excel-processor-task-2  # 执行第二个任务
```

---

## 💡 深层理念解释

### 为什么需要 `.claude` 目录？

1. **结构化开发**: 避免随意对话式编程
2. **知识积累**: 所有决策和过程都有记录
3. **团队协作**: 统一的规范和流程
4. **质量保证**: 强制性的审查和验证
5. **项目传承**: 完整的项目知识库

### Spec-Driven vs 传统开发

| 传统开发 | Spec-Driven Development |
|---------|------------------------|
| 想到什么写什么 | 先规范后编码 |
| 文档与代码分离 | 文档驱动代码 |
| 手动项目管理 | 自动任务追踪 |
| 个人经验驱动 | 标准流程驱动 |
| 质量靠运气 | 质量有保证 |

### AI 如何使用这个结构？

1. **读取 steering**: 了解项目背景和约束
2. **分析 specs**: 理解已有功能和架构
3. **执行 commands**: 按照定义的工作流操作
4. **更新状态**: 实时更新配置和进度
5. **积累知识**: 将经验写入 bugs 和 specs

---

## 🎯 实际开发价值

### 对开发者的价值
- **减少思考负担**: 有明确的工作流程
- **提高代码质量**: 强制的规范和审查
- **知识管理**: 完整的项目知识库
- **团队协作**: 统一的工作方式

### 对项目的价值
- **降低维护成本**: 清晰的文档和结构
- **提高开发效率**: 标准化的流程
- **减少bug率**: 系统化的测试和验证
- **便于扩展**: 模块化的规范管理

### 对团队的价值
- **新人快速上手**: 完整的项目指南
- **知识传承**: 不依赖个人经验
- **质量一致**: 统一的开发标准
- **协作效率**: 明确的分工和流程

---

## 🚀 使用建议

### 新项目启动时
1. 运行 `/spec-steering-setup` 创建指导文档
2. 编辑 product.md、tech.md、structure.md
3. 使用 `/spec-create` 创建第一个功能规范

### 日常开发中
1. 新功能先写规范，后写代码
2. Bug修复使用 bug-* 命令系列
3. 定期查看 `/spec-status` 了解进度

### 团队协作时
1. 规范文档作为沟通基础
2. 代码审查参考技术标准
3. 新人培训从 steering 文档开始

这个 `.claude` 目录结构体现了现代软件工程的最佳实践：**规范化、标准化、自动化**。它不仅仅是一个文件夹，而是一个完整的开发方法论的具体实现。