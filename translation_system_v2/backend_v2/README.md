# Backend V2 - 翻译系统后端（模块化架构）

> **🚀 新模块化架构：** 基于5大核心模块的现代化翻译系统，100%测试覆盖，89%代码覆盖率

## 📊 项目状态

| 指标 | 数值 |
|-----|------|
| **架构** | 模块化 (2024-10-16) |
| **测试数量** | 304个 |
| **测试通过率** | 100% |
| **代码覆盖率** | 89% |
| **代码行数** | 6,752行 |
| **API版本** | V2 (Pipeline API) |

详见: [📊 最终测试报告](FINAL_TEST_REPORT.md)

---

## 🏗️ 项目结构

```
backend_v2/
├── api/                          # API路由层
│   ├── pipeline_api.py          # ✨ V2 Pipeline API (新)
│   └── [v1 apis...]             # V1 兼容API
│
├── services/                     # 🎯 核心服务层（新架构）
│   ├── data_state/              # 数据状态管理模块
│   ├── processors/              # 数据处理器模块
│   ├── splitter/                # 任务拆分器模块
│   ├── transformer/             # 数据转换器模块
│   ├── orchestrator/            # 流程编排器模块
│   ├── excel_loader.py          # Excel加载器
│   └── llm/                     # LLM集成服务
│
├── tests/                        # 测试文件（304个测试）
│   ├── test_data_state.py       # DataState模块测试
│   ├── test_processors.py       # Processor模块测试
│   ├── test_splitter.py         # Splitter模块测试
│   ├── test_transformer.py      # Transformer模块测试
│   ├── test_orchestrator.py     # Orchestrator模块测试
│   └── test_end_to_end_integration.py  # 端到端集成测试
│
├── .claude/                      # 架构文档
│   ├── PIPELINE_ARCHITECTURE.md # Pipeline架构说明
│   ├── SIMPLIFIED_ARCHITECTURE.md # 简化架构说明
│   └── specs/                   # 模块开发规范
│
├── config/                       # 配置管理
├── models/                       # 数据模型
├── utils/                        # 工具类
└── archive/                      # 旧代码归档
```

---

## 📚 架构文档

### 核心架构
- [🏗️ **Pipeline 架构**](.claude/PIPELINE_ARCHITECTURE.md) - 流程编排架构设计
- [📖 **简化架构说明**](.claude/SIMPLIFIED_ARCHITECTURE.md) - 架构快速入门
- [📋 **模块开发规范**](.claude/specs/) - 各模块详细规范

### 模块说明
- [📦 **DataState**](services/data_state/README.md) - 数据状态管理
- [⚙️ **Processor**](services/processors/) - 数据处理器
- [✂️ **Splitter**](services/splitter/README.md) - 任务拆分器
- [🔄 **Transformer**](services/transformer/) - 数据转换器
- [🎭 **Orchestrator**](services/orchestrator/README.md) - 流程编排器

### 测试报告
- [📊 **最终测试报告**](FINAL_TEST_REPORT.md) - 完整的测试覆盖率和结果

---

## 🚀 快速开始

### 1. 环境准备
```bash
cd backend_v2
pip install -r requirements.txt
```

### 2. 启动服务
```bash
python3 main.py
# 服务将在 http://localhost:8013 启动
```

### 3. 测试 API
打开浏览器访问:
```
/mnt/d/work/trans_excel/translation_system_v2/frontend_v2/test_pages/v2_pipeline_test.html
```

或使用 Python 测试脚本:
```bash
python3 test_pipeline_api.py
```

---

## 🎯 核心特性

### ✅ V2 新架构特性
- 🏗️ **模块化架构** - 5个独立模块，单一职责
- 🔄 **数据不可变性** - 每次转换返回新状态
- 🎭 **Pipeline 编排** - 灵活的多阶段流程编排
- ✅ **CAPS Bug 修复** - 正确处理CAPS大写（不再发送给LLM）
- 🧪 **高测试覆盖** - 304个测试，89%覆盖率
- 🔌 **依赖管理** - 阶段间依赖自动解析

### 🆚 V1 vs V2 对比

