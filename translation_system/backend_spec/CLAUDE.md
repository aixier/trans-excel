# Claude Code Configuration

## 🎯 Project Overview

Translation System Backend V2 - 企业级 Excel 批量翻译管理系统

这是一个基于 **DataFrame-Centric Architecture** 的高性能翻译后端系统，专注于游戏本地化场景的批量翻译需求。系统采用 pandas DataFrame 作为核心数据结构，提供智能批处理、多LLM支持、实时监控等企业级功能。

## 📚 Important Documents

请先阅读以下核心文档了解项目：
- `ARCHITECTURE.md` - 完整架构设计文档 ⭐ 重要
- `SPEC_DRIVEN_REVIEW_MANUAL.md` - 规范审查手册
- `../backend_v2/` - 实际实现代码库

## 🏗️ System Architecture

### 核心架构特征
- **分层架构**: API层 → 服务层 → 数据层 → 基础设施层
- **DataFrame中心**: 所有数据操作围绕pandas DataFrame
- **服务化设计**: 31个独立服务模块，职责单一
- **LLM抽象层**: 支持OpenAI、通义千问等多种模型
- **批处理优化**: 5个文本合并调用，减少80%API成本

### 数据流设计
```
Excel上传 → 内容分析 → 任务生成 → 批次分配 → LLM翻译 → 结果聚合 → Excel导出
                                        ↓
                                   进度监控 → WebSocket推送
```

## 🚀 Quick Start Commands

### 开发环境启动
```bash
# 启动后端服务
cd ../backend_v2
uvicorn main:app --reload --port 8013

# 访问API文档
open http://localhost:8013/docs
```

### 核心功能测试
```bash
# 上传Excel文件进行分析
curl -X POST "http://localhost:8013/api/analyze/upload" \
  -F "file=@test.xlsx" \
  -F 'game_info={"game_name":"Game1"}'

# 查询任务进度
curl "http://localhost:8013/api/monitor/progress/{session_id}"

# WebSocket连接监控
wscat -c ws://localhost:8013/ws/{session_id}
```

## 🛠 Development Workflow

### 核心模块说明

#### API层模块 (`/api`)
- `analyze_api.py` - Excel文件上传与分析
- `task_api.py` - 任务创建与管理
- `execute_api.py` - 翻译执行控制
- `monitor_api.py` - 进度与性能监控
- `download_api.py` - 结果文件下载
- `websocket_api.py` - 实时通信支持

#### 服务层模块 (`/services`)
- **Excel处理**: `excel_loader.py`, `excel_analyzer.py`, `context_extractor.py`
- **任务执行**: `batch_allocator.py`, `batch_executor.py`, `worker_pool.py`
- **LLM集成**: `llm_factory.py`, `batch_translator.py`, `prompt_template.py`
- **系统支撑**: `performance_monitor.py`, `checkpoint_service.py`, `session_cleaner.py`

#### 数据模型 (`/models`)
- `task_dataframe.py` - 30字段完整任务模型
- `excel_dataframe.py` - Excel数据映射
- `game_info.py` - 游戏上下文信息

### 开发规范

- **DataFrame优先**: 使用向量化操作，避免循环
- **异步处理**: 使用async/await处理IO操作
- **错误处理**: 结构化日志 + HTTPException
- **类型注解**: 所有公共函数必须有type hints
- **测试覆盖**: 单元测试覆盖率 > 80%

## 💻 Development Philosophy

### 架构原则
1. **DataFrame-Centric**: 所有数据操作围绕pandas DataFrame
2. **Service-Oriented**: 服务化拆分，职责单一
3. **Async-First**: 异步优先，提升并发性能
4. **Batch-Optimized**: 批处理优化，降低成本

### 设计模式
- **Factory Pattern**: LLM提供者工厂
- **Strategy Pattern**: 批处理分配策略
- **Singleton Pattern**: 配置管理单例
- **Observer Pattern**: 进度监听推送

## 📁 Project Structure

