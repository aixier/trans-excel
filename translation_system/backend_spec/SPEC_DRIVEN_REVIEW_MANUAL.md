# 📖 Spec-Driven Development 人工核对手册

## 第一部分：理解 Spec-Driven 体系

### 1.1 核心理念
Spec-Driven Development（规范驱动开发）是一种确保软件开发质量的方法论：
- **先规范，后编码** - 所有代码必须有对应的规范文档
- **可追溯性** - 每行代码都能追溯到具体需求
- **渐进式细化** - 从抽象需求逐步细化到具体实现

### 1.2 三层文档体系
```
Requirements (需求) → Design (设计) → Tasks (任务)
     WHY                HOW            WHAT
   为什么做            怎么做          做什么
```

## 第二部分：规范文档核对清单

### 📋 2.1 Requirements.md 核对要点

#### A. 文档结构完整性
- [ ] 包含 Overview/Introduction 章节
- [ ] 明确的 User Stories（用户故事）
- [ ] 清晰的 Acceptance Criteria（验收标准）
- [ ] 与产品愿景的 Alignment 说明

#### B. 需求质量检查
```markdown
✅ 好的需求示例：
"WHEN 用户上传超过10MB的Excel文件
 THEN 系统SHALL 自动切换到分块处理模式
 AND 显示处理进度条"

❌ 差的需求示例：
"系统应该能处理大文件"
```

#### C. 验收标准检查
每个需求必须满足 **SMART** 原则：
- **S**pecific (具体) - 明确说明功能点
- **M**easurable (可测量) - 有明确的验收指标
- **A**chievable (可实现) - 技术上可行
- **R**elevant (相关) - 与业务目标相关
- **T**ime-bound (有时限) - 有实现优先级

### 📐 2.2 Design.md 核对要点

#### A. 技术架构检查
- [ ] 系统架构图清晰
- [ ] 数据流向明确
- [ ] 接口定义完整
- [ ] 错误处理策略

#### B. 设计决策记录
```markdown
## Architecture Decision Record (ADR)
决策：使用 pandas DataFrame 作为核心数据结构
原因：1. 高效的批量数据处理
      2. 丰富的数据转换功能
      3. 与 Excel 操作天然契合
替代方案：原生 Python dict（已评估，性能不足）
```

#### C. 接口设计规范
```python
# 检查接口是否符合 RESTful 规范
POST   /api/analyze/upload    # 上传文件
GET    /api/tasks/{id}         # 获取任务
PUT    /api/tasks/{id}/execute # 执行任务
DELETE /api/tasks/{id}         # 删除任务
```

### ✅ 2.3 Tasks.md 核对要点

#### A. 任务原子性检查
每个任务应该：
- [ ] 可在 2-4 小时内完成
- [ ] 有明确的完成定义
- [ ] 可独立测试验证
- [ ] 不依赖未完成的其他任务

#### B. 任务格式规范
```markdown
- [x] 1. 实现文件上传接口
  验证：POST /api/upload 返回 200
  测试：test_file_upload.py 通过

- [ ] 2. 添加文件大小验证
  验证：上传 >100MB 文件返回 413
  测试：test_large_file_rejection.py 通过
```

## 第三部分：代码实现核对

### 🔍 3.1 代码与规范对应检查

#### A. 追溯性验证
```python
# api/analyze_api.py
@router.post("/upload")
async def upload_file(file: UploadFile):
    """
    实现 requirements.md 中的 Requirement 1.1
    参考 design.md 中的 Section 3.2
    对应 tasks.md 中的 Task 1
    """
```

#### B. 测试覆盖验证
```bash
# 执行测试覆盖率检查
pytest tests/ --cov=. --cov-report=html

# 检查每个任务的测试
for task in tasks.md:
    assert exists(f"test_{task_name}.py")
    assert test_passes(task_name)
```

### 🏗️ 3.2 目录结构核对

```
backend_spec/
├── .claude/specs/          # ✅ 规范文档集中管理
│   └── feature-name/
│       ├── requirements.md # ✅ 需求已审批
│       ├── design.md       # ✅ 设计已评审
│       └── tasks.md        # ✅ 任务已分解
├── api/                    # ✅ 对应 design.md 的 API 设计
├── services/              # ✅ 对应 design.md 的业务逻辑
├── models/                # ✅ 对应 design.md 的数据模型
└── tests/                 # ✅ 对应 tasks.md 的测试用例
```

## 第四部分：质量门禁检查

### 🚦 4.1 代码质量指标

#### A. 静态代码分析
```bash
# Python 代码规范检查
black . --check           # 代码格式
flake8 .                  # 代码风格
mypy .                    # 类型检查
bandit -r .               # 安全扫描
```

#### B. 测试质量指标
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试全部通过
- [ ] 性能测试达标
- [ ] 边界条件已测试

### 📊 4.2 DataFrame 实现核对