| 特性 | V1 API | V2 Pipeline API |
|------|--------|-----------------|
| **架构** | 整体式 | 模块化 |
| **流程** | 4步分离API | 一站式Pipeline |
| **CAPS处理** | ❌ Bug (会翻译) | ✅ 修复 (只转大写) |
| **测试覆盖** | 未知 | 89% |
| **可扩展性** | 低 | 高 |
| **状态管理** | 可变 | 不可变 |

---

## 🔌 API 端点

### V2 Pipeline API (新)
```
POST   /api/v2/pipeline/translate        # 执行翻译Pipeline
GET    /api/v2/pipeline/health           # 健康检查
GET    /api/v2/pipeline/status/{id}      # 查询状态 (未来异步)
POST   /api/v2/pipeline/cancel/{id}      # 取消执行 (未来异步)
```

### V1 兼容API (保留)
```
POST   /api/analyze/upload               # 上传分析
POST   /api/tasks/split                  # 任务拆分
GET    /api/tasks/export/{id}            # 导出任务
POST   /api/execute/start                # 开始执行
GET    /api/monitor/status/{id}          # 监控状态
GET    /api/download/{id}                # 下载结果
```

---

## 🧪 运行测试

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行特定模块测试
```bash
pytest tests/test_data_state.py -v
pytest tests/test_processors.py -v
pytest tests/test_splitter.py -v
pytest tests/test_transformer.py -v
pytest tests/test_orchestrator.py -v
```

### 运行端到端集成测试
```bash
pytest tests/test_end_to_end_integration.py -v
```

### 查看测试覆盖率
```bash
pytest --cov=services --cov-report=html
```

---

## 🎓 开发指南

### 架构原则
1. **单一职责** - 每个模块只做一件事
2. **数据不可变** - 每次转换返回新状态
3. **依赖注入** - 通过构造函数注入依赖
4. **接口隔离** - 清晰的模块边界
5. **测试驱动** - 先写测试，再写实现

### 添加新的处理器
```python
# 1. 继承 Processor 基类
from services.processors import Processor

class MyProcessor(Processor):
    def process(self, task: pd.Series, context: Optional[Dict] = None) -> str:
        # 实现处理逻辑
        return result

# 2. 添加单元测试
# tests/test_processors.py

# 3. 在 Pipeline 中使用
orchestrator.add_stage(PipelineStage(
    stage_id='my_stage',
    splitter_rules=[MyRule()],
    transformer=BaseTransformer(MyProcessor())
))
```

### 添加新的拆分规则
```python
# 1. 继承 SplitRule 基类
from services.splitter import SplitRule

class MyRule(SplitRule):
    def should_process(self, sheet: str, row: int, col: str, data_state: DataState) -> bool:
        # 实现判断逻辑
        return True

# 2. 添加单元测试
# tests/test_splitter.py

# 3. 在 Pipeline 中使用
orchestrator.add_stage(PipelineStage(
    stage_id='my_stage',
    splitter_rules=[MyRule()],
    transformer=my_transformer
))
```

---

## 📖 常见问题

### Q: V1 和 V2 API 有什么区别？
**A:** V2 使用新的模块化架构，一次 API 调用完成所有处理（翻译+CAPS等），而 V1 需要多次 API 调用。V2 还修复了 CAPS 翻译 Bug。

### Q: 旧文档去哪了？
**A:** 所有旧的 V1 文档已移至 `archive/old_docs/` 目录。新架构文档在 `.claude/` 目录。

### Q: 如何验证 CAPS Bug 修复？
**A:** 使用 V2 Pipeline API 翻译包含 CAPS Sheet 的文件，检查 CAPS 内容是否转为大写而非被翻译。

### Q: 前端需要修改吗？
**A:** 不需要。V1 API 完全保留，前端可继续使用。V2 API 是额外提供的新端点。

---

## 🔗 相关链接

- [整体项目文档](../README.md) - 项目总体说明
- [Frontend V2](../frontend_v2/) - 前端实现
- [测试页面](../frontend_v2/test_pages/v2_pipeline_test.html) - V2 API 测试页面

---

## 📝 旧文档归档

所有 V1 架构的旧文档已移至 [`archive/`](archive/) 目录，包括：
- 86+ 旧脚本文件
- 25+ 旧文档文件
- V1 架构设计文档

详见: [Archive README](archive/README.md)

---

> **✨ 架构版本**: V2 Modular
> **📅 更新日期**: 2024-10-16
> **🏆 测试状态**: 304个测试全部通过
