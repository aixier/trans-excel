# ⚡ Spec-Driven Development 快速操作指南

## 🎯 你现在的状态

✅ **已完成：**
- npm 包已安装 (`@pimzino/claude-code-spec-workflow`)
- 项目已初始化 (`backend_spec` 目录)
- 所有命令已配置（14个 slash commands）
- 指导文档已创建（product.md, tech.md, structure.md）

## 🚀 立即开始（3步）

### Step 1: 重启 Claude Code
```bash
# 在终端执行（重要！必须重启才能加载命令）
claude --continue

# 或重新开始新会话
claude
```

### Step 2: 测试命令是否生效
在 Claude Code 中输入：
```
/spec-list
```
如果看到命令执行结果，说明安装成功。

### Step 3: 创建你的第一个功能
```
/spec-create test-feature "测试功能，验证系统是否正常工作"
```

---

## 📝 实战示例：创建 Excel 翻译功能

### 在 Claude Code 中执行：

```
/spec-create excel-translator "Excel文件翻译功能，支持批量处理，自动识别需翻译内容，保留格式和样式，实时进度追踪"
```

### 你会看到的流程：

#### 1️⃣ 第一阶段：需求分析
```
Claude: 我正在创建 Excel 翻译功能的规范...

🔍 分析现有代码库...
📝 生成需求文档...

[显示 requirements.md]

需求文档已生成，是否继续？(yes/no)
```
👉 **你的操作**：输入 `yes`

#### 2️⃣ 第二阶段：技术设计
```
Claude: 📐 生成技术设计...

[显示 design.md，包含架构图]

设计文档已生成，是否继续？(yes/no)
```
👉 **你的操作**：输入 `yes`

#### 3️⃣ 第三阶段：任务分解
```
Claude: 📋 分解任务...

[显示 tasks.md，列出所有任务]

任务列表已生成，是否生成任务命令？(yes/no)
```
👉 **你的操作**：输入 `yes`

#### 4️⃣ 第四阶段：开始实现
```
Claude: ✅ 任务命令已生成！

可以使用以下命令：
- /excel-translator-task-1
- /excel-translator-task-2
- /excel-translator-task-3
```
👉 **你的操作**：执行 `/excel-translator-task-1` 开始第一个任务

---

## 🔧 常用命令速查

| 命令 | 用途 | 示例 |
|-----|------|------|
| `/spec-create` | 创建新功能 | `/spec-create user-auth "用户认证"` |
| `/spec-status` | 查看进度 | `/spec-status` |
| `/spec-list` | 列出所有功能 | `/spec-list` |
| `/spec-execute` | 执行任务 | `/spec-execute 1 user-auth` |
| `/bug-create` | 报告Bug | `/bug-create login-fail "登录失败"` |

---

## 📂 文件位置参考

你的项目文件在这些位置：

```
/mnt/d/work/trans_excel/translation_system/backend_spec/
├── .claude/
│   ├── specs/              # 生成的规范文档在这里
│   │   └── excel-translator/
│   │       ├── requirements.md
│   │       ├── design.md
│   │       └── tasks.md
│   ├── steering/           # 项目指导文档
│   │   ├── product.md     # 产品愿景
│   │   ├── tech.md        # 技术标准
│   │   └── structure.md   # 项目结构
│   └── commands/          # 所有可用命令
```

---

## ❓ 遇到问题？

### 问题1：命令不可用
```bash
# 解决：重启 Claude Code
exit  # 退出当前会话
claude --continue  # 重新启动
```

### 问题2：不知道有哪些功能
```
# 在 Claude Code 中：
/spec-list  # 查看所有功能
/spec-status  # 查看进度
```

### 问题3：想修改生成的文档
- 小修改：直接编辑文件
- 大修改：重新运行 `/spec-create`

---

## 💡 专业提示

### 1. 详细描述功能
```
❌ 不好：/spec-create auth "认证"

✅ 好：/spec-create auth "用户认证系统，包含注册、登录、JWT令牌管理、
         密码重置、邮箱验证、角色权限控制、会话管理"
```

### 2. 分步执行任务
```
# 不要一次执行所有任务
/feature-task-1  # 执行
/spec-status     # 检查
/feature-task-2  # 继续
```

### 3. 利用 Bug 工作流
```
/bug-create issue-name "描述"  # 报告
/bug-analyze                    # 分析
/bug-fix                       # 修复
/bug-verify                    # 验证
```

---

## 🎉 现在就开始！

### 推荐的第一个命令：
```
/spec-create my-first-feature "我的第一个功能，用于测试系统是否正常工作"
```

### 或者创建实际功能：
```
/spec-create excel-analyzer "Excel文件分析器，识别需翻译内容"
```

---

## 📚 需要更多帮助？

- **完整指南**：查看 `COMPLETE_SPEC_DRIVEN_GUIDE.md`
- **项目示例**：查看 `backend_spec/INTEGRATION_EXAMPLE.md`
- **快速开始**：查看 `backend_spec/QUICK_START.md`

---

**记住核心流程：**
```
需求(Requirements) → 设计(Design) → 任务(Tasks) → 实现(Implementation)
```

每个阶段都需要你的确认（输入 yes）才会继续。

祝你使用愉快！ 🚀