# 🚀 Spec Commands 用法技巧与最佳实践完全指南

## 目录
1. [命令系统概览](#命令系统概览)
2. [规范开发命令详解](#规范开发命令详解)
3. [Bug修复命令详解](#bug修复命令详解)
4. [高级用法技巧](#高级用法技巧)
5. [团队协作最佳实践](#团队协作最佳实践)
6. [常见问题与解决方案](#常见问题与解决方案)

---

## 命令系统概览

### 🎯 命令分类

#### 核心开发命令（Core Development）
- `/spec-create` - 新功能规范创建器
- `/spec-execute` - 任务执行器
- `/spec-status` - 进度监控器
- `/spec-list` - 项目总览

#### 项目管理命令（Project Management）
- `/spec-steering-setup` - 项目初始化配置

#### Bug修复命令（Bug Fix Workflow）
- `/bug-create` - 问题报告器
- `/bug-analyze` - 根因分析器
- `/bug-fix` - 修复实施器
- `/bug-verify` - 验证器
- `/bug-status` - Bug状态查看器

### 📊 命令使用频率建议
```
每日必用: /spec-status, /spec-execute
每周常用: /spec-create, /bug-create
按需使用: /spec-list, /bug-analyze, /bug-fix
项目初期: /spec-steering-setup
```

---

## 规范开发命令详解

### `/spec-create` - 功能规范创建器

#### 🎯 核心作用
将一个功能想法转化为完整的开发规范，包含需求、设计、任务三个阶段。

#### 📝 语法格式
```bash
/spec-create <feature-name> "详细的功能描述"
```

#### 💡 命名技巧

**✅ 好的功能命名**
```bash
/spec-create user-authentication "用户认证系统"
/spec-create excel-batch-processor "Excel批量处理器"
/spec-create api-rate-limiter "API速率限制器"
/spec-create data-export-engine "数据导出引擎"
```

**❌ 避免的命名**
```bash
/spec-create auth "认证"           # 太简单
/spec-create user_auth "用户认证"   # 使用下划线
/spec-create Auth-System "认证系统" # 首字母大写
/spec-create 用户认证 "认证系统"     # 中文名称
```

#### 🔥 描述写作技巧

**模板公式**: `核心功能 + 关键特性 + 技术要求 + 业务价值`

**顶级描述示例**:
```bash
/spec-create translation-optimizer "翻译优化引擎，支持批量文本预处理、智能分块、多LLM负载均衡、翻译缓存、质量评分，降低翻译成本80%，提升处理速度5倍"

/spec-create user-session-manager "用户会话管理系统，包含JWT令牌生成、刷新机制、多设备登录控制、会话安全监控、异常登录检测，支持单点登录SSO集成"

/spec-create file-processing-pipeline "文件处理流水线，支持多格式上传(Excel/CSV/JSON)、数据验证、格式转换、批量处理、进度追踪、错误恢复，处理能力1000文件/小时"
```

#### 🔄 完整工作流程

**阶段1: 需求阶段 (Requirements)**
```
AI执行内容:
- 🔍 分析功能描述，提取核心需求
- 📚 查找项目中的相关模块和依赖
- 👥 生成用户故事 (User Stories)
- ✅ 定义验收标准 (Acceptance Criteria)
- 📋 创建需求文档 requirements.md

你的最佳实践:
✅ 仔细阅读生成的用户故事，确保符合实际需求
✅ 检查验收标准是否可测试、可衡量
✅ 确认需求覆盖了所有重要场景
✅ 输入 "yes" 确认，或提出具体修改建议
❌ 不要匆忙确认，这是质量的基础
```

**阶段2: 设计阶段 (Design)**
```
AI执行内容:
- 🏗️ 基于需求设计技术架构
- 📊 生成系统组件图和数据流图
- 🔧 定义API接口和数据模型
- 🎯 规划与现有系统的集成方案
- 📄 创建设计文档 design.md

你的最佳实践:
✅ 验证技术选型是否符合项目标准 (参考 tech.md)
✅ 检查架构设计的可扩展性和维护性
✅ 确认API设计的RESTful风格和一致性
✅ 评估性能影响和资源需求
❌ 不要忽视非功能性需求 (性能、安全、可用性)
```

**阶段3: 任务阶段 (Tasks)**
```
AI执行内容:
- 📋 将设计分解为具体的开发任务
- 🔗 分析任务间的依赖关系
- 📊 设置任务优先级和估时
- ✅ 为每个任务定义完成标准
- 🧪 确保每个任务支持TDD开发
- 📄 创建任务文档 tasks.md

你的最佳实践:
✅ 确认任务粒度适中 (不超过1天工作量)
✅ 检查任务的独立性和可测试性
✅ 验证依赖关系的合理性
✅ 决定是否生成自动任务命令
❌ 不要让任务过大或过小
```

**阶段4: 命令生成 (Optional)**
```
选择生成命令时:
- 生成 /feature-name-task-1, /feature-name-task-2 等
- 每个命令对应一个具体任务
- 支持任务级别的进度追踪

选择手动执行时:
- 使用 /spec-execute task-id feature-name
- 更灵活的执行顺序
- 适合复杂的任务依赖关系
```

#### 🎓 高级技巧

**1. 渐进式规范法**
```bash
# 第一版: 基础版本
/spec-create user-auth "基础用户认证，邮箱密码登录"

# 第二版: 扩展版本 (在基础版本完成后)
/spec-create user-auth-advanced "扩展认证功能，社交登录、双因子认证、单点登录"
```

**2. 模块化拆分法**
```bash
# 大功能拆分为多个小规范
/spec-create data-import "数据导入模块"
/spec-create data-validation "数据验证模块"
/spec-create data-processing "数据处理模块"
/spec-create data-export "数据导出模块"
```

**3. 依赖声明法**
```bash
# 在功能描述中明确依赖
/spec-create order-payment "订单支付功能，依赖已完成的user-auth和product-catalog，集成第三方支付API"
```

---

### `/spec-execute` - 任务执行器

#### 🎯 核心作用
按照TDD方式执行规范中定义的具体任务，确保代码质量。

#### 📝 语法格式
```bash
/spec-execute <task-number> <feature-name>
```

#### 💡 使用技巧

**选择正确的任务**
```bash
# 先查看任务列表
/spec-status user-auth

# 执行第一个未完成的任务
/spec-execute 3 user-auth

# 使用自动生成的命令 (如果有)
/user-auth-task-3
```

#### 🔄 TDD执行流程

**Red-Green-Refactor循环**
```
1. 📖 读取任务定义和要求
2. 🧪 编写或更新失败的测试 (Red)
3. 💻 编写最小可行代码让测试通过 (Green)
4. 🔧 重构代码提高质量 (Refactor)
5. 📝 更新文档和任务状态
6. ✅ 提交代码变更
```

#### 🎓 执行最佳实践

**1. 任务准备检查清单**
```
□ 确认前置任务已完成
□ 理解任务的具体要求
□ 查看相关的设计文档
□ 准备测试数据和环境
□ 检查代码分支状态
```

**2. 测试优先原则**
```python
# ✅ 正确的TDD步骤

# Step 1: 写测试 (Red)
def test_user_login_success():
    user = User.create(email="test@example.com", password="password123")
    result = auth_service.login("test@example.com", "password123")
    assert result.success == True
    assert result.token is not None

# Step 2: 跑测试，确认失败
pytest test_auth.py::test_user_login_success  # 应该失败

# Step 3: 写最小实现 (Green)
def login(email, password):
    return LoginResult(success=True, token="fake-token")

# Step 4: 跑测试，确认通过
pytest test_auth.py::test_user_login_success  # 应该通过

# Step 5: 重构 (Refactor)
def login(email, password):
    user = User.find_by_email(email)
    if user and user.verify_password(password):
        token = jwt.encode({"user_id": user.id})
        return LoginResult(success=True, token=token)
    return LoginResult(success=False, token=None)
```

**3. 增量开发策略**
```
□ 先实现核心功能，再添加边缘情况
□ 每次提交都保持功能完整
□ 及时更新任务状态
□ 记录重要决策和权衡
```

---

### `/spec-status` - 进度监控器

#### 🎯 核心作用
实时了解项目进度，识别瓶颈，指导工作优先级。

#### 📝 语法格式
```bash
/spec-status                    # 查看所有规范状态
/spec-status <feature-name>     # 查看特定功能详情
```

#### 💡 解读技巧

**状态符号含义**
```
✅ 已完成    - 该阶段已完成并通过验证
🔄 进行中    - 正在执行中
⏳ 待开始    - 计划中但未开始
⚠️  需要注意  - 存在问题或延期
🔒 被阻塞    - 等待其他任务完成
```

**进度数据分析**
```
Implementation: 3/8 tasks complete
- 已完成任务: 3个
- 总任务数: 8个
- 完成率: 37.5%
- 预估剩余工作量: 5个任务
```

#### 🎓 使用最佳实践

**1. 日常工作流程**
```bash
# 🌅 每日开始工作前
/spec-status                    # 查看昨天的进度
/spec-status current-feature    # 确认今天的任务

# 🌙 每日工作结束后
/spec-status                    # 确认今天的成果
# 提交代码并更新状态
```

**2. 问题识别模式**
```
⚠️ 危险信号:
- 某个任务卡住超过2天
- 多个功能同时进行中
- 任务依赖关系混乱
- 测试覆盖率低于80%

✅ 健康信号:
- 任务按顺序完成
- 每天都有进展
- 测试和文档同步更新
- 代码质量保持稳定
```

**3. 团队协作应用**
```bash
# 晨会准备
/spec-status > daily_progress.txt

# 向经理汇报
/spec-status | grep "Complete\|Progress"

# 帮助同事了解项目
/spec-list | head -5
```

---

### `/spec-list` - 项目总览

#### 🎯 核心作用
提供项目级别的健康检查，快速了解所有功能的整体状况。

#### 📝 语法格式
```bash
/spec-list
```

#### 💡 解读技巧

**项目健康度评估**
```
📊 健康项目特征:
- 大部分功能处于实现阶段
- 没有长期停滞的规范
- 新功能持续添加
- Bug修复及时响应

⚠️ 需要关注的情况:
- 多个功能卡在需求阶段
- 实现阶段任务完成率低
- 长时间没有新功能
- Bug数量持续增长
```

#### 🎓 使用场景

**1. 项目规划**
```bash
# 季度规划会议前
/spec-list > quarterly_status.md

# 识别优先级
grep "Planning" quarterly_status.md  # 找到规划阶段的功能
grep "Complete" quarterly_status.md  # 统计已完成功能
```

**2. 资源分配**
```bash
# 新人分配任务
/spec-list | grep "In Progress"     # 找到进行中的功能
/spec-status feature-name           # 查看具体任务难度
```

**3. 风险识别**
```bash
# 识别风险功能
/spec-list | grep -E "(⚠️|🔒)"      # 找到有问题的功能
# 制定应对措施
```

---

### `/spec-steering-setup` - 项目初始化

#### 🎯 核心作用
为新项目或现有项目创建指导性文档，让AI深度理解项目背景和约束。

#### 📝 语法格式
```bash
/spec-steering-setup
```

#### 🔄 执行流程

**自动分析阶段**
```
AI会自动分析:
1. 📂 项目目录结构
2. 📦 依赖配置文件 (package.json, requirements.txt等)
3. 📄 现有文档 (README, CHANGELOG等)
4. 💻 源代码模式和约定
5. 🏗️ 架构特征和技术栈
```

**交互确认阶段**
```
AI会展示推断结果:
- Product Details: 产品目标和用户价值
- Technology Stack: 技术栈和工具选择
- Project Structure: 文件组织和命名规范

你需要确认或修正这些推断
```

**文档生成阶段**
```
生成三个核心文档:
- product.md: 产品愿景和业务目标
- tech.md: 技术标准和开发规范
- structure.md: 项目结构和组织方式
```

#### 🎓 最佳实践

**1. 项目启动时机**
```
✅ 最佳时机:
- 新项目刚创建
- 团队成员加入
- 技术栈重大变更
- 开发规范更新

❌ 避免时机:
- 项目进行中途 (除非必要)
- 频繁修改 (保持稳定)
```

**2. 文档维护策略**
```
定期更新(每季度):
- 检查技术栈是否变化
- 更新项目目标和优先级
- 调整开发规范和最佳实践

重大变更时立即更新:
- 架构重构
- 技术栈升级
- 团队扩张
- 业务方向调整
```

---

## Bug修复命令详解

### Bug修复工作流概览

Bug修复采用轻量级的4阶段流程：**Report → Analyze → Fix → Verify**

```mermaid
graph LR
    A[/bug-create] --> B[/bug-analyze]
    B --> C[/bug-fix]
    C --> D[/bug-verify]
    D --> E[✅ 完成]
```

---

### `/bug-create` - 问题报告器

#### 🎯 核心作用
系统化地记录问题，确保信息完整，为后续分析奠定基础。

#### 📝 语法格式
```bash
/bug-create <bug-name> "详细的问题描述"
```

#### 💡 Bug命名规范

**命名模式**: `[模块]-[问题类型]-[简短描述]`

```bash
# ✅ 优秀的Bug命名
/bug-create login-timeout-mobile "移动端登录超时问题"
/bug-create export-memory-leak "Excel导出内存泄漏"
/bug-create api-rate-limit-error "API速率限制错误处理"
/bug-create ui-layout-broken-safari "Safari浏览器布局错乱"

# ❌ 避免的命名
/bug-create bug1 "有个问题"              # 太简单
/bug-create LoginTimeoutProblem "登录超时" # 驼峰命名
/bug-create 登录问题 "用户无法登录"        # 中文命名
```

#### 🔥 问题描述写作技巧

**STAR模板**: Situation(情况) + Task(任务) + Action(操作) + Result(结果)

```bash
# 🏆 金标准描述示例
/bug-create data-corruption-batch "批量导入时数据损坏：当用户上传包含特殊字符(如emoji)的Excel文件进行批量导入时，系统在处理过程中将特殊字符转换为乱码，导致最终导出的文件中用户名称显示错误，影响约15%的批量导入操作"

# 包含的关键信息：
# - 触发条件：特殊字符Excel文件
# - 操作路径：批量导入 → 处理 → 导出
# - 具体表现：特殊字符变乱码
# - 影响范围：15%的操作
# - 业务影响：用户名称错误
```

**问题描述检查清单**
```
□ 问题出现的具体场景
□ 重现步骤 (1, 2, 3...)
□ 期望的正确行为
□ 实际的错误行为
□ 影响范围和严重程度
□ 错误信息或截图
□ 环境信息 (浏览器、版本等)
```

#### 🔄 执行流程

**自动创建结构**
```
.claude/bugs/bug-name/
├── report.md      # 问题报告 (此阶段生成)
├── analysis.md    # 根因分析 (下阶段生成)
├── fix.md         # 修复方案 (下阶段生成)
└── verification.md # 验证报告 (最后生成)
```

**报告内容结构**
```markdown
# Bug Report: bug-name

## Problem Description
[详细描述问题]

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
[应该发生什么]

## Actual Behavior
[实际发生什么]

## Environment
- OS: [操作系统]
- Browser: [浏览器版本]
- Version: [软件版本]

## Additional Information
[其他相关信息]
```

---

### `/bug-analyze` - 根因分析器

#### 🎯 核心作用
深入分析问题的根本原因，而不仅仅是表面现象。

#### 📝 语法格式
```bash
/bug-analyze
```

#### 🔍 分析方法论

**5Why分析法**
```
为什么用户登录失败？
└─ 因为数据库连接超时
   └─ 为什么数据库连接超时？
      └─ 因为连接池被耗尽
         └─ 为什么连接池被耗尽？
            └─ 因为连接没有正确释放
               └─ 为什么连接没有正确释放？
                  └─ 因为异常处理中缺少finally块
```

**根因分类**
```
🐛 代码缺陷 (Code Defects)
- 逻辑错误
- 边界条件处理
- 异常处理不当
- 数据类型错误

🏗️ 设计问题 (Design Issues)
- 架构不当
- 性能瓶颈
- 扩展性限制
- 用户体验问题

🔧 配置错误 (Configuration Errors)
- 环境配置
- 参数设置
- 权限问题
- 网络配置

🌍 环境因素 (Environmental Factors)
- 硬件限制
- 第三方服务
- 网络问题
- 并发冲突
```

#### 🎓 分析最佳实践

**1. 数据收集**
```bash
# 收集日志
grep "ERROR" /var/log/app.log | tail -20

# 检查系统资源
top, htop, iostat

# 数据库状态
SHOW PROCESSLIST;
SHOW ENGINE INNODB STATUS;

# 网络状态
netstat -an | grep :8080
```

**2. 假设验证**
```
假设 → 测试 → 确认/排除

例如：
假设：内存泄漏导致性能下降
测试：使用内存分析工具监控
结果：确认内存使用持续增长
结论：假设成立，定位到具体代码
```

---

### `/bug-fix` - 修复实施器

#### 🎯 核心作用
基于根因分析实施具体的修复方案，确保问题彻底解决。

#### 📝 语法格式
```bash
/bug-fix
```

#### 🔧 修复策略

**修复类型分类**
```
🚀 快速修复 (Hot Fix)
- 关键业务功能故障
- 安全漏洞
- 数据丢失风险
- 性能严重退化

📋 常规修复 (Regular Fix)
- 功能性Bug
- 用户体验问题
- 性能优化
- 代码重构

🔄 长期重构 (Long-term Refactor)
- 架构问题
- 技术债务
- 设计改进
- 扩展性提升
```

#### 🎓 修复最佳实践

**1. 修复前准备**
```bash
# 创建修复分支
git checkout -b fix/bug-name

# 编写失败测试 (重现Bug)
pytest test_bug_reproduction.py  # 应该失败

# 备份相关数据
mysqldump database > backup.sql
```

**2. 修复实施**
```python
# ✅ 好的修复示例

# Before: 有Bug的代码
def process_user_data(data):
    result = []
    for item in data:
        result.append(item.upper())  # 假设某些item可能是None
    return result

# After: 修复后的代码
def process_user_data(data):
    result = []
    for item in data:
        if item is not None:  # 添加空值检查
            result.append(item.upper())
        else:
            logging.warning(f"Skipping None item in user data")
    return result

# 添加测试
def test_process_user_data_with_none():
    data = ["hello", None, "world"]
    result = process_user_data(data)
    assert result == ["HELLO", "WORLD"]
```

**3. 修复验证**
```bash
# 运行修复测试
pytest test_bug_reproduction.py  # 现在应该通过

# 运行回归测试
pytest tests/ -v

# 代码质量检查
flake8 modified_files.py
mypy modified_files.py
```

---

### `/bug-verify` - 验证器

#### 🎯 核心作用
全面验证修复效果，确保问题解决且未引入新问题。

#### 📝 语法格式
```bash
/bug-verify
```

#### ✅ 验证清单

**功能验证**
```
□ 原始问题已解决
□ 重现步骤不再触发Bug
□ 边界条件正常处理
□ 错误处理逻辑正确
□ 性能指标达标
```

**回归验证**
```
□ 所有单元测试通过
□ 集成测试通过
□ 相关功能未受影响
□ 数据完整性保持
□ 用户体验未降级
```

**部署验证**
```
□ 开发环境验证
□ 测试环境验证
□ 预生产环境验证
□ 生产环境监控
□ 用户反馈收集
```

#### 🎓 验证最佳实践

**1. 多层验证策略**
```
第一层：开发者自验证
- 本地测试环境
- 单元和集成测试
- 代码审查

第二层：QA团队验证
- 专业测试环境
- 端到端测试
- 用户场景测试

第三层：生产环境验证
- 灰度发布
- 监控指标
- 用户反馈
```

**2. 验证文档模板**
```markdown
# Bug Verification Report

## Fix Summary
- Bug: [bug-name]
- Root Cause: [根本原因]
- Fix Method: [修复方法]
- Files Changed: [修改的文件]

## Verification Results

### Functional Testing
- ✅ Original issue resolved
- ✅ Reproduction steps no longer trigger bug
- ✅ Edge cases handled properly

### Regression Testing
- ✅ Unit tests: 156/156 passed
- ✅ Integration tests: 23/23 passed
- ✅ Related features unaffected

### Performance Impact
- Response time: 45ms (baseline: 50ms) ✅
- Memory usage: No significant change ✅
- Database queries: Optimized ✅

## Deployment Status
- Dev: ✅ Verified
- Test: ✅ Verified
- Production: 🔄 Deployed, monitoring

## Sign-off
- Developer: [Name] ✅
- QA Lead: [Name] ✅
- Product Owner: [Name] ✅
```

---

### `/bug-status` - Bug状态查看器

#### 🎯 核心作用
追踪所有Bug的处理进度，提供项目质量概览。

#### 📝 语法格式
```bash
/bug-status                    # 查看所有Bug状态
/bug-status <bug-name>         # 查看特定Bug详情
```

#### 📊 状态解读

**Bug生命周期状态**
```
📝 报告阶段 (Reported)
- 刚创建，等待分析

🔍 分析阶段 (Analyzing)
- 正在调查根因

🔧 修复阶段 (Fixing)
- 实施修复方案

✅ 验证阶段 (Verifying)
- 测试修复效果

🎯 已完成 (Resolved)
- 修复完成并验证

🔄 重新开放 (Reopened)
- 修复后又出现问题
```

#### 🎓 使用技巧

**1. 质量仪表板**
```bash
# 每日Bug检查
/bug-status | grep -E "(🔧|✅)" | wc -l    # 活跃Bug数量

# 每周质量报告
/bug-status > weekly_bugs.txt
grep "Resolved" weekly_bugs.txt | wc -l    # 解决的Bug数
grep "Reported" weekly_bugs.txt | wc -l   # 新增的Bug数
```

**2. 优先级管理**
```
高优先级 (立即处理):
- 安全漏洞
- 数据丢失
- 服务中断
- 支付问题

中优先级 (1-2天):
- 功能异常
- 性能问题
- 用户体验
- 兼容性问题

低优先级 (计划处理):
- 界面优化
- 功能增强
- 代码重构
- 文档更新
```

---

## 高级用法技巧

### 🔄 命令组合模式

#### 快速项目评估模式
```bash
/spec-list              # 项目健康度总览
↓
/spec-status            # 详细进度分析
↓
/bug-status             # 质量状况检查
↓
制定工作计划
```

#### 新功能开发模式
```bash
/spec-create feature-name "description"
↓ (审查确认各阶段)
/spec-execute 1 feature-name
↓
/spec-status feature-name
↓
重复执行直到完成
```

#### 问题解决模式
```bash
/bug-create bug-name "description"
↓
/bug-analyze
↓
/bug-fix
↓
/bug-verify
↓
/bug-status (确认关闭)
```

### 🚀 效率提升技巧

#### 1. 批量操作技巧
```bash
# 同时查看多个功能状态
for feature in auth payment export; do
  echo "=== $feature ==="
  /spec-status $feature
done

# 批量创建相关功能
features=(
  "user-registration|用户注册功能"
  "user-profile|用户资料管理"
  "user-settings|用户设置配置"
)

for item in "${features[@]}"; do
  name=$(echo $item | cut -d'|' -f1)
  desc=$(echo $item | cut -d'|' -f2)
  /spec-create $name "$desc"
done
```

#### 2. 模板化描述
```bash
# 创建功能描述模板
export AUTH_TEMPLATE="用户认证系统，支持邮箱密码登录、JWT令牌管理、会话保持、密码重置、账户锁定保护"
export API_TEMPLATE="RESTful API接口，包含CRUD操作、数据验证、错误处理、API文档、速率限制、版本控制"
export EXPORT_TEMPLATE="数据导出功能，支持多格式(Excel/CSV/PDF)、自定义字段、数据过滤、批量处理、进度显示、邮件通知"

# 使用模板
/spec-create user-auth "$AUTH_TEMPLATE"
/spec-create data-api "$API_TEMPLATE"
/spec-create report-export "$EXPORT_TEMPLATE"
```

#### 3. 智能化工作流
```bash
# 创建每日工作脚本
cat > daily_work.sh << 'EOF'
#!/bin/bash
echo "🌅 开始今日工作"

echo "📊 项目状态概览:"
/spec-list | head -5

echo "🎯 我的任务:"
/spec-status current-feature

echo "🐛 待处理Bug:"
/bug-status | grep -E "(🔧|🔍)"

echo "💡 建议下一步:"
# 基于状态输出建议
EOF

chmod +x daily_work.sh
```

### 📈 进阶自动化

#### 1. Git集成
```bash
# 创建Git钩子
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# 提交前自动更新任务状态
if git diff --cached --name-only | grep -E "(test_|_test\.py)"; then
  echo "🧪 检测到测试文件变更，可能任务完成"
  echo "请使用 /spec-status 确认任务进度"
fi
EOF

chmod +x .git/hooks/pre-commit
```

#### 2. 状态监控
```bash
# 创建状态监控脚本
cat > monitor_progress.sh << 'EOF'
#!/bin/bash
DATE=$(date +"%Y-%m-%d")
LOG_FILE="progress_$DATE.log"

echo "=== Daily Progress Report - $DATE ===" >> $LOG_FILE
/spec-list >> $LOG_FILE
echo "" >> $LOG_FILE
/bug-status >> $LOG_FILE

# 发送邮件报告 (可选)
if [ -n "$TEAM_EMAIL" ]; then
  mail -s "Daily Progress - $DATE" "$TEAM_EMAIL" < $LOG_FILE
fi
EOF
```

---

## 团队协作最佳实践

### 👥 角色分工

#### 项目经理 (Project Manager)
```bash
# 每日晨会准备
/spec-list > team_status.md
/bug-status | grep -E "(🔧|🔍)" > urgent_bugs.md

# 每周规划会议
/spec-list | grep "Planning" > next_sprint.md

# 向上汇报
/spec-list | grep "Complete" | wc -l  # 完成功能数
/bug-status | grep "Resolved" | wc -l  # 解决Bug数
```

#### 技术负责人 (Tech Lead)
```bash
# 代码审查前准备
/spec-status feature-name  # 了解功能要求

# 架构决策
/spec-steering-setup  # 更新技术标准

# 质量把控
/bug-status | grep "🔧"  # 关注修复中的Bug
```

#### 开发人员 (Developer)
```bash
# 每日工作流程
/spec-status  # 查看自己的任务
/spec-execute task-id feature-name  # 执行任务
/spec-status feature-name  # 确认进度

# Bug处理
/bug-create bug-name "description"  # 发现Bug时
/bug-analyze  # 分析问题
/bug-fix  # 实施修复
```

#### QA工程师 (QA Engineer)
```bash
# 测试计划制定
/spec-status feature-name  # 了解功能实现情况

# Bug跟踪
/bug-status  # 监控Bug处理进度
/bug-verify  # 验证修复结果

# 质量报告
/bug-status | grep "Resolved" > quality_report.md
```

### 🔄 协作工作流程

#### 功能开发协作
```
1. 产品经理: 提出需求
2. 技术负责人: /spec-create feature-name "需求描述"
3. 团队讨论: 审查需求、设计、任务
4. 开发人员: /spec-execute task-id feature-name
5. QA工程师: 验证功能实现
6. 产品经理: 确认业务价值
```

#### Bug处理协作
```
1. 任何人发现: /bug-create bug-name "description"
2. 技术负责人: 分配给合适的开发人员
3. 开发人员: /bug-analyze → /bug-fix
4. QA工程师: /bug-verify
5. 产品经理: 确认业务影响消除
```

### 📋 团队规范

#### 命名约定
```
功能命名: [模块]-[功能]-[子功能]
- user-auth-login
- data-export-excel
- api-rate-limiter

Bug命名: [模块]-[类型]-[简述]
- login-timeout-mobile
- export-memory-leak
- api-validation-error
```

#### 描述标准
```
功能描述模板:
"[核心功能]，支持[特性列表]，[性能要求]，[业务价值]"

Bug描述模板:
"[问题现象]：[触发条件]时，[具体表现]，[影响范围]"
```

#### 工作节奏
```
每日 (Daily):
- 查看 /spec-status 了解任务进度
- 执行 1-2 个任务
- 更新任务状态

每周 (Weekly):
- 团队状态同步: /spec-list
- 质量回顾: /bug-status
- 下周规划

每月 (Monthly):
- 更新 steering 文档
- 优化工作流程
- 团队技能提升
```

---

## 常见问题与解决方案

### ❓ 命令执行问题

#### Q1: 命令无响应或报错
```
问题现象: 输入 /spec-create 后无反应

解决方案:
1. 检查命令格式是否正确
   /spec-create feature-name "description"

2. 确认 Claude Code 连接正常
   重启 Claude Code 应用

3. 检查项目目录是否正确
   cd /path/to/your/project

4. 验证 .claude 目录是否存在
   ls -la .claude/
```

#### Q2: 生成的文档不符合预期
```
问题现象: 需求文档太简单或太复杂

解决方案:
1. 优化功能描述的详细程度
   提供更多上下文信息

2. 检查 steering 文档是否配置
   /spec-steering-setup

3. 在确认阶段提出具体修改意见
   不要直接说 "yes"，指出需要改进的地方

4. 迭代改进
   可以重新运行 /spec-create 优化结果
```

### ❓ 工作流程问题

#### Q3: 任务依赖关系混乱
```
问题现象: 任务B依赖任务A，但A还没完成

解决方案:
1. 严格按照任务顺序执行
   /spec-status feature-name  # 查看依赖关系

2. 如果必须并行，确保接口定义清晰
   先完成接口设计任务

3. 使用Mock或Stub隔离依赖
   def mock_dependency():
       return {"status": "success", "data": "test"}
```

#### Q4: 多人协作冲突
```
问题现象: 多人同时修改同一个规范

解决方案:
1. 明确任务分配
   每个任务只分配给一个人

2. 使用分支策略
   git checkout -b feature/task-name

3. 及时同步状态
   完成任务立即更新 /spec-status

4. 建立沟通机制
   每日站会同步进度
```

### ❓ 质量控制问题

#### Q5: 测试覆盖率不足
```
问题现象: 任务完成但测试不充分

解决方案:
1. 强制TDD流程
   先写测试，再写实现

2. 设置覆盖率门槛
   pytest --cov=. --cov-fail-under=80

3. 代码审查检查测试
   每个PR都检查测试质量

4. 自动化检查
   在CI中加入覆盖率检查
```

#### Q6: 文档与代码不同步
```
问题现象: 代码已修改但规范文档未更新

解决方案:
1. 建立更新机制
   代码变更 → 规范更新 → 任务状态更新

2. 定期审查
   每周检查文档与代码的一致性

3. 自动化提醒
   Git钩子检查文档更新

4. 明确责任
   谁改代码谁更新文档
```

### ❓ 性能和扩展问题

#### Q7: 规范文档过多难以管理
```
问题现象: /spec-list 输出太长难以阅读

解决方案:
1. 使用分层管理
   /spec-list | grep "Complete"     # 只看完成的
   /spec-list | grep "In Progress"  # 只看进行中的

2. 归档已完成功能
   mkdir .claude/specs/archived/
   mv completed-specs .claude/specs/archived/

3. 使用标签分类
   在功能名中加入分类前缀
   auth-*, data-*, ui-*

4. 定期清理
   每季度归档旧的规范
```

#### Q8: Bug数量增长过快
```
问题现象: 新Bug比解决的Bug多

解决方案:
1. 分析Bug趋势
   /bug-status | grep "Reported" | wc -l  # 新增数量
   /bug-status | grep "Resolved" | wc -l  # 解决数量

2. 优先级管理
   先解决高优先级Bug

3. 预防性措施
   加强代码审查
   提高测试覆盖率
   定期代码质量检查

4. 团队技能提升
   Bug分析技能培训
   最佳实践分享
```

---

## 🎯 总结和建议

### 成功使用Spec Commands的关键

#### 1. 理念转变
```
从 "想到什么做什么"
到 "规范指导实现"

从 "个人经验驱动"
到 "标准流程驱动"

从 "文档与代码分离"
到 "文档驱动开发"
```

#### 2. 工具精通
```
掌握每个命令的核心作用
理解命令间的协作关系
形成个人的使用习惯
建立团队的工作规范
```

#### 3. 持续改进
```
定期回顾工作流程效果
收集团队反馈优化规范
更新 steering 文档内容
分享最佳实践经验
```

### 开始你的Spec-Driven之旅

#### 第一周：基础掌握
```
Day 1: /spec-steering-setup + 阅读生成的文档
Day 2-3: /spec-create 创建第一个简单功能
Day 4-5: /spec-execute 完成几个任务
Day 6-7: /spec-status + /spec-list 熟悉监控
```

#### 第二周：工作流熟练
```
Day 1-3: 完成第一个完整功能
Day 4-5: 体验 Bug 修复工作流
Day 6-7: 团队协作和经验总结
```

#### 第三周：深度应用
```
Day 1-2: 高级技巧和自动化
Day 3-4: 团队规范制定
Day 5-7: 持续优化和改进
```

记住：**工具的价值在于正确使用**。投入时间学习这些命令的正确用法，会让你的开发效率和代码质量都有质的提升！

立即开始：
```bash
/spec-steering-setup
```

祝你在 Spec-Driven Development 的道路上越走越顺！🚀