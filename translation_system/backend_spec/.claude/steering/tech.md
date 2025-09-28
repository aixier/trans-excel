# 技术规范文档

## Translation System Backend V2

### 技术架构概述

系统采用分层架构设计，以DataFrame为数据处理核心，通过服务化拆分实现高内聚低耦合，使用异步处理提升系统吞吐量。

```
┌─────────────────────────────────────┐
│          API层 (FastAPI)            │
├─────────────────────────────────────┤
│         服务层 (Services)           │
├─────────────────────────────────────┤
│      数据模型层 (DataFrame)         │
├─────────────────────────────────────┤
│      基础设施层 (Database)          │
└─────────────────────────────────────┘
```

### 核心技术栈

#### Web框架
- **FastAPI 0.104.1**
  - 异步请求处理
  - 自动API文档生成
  - 数据验证（Pydantic）
  - WebSocket支持

#### 数据处理
- **pandas 2.1.3**
  - DataFrame核心数据结构
  - 向量化批量操作
  - 内存优化技术
  - Excel文件处理

- **openpyxl 3.1.2**
  - Excel读写操作
  - 样式保留
  - 多Sheet处理

#### 异步处理
- **asyncio**
  - 协程并发控制
  - 异步IO操作
  - 事件循环管理

- **httpx**
  - 异步HTTP客户端
  - 连接池管理
  - 超时控制

#### 数据存储
- **MySQL 8.0**
  - 任务数据持久化
  - 事务支持
  - 索引优化

- **Redis 5.0**
  - 会话缓存
  - 任务队列
  - 分布式锁

### 设计模式与原则

#### 1. DataFrame-Centric Pattern
```python
# 所有数据操作围绕DataFrame
class TaskDataFrameManager:
    def __init__(self):
        self.df = pd.DataFrame(columns=TASK_DF_COLUMNS)

    def batch_update(self, updates: List[Dict]):
        # 向量化批量更新
        mask = self.df['task_id'].isin([u['task_id'] for u in updates])
        for col, values in updates_dict.items():
            self.df.loc[mask, col] = values
```

#### 2. Factory Pattern
```python
# LLM提供者工厂
class LLMFactory:
    @staticmethod
    def create_provider(config: LLMConfig) -> BaseLLMProvider:
        providers = {
            'openai': OpenAIProvider,
            'qwen': QwenProvider,
            'custom': CustomProvider
        }
        return providers[config.provider](config)
```

#### 3. Strategy Pattern
```python
# 批处理策略
class BatchAllocationStrategy(ABC):
    @abstractmethod
    def allocate(self, tasks: List) -> List[Batch]:
        pass

class CharCountStrategy(BatchAllocationStrategy):
    def allocate(self, tasks: List) -> List[Batch]:
        # 基于字符数的均衡分配
        return self._balance_by_chars(tasks)
```

#### 4. Singleton Pattern
```python
# 配置管理单例
class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### 编码规范

#### Python规范
```python
# PEP 8 编码规范
- 缩进：4个空格
- 行长：最大100字符
- 命名：snake_case for functions, PascalCase for classes
- 导入：标准库、第三方库、本地模块分组

# 类型注解
def process_task(
    task_id: str,
    options: Dict[str, Any]
) -> TaskResult:
    """处理单个翻译任务。

    Args:
        task_id: 任务唯一标识
        options: 处理选项

    Returns:
        TaskResult: 任务处理结果
    """
    pass

# 文档字符串（Google Style）
"""模块描述。

详细说明模块功能和使用方法。

Example:
    >>> from module import function
    >>> result = function(param)
"""
```

#### 异步编程规范
```python
# 异步函数定义
async def fetch_translation(
    text: str,
    target_lang: str
) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        return response.json()['result']

# 并发控制
async def process_batch(tasks: List[Task]):
    # 限制并发数
    semaphore = asyncio.Semaphore(10)

    async def process_with_limit(task):
        async with semaphore:
            return await process_task(task)

    results = await asyncio.gather(
        *[process_with_limit(task) for task in tasks]
    )
    return results
```

#### DataFrame操作规范
```python
# 使用向量化操作
# ✅ 好的做法
df.loc[df['status'] == 'pending', 'status'] = 'processing'

# ❌ 避免循环
for index, row in df.iterrows():
    if row['status'] == 'pending':
        df.loc[index, 'status'] = 'processing'

# 内存优化
df['status'] = df['status'].astype('category')
df['priority'] = df['priority'].astype('int8')
df['created_at'] = pd.to_datetime(df['created_at'])
```

### 性能优化策略

#### 1. DataFrame优化
- 类型优化减少内存50%
- 向量化操作提升100倍性能
- 分块处理大文件
- 使用.loc[]高效索引

#### 2. LLM调用优化
- 5个文本合并调用
- Token数量平衡
- 请求缓存机制
- 并发数量控制

#### 3. 异步处理优化
- 协程池管理
- 非阻塞IO
- 事件驱动架构
- WebSocket推送

#### 4. 数据库优化
- 连接池复用
- 批量插入更新
- 索引优化
- 查询缓存

### 错误处理规范

```python
from fastapi import HTTPException
from loguru import logger
from typing import Optional