```
backend_v2/                      # 实际实现目录
├── api/                        # API层 (6个模块)
│   ├── analyze_api.py         # Excel分析
│   ├── task_api.py            # 任务管理
│   ├── execute_api.py         # 执行控制
│   ├── monitor_api.py         # 监控查询
│   ├── download_api.py        # 文件下载
│   └── websocket_api.py       # 实时通信
├── services/                   # 服务层 (31个服务)
│   ├── executor/              # 执行服务群
│   │   ├── batch_executor.py
│   │   ├── worker_pool.py
│   │   └── progress_tracker.py
│   ├── llm/                   # LLM服务群
│   │   ├── llm_factory.py
│   │   ├── batch_translator.py
│   │   └── openai_provider.py
│   ├── persistence/           # 持久化服务
│   ├── monitor/               # 监控服务
│   └── export/                # 导出服务
├── models/                     # 数据模型层
│   ├── task_dataframe.py      # 核心任务模型
│   ├── excel_dataframe.py     # Excel映射
│   └── game_info.py           # 游戏信息
├── database/                   # 数据库层
├── utils/                      # 工具函数
└── tests/                      # 测试套件
```

## Technology Stack

### Core Dependencies
```python
# Web Framework
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6

# Data Processing
pandas==2.1.3
openpyxl==3.1.2
numpy==1.24.3

# Database
sqlalchemy==2.0.23
mysqlclient==2.2.0
alembic==1.12.1

# Cache & Queue
redis==5.0.1
celery==5.3.4

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.1

# Monitoring
loguru==0.7.2
prometheus-client==0.19.0
```

### When to Use Each Dependency

- **FastAPI**: All REST API endpoints
- **pandas**: DataFrame operations for task management
- **openpyxl**: Excel file reading/writing
- **SQLAlchemy**: Database ORM operations
- **Redis**: Session caching and task queues
- **pytest**: All testing scenarios
- **loguru**: Structured logging

## Common Tasks

### 添加新的 API 端点
1. 查看 `spec.md` 中的 API 规范
2. 在对应的 `api/*_api.py` 文件中添加端点
3. 编写测试用例 `tests/test_*_api.py`
4. 更新 API 文档

### 优化 DataFrame 操作
1. 使用 vectorized operations 而非循环
2. 利用 `.loc[]` 和 `.iloc[]` 进行高效索引
3. 使用 `chunk` 处理大文件
4. 实现内存优化的数据类型

### 实现新功能
1. 先运行 `/specify` 明确需求
2. 运行 `/plan` 制定技术方案
3. 运行 `/tasks` 生成任务列表
4. 按 TDD 方式逐个实现任务

## Error Handling

### 标准错误处理模式
```python
from fastapi import HTTPException
from loguru import logger

try:
    # 业务逻辑
    result = process_data()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.exception("Unexpected error")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### 日志级别使用
- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息和业务流程
- **WARNING**: 警告但不影响功能
- **ERROR**: 错误但可恢复
- **CRITICAL**: 严重错误需要立即处理

## Testing Guidelines

### 测试文件命名
- 单元测试: `test_<module>.py`
- 集成测试: `test_integration_<feature>.py`
- 端到端测试: `test_e2e_<scenario>.py`

### 测试结构
```python
class TestAnalyzeAPI:
    """测试分析 API"""

    def test_upload_valid_file(self, client):
        """测试上传有效文件"""
        # Given: 准备测试数据
        # When: 执行操作
        # Then: 验证结果

    @pytest.mark.parametrize("file_size", [1_000_000, 5_000_000])
    def test_large_file_handling(self, client, file_size):
        """测试大文件处理"""
        pass
```

## Performance Optimization

### DataFrame 优化策略
```python
# 1. 类型优化 - 减少50%内存
df['status'] = df['status'].astype('category')
df['priority'] = df['priority'].astype('int8')

# 2. 向量化操作 - 提升100倍性能
df.loc[mask, 'result'] = translations  # 批量更新

# 3. 分块处理 - 避免内存溢出
for chunk in pd.read_excel(file, chunksize=10000):
    process_chunk(chunk)
