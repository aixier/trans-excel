# Translation System Backend Spec

## 🚀 快速开始

这个项目使用 **Spec-Driven Development** 方法，通过 Claude Code 的 slash commands 进行开发。

### 前置要求

1. 安装 Claude Code
2. 安装 npm 包（已完成）：
   ```bash
   npm install -g @pimzino/claude-code-spec-workflow
   ```

### 使用方法

在 Claude Code 中使用以下命令：

#### 1. 创建新功能
```bash
/spec-create feature-name "功能描述"
```

例如：
```bash
/spec-create excel-analyzer "Excel文件分析功能，自动识别需翻译内容"
```

#### 2. 执行任务
```bash
# 使用自动生成的命令
/feature-name-task-1

# 或手动执行
/spec-execute 1 feature-name
```

#### 3. 查看进度
```bash
/spec-status
```

#### 4. Bug 修复流程
```bash
/bug-create bug-name "问题描述"
/bug-analyze
/bug-fix
/bug-verify
```

## 📁 项目结构

```
backend_spec/
├── .claude/              # Claude Code 配置
│   ├── commands/         # Slash 命令定义
│   ├── specs/           # 功能规范文档
│   ├── bugs/            # Bug 修复记录
│   ├── steering/        # 项目指导文档
│   │   ├── product.md   # 产品愿景
│   │   ├── tech.md      # 技术标准
│   │   └── structure.md # 项目结构
│   └── templates/       # 文档模板
│
├── CLAUDE.md            # Claude Code 配置说明
├── package.json         # Node.js 配置
└── README.md           # 本文档
```

## 🔄 工作流程

1. **需求分析** → 自动生成 requirements.md
2. **技术设计** → 自动生成 design.md
3. **任务分解** → 自动生成 tasks.md
4. **实现开发** → TDD 方式逐个完成任务

## 📚 重要文档

- **产品愿景**: `.claude/steering/product.md`
- **技术标准**: `.claude/steering/tech.md`
- **项目结构**: `.claude/steering/structure.md`

## 🛠 技术栈

- **语言**: Python 3.10+
- **框架**: FastAPI
- **数据处理**: pandas
- **数据库**: MySQL + SQLAlchemy
- **缓存**: Redis
- **测试**: pytest

## 💡 开发原则

1. **Spec-Driven**: 所有开发从规范开始
2. **Test-Driven**: 先写测试，后写代码
3. **Context-Aware**: 遵循 steering 文档
4. **Iterative**: 小步迭代，频繁验证

## 📖 更多信息

- [Spec Workflow 官方文档](https://github.com/Pimzino/claude-code-spec-workflow)
- [集成示例](./INTEGRATION_EXAMPLE.md)

## 开始你的第一个功能

在 Claude Code 中运行：
```bash
/spec-create my-first-feature "我的第一个功能描述"
```

祝开发愉快！ 🎉