#### A. 数据结构一致性
```python
# 检查 DataFrame 定义
class TaskDataFrame:
    required_columns = [
        'task_id',      # UUID
        'status',       # Enum
        'created_at',   # datetime
        'updated_at'    # datetime
    ]

    dtypes = {
        'task_id': 'string',
        'status': 'category',
        'created_at': 'datetime64[ns]',
        'updated_at': 'datetime64[ns]'
    }
```

#### B. 性能优化检查
```python
# ✅ 好的实践
df = pd.read_excel(file, chunksize=10000)  # 分块读取
df['status'] = df['status'].astype('category')  # 类别优化

# ❌ 需要改进
df = pd.read_excel(file)  # 一次性加载
for index, row in df.iterrows():  # 低效循环
```

## 第五部分：人工核对流程

### 📝 5.1 核对步骤

#### 阶段一：规范审查
```bash
1. 进入规范目录
   cd .claude/specs/feature-name

2. 检查文档完整性
   ls -la *.md

3. 验证需求合理性
   review requirements.md

4. 评审技术设计
   review design.md

5. 确认任务分解
   grep "^- \[" tasks.md | wc -l
```

#### 阶段二：代码审查
```bash
6. 检查代码实现
   git diff --name-only | grep -E "\.(py|js|ts)$"

7. 运行测试套件
   pytest tests/ -v

8. 检查测试覆盖
   pytest --cov=. --cov-report=term-missing

9. 性能测试
   locust -f tests/performance/
```

#### 阶段三：集成验证
```bash
10. API 文档检查
    curl http://localhost:8013/docs

11. 端到端测试
    python tests/e2e/test_workflow.py

12. 日志审查
    tail -f logs/app.log
```

### 🔄 5.2 迭代改进检查

#### A. 反馈收集
- [ ] 用户反馈已记录
- [ ] 性能指标已分析
- [ ] 错误日志已审查
- [ ] 改进建议已评估

#### B. 持续优化
```python
# 性能监控点
@monitor_performance
def process_large_file(file_path):
    start_time = time.time()
    # 处理逻辑
    metrics.record_latency(time.time() - start_time)
```

## 第六部分：核对报告模板

### 📄 6.1 规范核对报告

```markdown
# Feature: [功能名称] 核对报告

## 1. 规范文档检查
- [x] requirements.md 完整且已审批
- [x] design.md 技术方案合理
- [x] tasks.md 任务分解清晰

## 2. 代码实现检查
- [x] 所有任务已完成 (15/15)
- [x] 代码符合规范
- [x] 测试覆盖率: 85%

## 3. 质量指标
- API 响应时间: P95 < 200ms ✅
- 内存使用: < 512MB ✅
- 错误率: < 0.1% ✅

## 4. 问题与风险
- 问题1: [描述] → [解决方案]
- 风险1: [描述] → [缓解措施]

## 5. 核对结论
状态: ✅ 通过 / ⚠️ 需改进 / ❌ 不通过

签字: ___________
日期: 2025-01-28
```

### 🎯 6.2 核对要点总结

#### 关键成功因素
1. **规范先行** - 不写无规范的代码
2. **测试驱动** - 不写无测试的功能
3. **持续验证** - 每个阶段都要验证
4. **文档同步** - 代码与文档保持一致

#### 常见问题检查
- [ ] 需求是否过于模糊？
- [ ] 设计是否过度工程？
- [ ] 任务是否粒度过大？
- [ ] 测试是否覆盖边界？
- [ ] 性能是否满足要求？

## 第七部分：工具与命令

### 🛠️ 7.1 自动化检查命令

```bash
# 完整的核对脚本
cat > check_spec.sh << 'EOF'
#!/bin/bash
FEATURE=$1

echo "=== Checking $FEATURE ==="

# 1. 检查规范文档
echo "Checking specs..."
for file in requirements design tasks; do
  if [ -f ".claude/specs/$FEATURE/$file.md" ]; then
    echo "✅ $file.md exists"
  else
    echo "❌ $file.md missing"
  fi
done

# 2. 检查任务完成度
echo "Checking task completion..."
TOTAL=$(grep -c "^- \[.\]" .claude/specs/$FEATURE/tasks.md)
DONE=$(grep -c "^- \[x\]" .claude/specs/$FEATURE/tasks.md)
echo "Tasks: $DONE/$TOTAL completed"

# 3. 运行测试
echo "Running tests..."
pytest tests/ -v --tb=short

# 4. 检查代码质量
echo "Checking code quality..."
black . --check
mypy .

echo "=== Check Complete ==="
EOF

chmod +x check_spec.sh
./check_spec.sh feature-name
```

### 📚 7.2 参考资源

- **规范模板**: `.claude/templates/`
- **最佳实践**: `.claude/steering/best-practices.md`
- **问题排查**: `.claude/docs/troubleshooting.md`
- **性能基准**: `.claude/benchmarks/`

## 第八部分：快速检查清单

### ✅ 规范阶段检查点

