# Claude Code 集成指南 - Step by Step

## 前置准备

### 1. 安装 Claude Code
```bash
# 确保已安装 Claude Code CLI
# 访问 https://claude.ai/code 获取安装说明
```

### 2. 项目结构准备
```bash
# 进入项目目录
cd /mnt/d/work/trans_excel/translation_system/backend_spec

# 确认目录结构
ls -la
# 应该看到:
# - spec.md (项目规范)
# - CLAUDE.md (Claude 配置)
# - commands/ (自定义命令)
# - specs/ (规范文档)
```

## Step 1: 初始化 Spec-Driven 项目

### 1.1 创建基础规范文件
```bash
# 如果还没有 spec.md，创建它
touch spec.md

# 编辑 spec.md，定义项目规范
# 参考 backend_spec/spec.md 模板
```

### 1.2 配置 CLAUDE.md
```bash
# 创建 CLAUDE.md 配置文件
touch CLAUDE.md

# 添加以下基础配置:
cat << 'EOF' > CLAUDE.md
# Claude Code Configuration

## Project Overview
[项目描述]

## Development Philosophy
- 规范优先
- 测试驱动
- 最小化代码

## Technology Stack
[技术栈列表]

## Common Tasks
[常用任务说明]
EOF
```

### 1.3 创建命令目录
```bash
mkdir -p .claude commands specs docs tests
```

## Step 2: 设置开发工作流

### 2.1 安装开发命令
```bash
# 复制命令脚本
cp commands/*.sh ./

# 设置执行权限
chmod +x *.sh

# 命令说明:
# - specify.sh: 生成需求规范
# - plan.sh: 生成技术方案
# - tasks.sh: 生成任务列表
# - implement.sh: TDD 实现助手
# - verify.sh: 验证检查
```

### 2.2 创建第一个需求
```bash
# 运行需求分析
./specify.sh

# 输入需求描述，例如:
# "创建用户认证系统，支持 JWT 登录"
# 输入 END 结束

# 查看生成的需求文档
ls specs/requirement_*.md
```

### 2.3 生成技术方案
```bash
# 基于需求生成技术方案
./plan.sh

# 查看生成的方案
ls specs/plan_*.md
```

### 2.4 分解任务
```bash
# 生成任务列表
./tasks.sh

# 查看任务分解
cat specs/tasks_*.md
```

## Step 3: 与 Claude Code 交互

### 3.1 启动 Claude Code
```bash
# 在项目目录启动 Claude
claude-code

# Claude 会自动读取 CLAUDE.md 配置
```

### 3.2 使用 Slash Commands

#### 基础命令
```bash
# 需求分析
/specify 添加批量导入功能，支持 CSV 和 Excel

# 技术规划
/plan 使用 pandas 处理文件，celery 异步任务

# 任务分解
/tasks 生成开发任务列表

# 开始实现
/implement 按 TDD 方式实现功能
```

#### 自定义命令
```bash
# 在 .claude/commands/ 创建自定义命令
cat > .claude/commands/test-api.js << 'EOF'
module.exports = {
  name: 'test-api',
  description: '测试 API 端点',
  async execute(context) {
    // 运行 API 测试
    const { exec } = require('child_process');
    exec('pytest tests/test_api.py -v', (error, stdout) => {
      console.log(stdout);
    });
  }
}
EOF
```

### 3.3 典型对话示例

```markdown
User: 按照 spec.md 实现文件上传 API

Claude: 我会按照 spec.md 中的规范实现文件上传 API。首先创建测试文件...
[创建 test_upload_api.py]
[创建 upload_api.py]
[运行测试确保通过]

User: 优化 DataFrame 内存使用

Claude: 我会查看当前 DataFrame 使用情况并进行优化...
[分析内存使用]
[实现优化方案]
[验证优化效果]
```

## Step 4: TDD 开发流程

### 4.1 创建测试
```python
# tests/test_analyze_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_upload_file():
    """测试文件上传"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Given: 准备测试文件
        files = {"file": ("test.xlsx", b"content", "application/xlsx")}

        # When: 上传文件
        response = await client.post("/api/analyze/upload", files=files)

        # Then: 验证响应
        assert response.status_code == 200
        assert "session_id" in response.json()
```

### 4.2 运行测试（RED）
```bash
pytest tests/test_analyze_api.py -v
# 测试失败 - 因为还没有实现
```

### 4.3 实现功能（GREEN）
```python
# api/analyze_api.py
from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/api/analyze")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 最小实现
    return {"session_id": "test-session-id"}
```

### 4.4 重构（REFACTOR）
```python
# 添加验证、错误处理、日志等
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # 验证文件
        validate_file(file)

        # 处理文件
        session_id = await process_file(file)

        logger.info(f"File uploaded: {file.filename}")
        return {"session_id": session_id}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## Step 5: 实际项目集成

### 5.1 从 backend_v2 迁移到 backend_spec

```bash
# 1. 分析现有代码
cd /mnt/d/work/trans_excel/translation_system/backend_v2
find . -name "*.py" | xargs wc -l

# 2. 创建迁移规范
cd ../backend_spec
./specify.sh
# 输入: "迁移 backend_v2 到 spec-driven 架构"

# 3. 生成迁移方案
./plan.sh

# 4. 分解迁移任务
./tasks.sh
```

### 5.2 逐步迁移模块

#### 阶段1: 迁移数据模型
```bash
# 与 Claude 对话
"按照 spec.md 迁移 backend_v2 的数据模型到 backend_spec"