```

### LLM调用优化
```python
# 批量合并 - 减少80%调用次数
batch = combine_texts(texts[:5])  # 5个文本合并
response = llm.translate_batch(batch)
results = split_response(response)
```

### 并发控制
- 最大10个LLM并发请求
- WebSocket异步推送
- 数据库连接池复用

## Debugging Tips

### 常见问题排查
1. **内存泄漏**: 使用 `memory_profiler` 分析
2. **慢查询**: 检查数据库索引和查询计划
3. **并发问题**: 使用 `asyncio.Lock` 保护共享资源
4. **文件处理**: 确保正确关闭文件句柄

### 调试工具
- `ipdb`: 交互式调试
- `line_profiler`: 行级性能分析
- `memory_profiler`: 内存使用分析
- `py-spy`: 生产环境性能分析

## Deployment Checklist

### 部署前检查
- [ ] 所有测试通过
- [ ] 代码覆盖率 > 80%
- [ ] 无安全漏洞（运行 `bandit`）
- [ ] 性能测试达标
- [ ] 文档更新完成
- [ ] 数据库迁移脚本准备

### 环境变量配置
```bash
# .env.production
API_HOST=0.0.0.0
API_PORT=8013
DB_URL=mysql://user:pass@host/db
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
MAX_WORKERS=4
```

## Continuous Improvement

### 代码审查重点
1. 是否符合 spec.md 规范
2. 测试覆盖是否充分
3. 错误处理是否完善
4. 性能是否达标
5. 文档是否更新

### 性能监控指标
- API 响应时间 P50/P95/P99
- 数据库查询时间
- 内存使用趋势
- 错误率和错误类型分布
- 任务处理吞吐量

## Quick Commands

### 开发常用命令
```bash
# 启动服务
cd ../backend_v2
uvicorn main:app --reload --port 8013

# 运行测试
pytest tests/ -v --cov=.

# 代码质量检查
black . --check
flake8 .
mypy .

# 查看API文档
open http://localhost:8013/docs
```

### 调试命令
```bash
# 查看服务日志
tail -f logs/app.log

# 监控性能
python -m cProfile -o profile.stats main.py

# 内存分析
python -m memory_profiler main.py
```

### 数据库操作
```bash
# 连接MySQL
mysql -h localhost -P 3306 -u root -p translation_db

# 查看任务状态
SELECT status, COUNT(*) FROM tasks GROUP BY status;
```

## 🎯 Key Features

### 已实现功能
- ✅ Excel文件批量上传与解析
- ✅ 智能文本提取与上下文分析
- ✅ 30字段完整任务管理系统
- ✅ 多LLM模型支持（OpenAI、通义千问）
- ✅ 批量翻译优化（5文本合并）
- ✅ WebSocket实时进度推送
- ✅ 断点续传与故障恢复
- ✅ 性能监控与日志持久化

### 核心性能指标
- 单文件处理: 10MB Excel < 5秒
- 批量翻译: 1000条文本 < 2分钟
- 并发支持: 100个会话同时处理
- 内存优化: DataFrame减少50%内存占用
- API成本: 批处理减少80%调用次数

## 📋 TaskDataFrame Schema

```python
# 30个字段的完整任务模型
task_id: str              # UUID任务标识
batch_id: str             # 批次分组
source_text: str          # 源文本内容
target_lang: category     # 目标语言(PT/TH/VN)
status: category          # 任务状态
priority: int8            # 优先级(1-10)
result: str               # 翻译结果
confidence: float32       # 置信度(0-1)
duration_ms: int32        # 处理时长
token_count: int32        # Token使用量
llm_model: str            # 使用的模型
# ... 更多字段见 models/task_dataframe.py
```

## Remember

1. **DataFrame是核心** - 所有数据操作围绕DataFrame
2. **批处理优先** - 合并请求降低成本
3. **异步处理** - 提升系统吞吐量
4. **服务解耦** - 保持模块独立性
5. **监控先行** - 实时了解系统状态