#### Requirements 阶段
```bash
□ 需求文档存在且格式正确
□ 用户故事清晰可理解
□ 验收标准可测试
□ 与产品愿景对齐
□ 优先级已定义
```

#### Design 阶段
```bash
□ 技术架构图完整
□ API 接口已定义
□ 数据模型已设计
□ 性能指标已设定
□ 安全考虑已评估
```

#### Tasks 阶段
```bash
□ 任务分解合理（2-4小时）
□ 每个任务可独立完成
□ 测试用例已规划
□ 依赖关系已明确
□ 完成标准已定义
```

### 🔍 代码实现检查点

#### 编码规范
```bash
□ 遵循 PEP 8 规范
□ 类型注解完整
□ 文档字符串规范
□ 错误处理完善
□ 日志记录充分
```

#### 测试覆盖
```bash
□ 单元测试 > 80%
□ 集成测试通过
□ 端到端测试通过
□ 性能测试达标
□ 安全测试通过
```

#### 文档同步
```bash
□ API 文档更新
□ README 更新
□ CHANGELOG 记录
□ 部署文档完整
□ 操作手册更新
```

### 📊 性能与质量检查点

#### 性能指标
```bash
□ API 响应时间 < 200ms (P95)
□ 内存使用 < 512MB
□ CPU 使用率 < 70%
□ 并发支持 > 100 用户
□ 文件处理 > 10MB/s
```

#### 质量指标
```bash
□ 代码复杂度 < 10
□ 代码重复率 < 5%
□ 技术债务已记录
□ 安全漏洞已修复
□ 依赖版本已更新
```

## 第九部分：常见问题与解决方案

### ❓ FAQ

#### Q1: 规范文档应该多详细？
**A:** 足够让不了解项目的开发者能够理解和实现。关键是平衡详细度和可维护性。

#### Q2: 任务粒度如何把握？
**A:** 每个任务应该：
- 可在半天内完成
- 有明确的输入输出
- 可独立测试验证

#### Q3: 如何处理需求变更？
**A:**
1. 更新 requirements.md
2. 评估对 design.md 的影响
3. 调整 tasks.md 中的任务
4. 保留变更历史记录

#### Q4: 测试覆盖率不达标怎么办？
**A:**
1. 识别未覆盖的代码
2. 补充单元测试
3. 考虑是否有死代码
4. 记录无法测试的原因

### 🔧 故障排查

#### 问题：规范与实现不一致
```bash
# 解决步骤
1. git diff 查看代码变更
2. 对比规范文档
3. 确定是规范过时还是实现偏离
4. 更新文档或修正代码
```

#### 问题：性能不达标
```python
# 性能分析
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# 运行代码
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

## 第十部分：持续改进

### 📈 度量与改进

#### 关键度量指标
1. **规范完成率** = 已完成规范 / 总规范数
2. **任务完成率** = 已完成任务 / 总任务数
3. **测试覆盖率** = 已测试代码 / 总代码量
4. **缺陷密度** = 缺陷数 / 代码行数
5. **技术债务** = 待改进项 × 平均修复时间

#### 改进建议收集
```markdown
## 改进建议模板

### 问题描述
[具体描述遇到的问题]

### 影响范围
[影响的功能/模块]

### 建议方案
[提出的解决方案]

### 预期收益
[实施后的预期效果]

### 实施成本
[时间/资源评估]
```

### 🎯 最佳实践总结

1. **始终从规范开始** - 不要急于编码
2. **小步快跑** - 频繁集成和验证
3. **测试优先** - TDD 不是可选项
4. **文档即代码** - 保持同步更新
5. **持续重构** - 保持代码质量
6. **及时沟通** - 遇到问题立即反馈
7. **数据驱动** - 基于度量做决策

---

## 核对员签名区

```
核对员: ________________
日期: __________________
版本: v2.0
状态: [ ] 通过  [ ] 条件通过  [ ] 不通过

备注:
_________________________________
_________________________________
_________________________________

下次核对日期: ________________
负责人: ______________________
```

## 附录：快速命令参考

```bash
# 规范管理命令
/spec-create feature-name "描述"  # 创建新规范
/spec-list                        # 列出所有规范
/spec-status feature-name         # 查看规范状态
/spec-execute task-id feature     # 执行任务

# 质量检查命令
pytest tests/ -v --cov=.          # 运行测试
black . --check                   # 代码格式检查
mypy .                            # 类型检查
bandit -r .                       # 安全检查

# 性能分析命令
python -m cProfile -o profile.stats app.py
python -m pstats profile.stats
locust -f tests/performance/locustfile.py

# 文档生成命令
python -m mkdocs build            # 生成文档
python -m mkdocs serve            # 预览文档
```

---

**文档版本**: 2.0
**最后更新**: 2025-01-28
**维护者**: Backend Spec Team
**反馈邮箱**: spec-team@example.com

此手册是 Spec-Driven Development 的核心参考，确保每个开发环节都得到严格把控，是项目质量的最终保障。