# Claude 会:
# 1. 读取 backend_v2 的模型
# 2. 创建测试
# 3. 迁移代码
# 4. 验证功能
```

#### 阶段2: 迁移 API
```bash
# 逐个迁移 API
"迁移 analyze_api.py，保持接口兼容"
"迁移 task_api.py，添加测试覆盖"
"迁移 execute_api.py，优化性能"
```

#### 阶段3: 迁移服务层
```bash
# 迁移业务逻辑
"迁移 excel_analyzer 服务，使用 TDD"
"迁移 batch_executor，添加并发控制"
```

### 5.3 验证迁移结果

```bash
# 运行完整验证
./verify.sh

# 检查项:
# ✓ 项目结构
# ✓ Python 环境
# ✓ 代码质量
# ✓ 测试覆盖
# ✓ 文档完整
# ✓ 性能基准
# ✓ 安全检查
```

## Step 6: 持续集成

### 6.1 设置 Git Hooks
```bash
# .git/hooks/pre-commit
#!/bin/bash
./commands/verify.sh
if [ $? -ne 0 ]; then
    echo "验证失败，请修复问题后再提交"
    exit 1
fi
```

### 6.2 CI/CD 配置
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ --cov
      - name: Check coverage
        run: coverage report --fail-under=80
```

## Step 7: 日常开发流程

### 7.1 新功能开发
```bash
# 1. 创建需求
./specify.sh
"添加实时进度通知功能"

# 2. 与 Claude 讨论方案
"基于 WebSocket 实现实时通知，评估技术方案"

# 3. 生成任务
./tasks.sh

# 4. TDD 开发
"按照任务列表，使用 TDD 实现 WebSocket 功能"

# 5. 验证
./verify.sh
```

### 7.2 Bug 修复
```bash
# 1. 报告问题
"用户反馈：大文件上传失败"

# 2. 分析原因
"分析 upload_api.py 的大文件处理逻辑"

# 3. 编写测试重现
"创建测试用例重现大文件上传问题"

# 4. 修复问题
"修复大文件上传，使用流式处理"

# 5. 验证修复
"运行测试确认问题已修复"
```

### 7.3 性能优化
```bash
# 1. 性能分析
"分析当前 API 性能瓶颈"

# 2. 制定优化方案
"基于分析结果，制定优化方案"

# 3. 实施优化
"实现 DataFrame 内存优化"
"添加 Redis 缓存层"
"优化数据库查询"

# 4. 性能测试
"运行性能测试，对比优化前后"
```

## 最佳实践建议

### Do's ✅
1. **始终从 spec.md 开始** - 规范是唯一真理源
2. **坚持 TDD** - 先写测试，再写代码
3. **频繁验证** - 每次改动后运行 verify.sh
4. **保持文档同步** - 代码改动同步更新文档
5. **利用 Claude 的上下文** - 让 Claude 读取相关文件

### Don'ts ❌
1. **不要跳过测试** - 没有测试的代码是债务
2. **不要忽略规范** - 偏离规范会导致混乱
3. **不要过度设计** - 保持简单，按需演进
4. **不要手动重复** - 自动化所有重复任务
5. **不要忽视性能** - 定期运行性能测试

## 常见问题解决

### Q1: Claude 不理解项目结构？
```bash
# 确保 CLAUDE.md 配置正确
# 让 Claude 读取关键文件
"请先读取 spec.md 和 CLAUDE.md 了解项目"
```

### Q2: 测试运行失败？
```bash
# 检查依赖
pip install -r requirements.txt

# 检查环境变量
export PYTHONPATH=$PWD

# 详细错误信息
pytest tests/ -vv --tb=long
```

### Q3: 性能不达标？
```bash
# 使用性能分析工具
python -m cProfile -o profile.stats main.py
python -m pstats profile.stats

# 内存分析
python -m memory_profiler main.py
```

## 进阶技巧

### 1. 自定义 Claude 行为
```javascript
// .claude/config.js
module.exports = {
  beforeCommand: (command) => {
    console.log(`Running: ${command}`);
  },
  afterCommand: (command, result) => {
    if (command.includes('test')) {
      console.log('Test results:', result);
    }
  }
}
```

### 2. 批量任务自动化
```bash
# 创建批量执行脚本
cat > batch_implement.sh << 'EOF'
#!/bin/bash
for task in $(cat specs/tasks_*.md | grep "^- \[ \]" | head -5); do
    echo "实现: $task"
    # 调用 Claude API 或手动实现
done
EOF
```

### 3. 智能提示优化
```markdown
# 在 CLAUDE.md 添加提示模板
## Prompt Templates

### 功能实现
"按照 spec.md 的 [章节名] 实现 [功能名]，
要求：1) TDD 2) 类型标注 3) 错误处理 4) 日志记录"

### 代码审查
"审查 [文件名]，检查：1) 规范符合性 2) 性能问题 3) 安全隐患"
```

## 总结

通过本指南，您应该能够：

1. ✅ 理解 Spec-Driven Development 的核心概念
2. ✅ 配置 Claude Code 项目环境
3. ✅ 使用 SDD 工作流开发功能
4. ✅ 将现有项目迁移到 SDD 架构
5. ✅ 建立持续集成和质量保证流程

记住：**规范驱动一切，测试保证质量，Claude 加速开发**

祝您开发顺利！🚀