class BusinessException(Exception):
    """业务异常基类。"""
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(message)

# API层错误处理
@router.post("/api/translate")
async def translate(request: TranslateRequest):
    try:
        result = await translation_service.translate(request)
        return {"code": 200, "data": result}
    except BusinessException as e:
        logger.warning(f"Business error: {e.message}")
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.exception("Unexpected error")
        raise HTTPException(status_code=500, detail="Internal server error")

# 服务层错误处理
async def translate_with_retry(text: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await llm_provider.translate(text)
        except TemporaryError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # 指数退避
            await asyncio.sleep(wait_time)
```

### 日志规范

```python
from loguru import logger

# 日志配置
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    format="{time} {level} {message}"
)

# 日志级别使用
logger.debug(f"Processing task: {task_id}")  # 调试信息
logger.info(f"Task completed: {task_id}")    # 一般信息
logger.warning(f"Retry task: {task_id}")     # 警告信息
logger.error(f"Task failed: {task_id}")      # 错误信息
logger.critical("System shutdown")           # 严重错误

# 结构化日志
logger.info(
    "Task processed",
    task_id=task_id,
    duration_ms=duration,
    status="completed"
)
```

### 测试规范

#### 单元测试
```python
import pytest
from unittest.mock import Mock, patch

class TestTaskManager:
    """测试任务管理器。"""

    @pytest.fixture
    def task_manager(self):
        """创建测试用任务管理器。"""
        return TaskDataFrameManager()

    def test_create_task(self, task_manager):
        """测试创建任务。"""
        # Given
        task_data = {"source_text": "Hello", "target_lang": "zh"}

        # When
        task_id = task_manager.create_task(task_data)

        # Then
        assert task_id is not None
        task = task_manager.get_task(task_id)
        assert task['source_text'] == "Hello"

    @patch('services.llm.openai_provider.httpx.AsyncClient')
    async def test_translate_with_mock(self, mock_client):
        """测试模拟LLM调用。"""
        # Given
        mock_client.post.return_value.json.return_value = {
            "result": "你好"
        }

        # When
        result = await translate_text("Hello", "zh")

        # Then
        assert result == "你好"
```

#### 集成测试
```python
@pytest.mark.integration
class TestAPIIntegration:
    """API集成测试。"""

    async def test_upload_and_process(self, client):
        """测试完整上传处理流程。"""
        # Upload file
        with open("test.xlsx", "rb") as f:
            response = await client.post(
                "/api/analyze/upload",
                files={"file": f}
            )
        assert response.status_code == 200
        session_id = response.json()["session_id"]

        # Start processing
        response = await client.post(
            f"/api/execute/start",
            json={"session_id": session_id}
        )
        assert response.status_code == 200
```

### 安全规范

#### 1. 认证授权
```python
from fastapi import Depends, Security
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Security(security)):
    token = credentials.credentials
    # 验证token逻辑
    if not is_valid_token(token):
        raise HTTPException(status_code=401)
    return token

@router.get("/api/protected")
async def protected_route(token = Depends(verify_token)):
    return {"message": "Protected resource"}
```

#### 2. 输入验证
```python
from pydantic import BaseModel, validator

class FileUploadRequest(BaseModel):
    file_size: int
    file_name: str

    @validator('file_size')
    def validate_size(cls, v):
        if v > 100 * 1024 * 1024:  # 100MB
            raise ValueError("File too large")
        return v

    @validator('file_name')
    def validate_name(cls, v):
        if not v.endswith(('.xlsx', '.xls')):
            raise ValueError("Invalid file type")
        return v
```

#### 3. SQL注入防护
```python
# 使用参数化查询
def get_task_by_id(task_id: str):
    query = "SELECT * FROM tasks WHERE task_id = %s"
    return db.execute(query, (task_id,))

# 避免字符串拼接
# ❌ 不安全
query = f"SELECT * FROM tasks WHERE task_id = '{task_id}'"
```

### 部署规范

#### Docker配置
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 运行服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8013"]
```

#### 环境变量
```bash
# .env.production
API_HOST=0.0.0.0
API_PORT=8013
DB_URL=mysql://user:pass@localhost/translation_db
REDIS_URL=redis://localhost:6379/0
LLM_API_KEY=${LLM_API_KEY}
LOG_LEVEL=INFO
MAX_WORKERS=4
```

### 监控指标

#### 业务指标
- 任务处理速度
- 翻译成功率
- API调用成本
- 用户满意度

#### 技术指标
- API响应时间
- 系统吞吐量
- 错误率
- 资源使用率

#### 告警规则
- 错误率 > 1%
- 响应时间 > 1秒
- CPU使用率 > 80%
- 内存使用率 > 90%

---
*文档版本*: 2.0.0
*更新日期*: 2025-01-29
*技术负责人*: Backend Team