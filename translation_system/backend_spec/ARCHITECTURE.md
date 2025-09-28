# Translation System Backend V2 架构设计文档

## 📋 目录

1. [系统概述](#系统概述)
2. [架构设计](#架构设计)
3. [核心模块](#核心模块)
4. [数据流设计](#数据流设计)
5. [技术栈](#技术栈)
6. [设计模式](#设计模式)
7. [性能优化](#性能优化)
8. [部署架构](#部署架构)

## 系统概述

### 项目定位
Translation System Backend V2 是一个企业级的Excel批量翻译管理系统后端，专注于游戏本地化翻译场景。系统采用DataFrame为中心的数据处理架构，提供高性能的批量翻译能力。

### 核心价值
- **批量处理优化**: 支持大规模Excel文件的并发翻译
- **智能上下文管理**: 游戏场景感知的翻译质量保证
- **多LLM支持**: 灵活的AI模型切换和成本优化
- **实时监控**: WebSocket推送的进度跟踪
- **断点续传**: 任务级别的故障恢复机制

## 架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      客户端应用层                              │
│                   (Web/Desktop/Mobile)                       │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API网关层 (FastAPI)                      │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ Analyze  │   Task   │ Execute  │ Monitor  │ Download │  │
│  │   API    │   API    │   API    │   API    │   API    │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        业务服务层                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   Excel处理服务群                                       │  │
│  │   - ExcelLoader: 文件加载与解析                        │  │
│  │   - ExcelAnalyzer: 内容分析与统计                      │  │
│  │   - ContextExtractor: 上下文提取                       │  │
│  │   - LanguageDetector: 语言识别                         │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   任务执行服务群                                        │  │
│  │   - BatchAllocator: 批次分配                           │  │
│  │   - BatchExecutor: 批量执行引擎                        │  │
│  │   - WorkerPool: 并发工作池                             │  │
│  │   - ProgressTracker: 进度跟踪                          │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   LLM集成服务群                                         │  │
│  │   - LLMFactory: 模型工厂                               │  │
│  │   - BatchTranslator: 批量翻译优化器                    │  │
│  │   - PromptTemplate: 提示词管理                         │  │
│  │   - CostCalculator: 成本计算                           │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   支撑服务群                                            │  │
│  │   - PerformanceMonitor: 性能监控                        │  │
│  │   - CheckpointService: 检查点管理                      │  │
│  │   - SessionCleaner: 会话清理                           │  │
│  │   - LogPersister: 日志持久化                           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据模型层 (DataFrame)                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   TaskDataFrame (30字段完整任务模型)                    │  │
│  │   - 任务标识: task_id, batch_id, group_id             │  │
│  │   - 文本数据: source_text, result, context            │  │
│  │   - 位置信息: excel_id, sheet, row, col               │  │
│  │   - 状态管理: status, priority, retry_count           │  │
│  │   - 性能指标: duration_ms, token_count, cost          │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   ExcelDataFrame (Excel数据映射)                        │  │
│  │   GameInfo (游戏上下文信息)                             │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      基础设施层                               │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │  MySQL   │  Redis   │   File   │ Session  │  Config  │  │
│  │    DB    │  Cache   │  System  │ Manager  │ Manager  │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 分层职责

#### 1. API网关层
- **职责**: 请求路由、参数验证、响应格式化
- **技术**: FastAPI、Pydantic、CORS中间件
- **特点**: 异步处理、自动文档生成、WebSocket支持

#### 2. 业务服务层
- **职责**: 核心业务逻辑实现
- **原则**: 单一职责、服务解耦、可组合
- **通信**: 内部同步调用、异步任务队列

#### 3. 数据模型层
- **职责**: 数据结构定义、类型转换、验证规则
- **核心**: pandas DataFrame为中心
- **优化**: 类别类型、内存映射、向量化操作

#### 4. 基础设施层
- **职责**: 数据持久化、缓存、配置管理
- **组件**: 数据库连接池、Redis客户端、文件系统

## 核心模块

### API模块详解

#### 1. analyze_api.py - Excel分析接口
```python
功能：
- 文件上传与验证
- Excel内容解析
- 翻译需求分析
- 会话创建管理

关键接口：
POST /api/analyze/upload
- 输入: Excel文件 + 游戏信息
- 输出: 分析结果 + session_id
```

#### 2. task_api.py - 任务管理接口
```python
功能：
- 任务创建与分配
- 批次管理
- 优先级调度
- 任务状态查询

关键接口：
POST /api/tasks/create - 创建任务
GET  /api/tasks/{id} - 查询任务
PUT  /api/tasks/{id}/priority - 调整优先级
```

#### 3. execute_api.py - 执行控制接口
```python
功能：
- 翻译执行触发
- 批量处理控制
- 暂停/恢复/取消
- 重试机制

关键接口：
POST /api/execute/start - 开始执行
POST /api/execute/pause - 暂停执行
POST /api/execute/resume - 恢复执行
```

#### 4. monitor_api.py - 监控接口
```python
功能：
- 实时进度查询
- 性能指标监控
- 错误日志查看
- 资源使用统计

关键接口：
GET /api/monitor/progress - 进度查询
GET /api/monitor/performance - 性能指标
GET /api/monitor/logs - 日志查询
```

#### 5. websocket_api.py - 实时通信
```python
功能：
- 进度推送
- 状态变更通知
- 错误告警
- 双向通信

WebSocket端点：
WS /ws/{session_id}
```

### 服务模块详解

#### Excel处理服务群

##### ExcelLoader
- **功能**: 加载Excel文件到DataFrame
- **特性**:
  - 支持xlsx/xls格式
  - 多Sheet处理
  - 样式保留
  - 大文件分块加载
  - 编码自动检测

##### ExcelAnalyzer
- **功能**: 分析Excel内容特征
- **输出**:
  - 文本单元格统计
  - 语言分布
  - Sheet结构
  - 预估token数
  - 成本估算

##### ContextExtractor
- **功能**: 提取翻译上下文
- **策略**:
  - 相邻单元格关联
  - 列标题识别
  - Sheet名称语义
  - 游戏术语识别

#### 任务执行服务群

##### BatchAllocator
- **功能**: 智能批次分配
- **算法**:
  - 基于字符数的均衡分配
  - 优先级队列
  - 语言分组
  - 上下文聚合

##### BatchExecutor
- **功能**: 批量执行引擎
- **特性**:
  - 并发控制
  - 错误隔离
  - 进度跟踪
  - 断点续传

##### WorkerPool
- **功能**: 工作线程池管理
- **配置**:
  - 动态扩缩容
  - 负载均衡
  - 超时控制
  - 资源限制

#### LLM集成服务群

##### LLMFactory
- **功能**: LLM提供者工厂
- **支持**:
  - OpenAI GPT系列
  - 通义千问
  - 自定义模型
  - 动态切换

##### BatchTranslator
- **功能**: 批量翻译优化
- **优化策略**:
  - 5个文本合并调用
  - Token数量平衡
  - 上下文复用
  - 缓存机制

##### PromptTemplate
- **功能**: 提示词模板管理
- **模板类型**:
  - 游戏翻译专用
  - 术语表支持
  - 风格指导
  - 多语言适配

## 数据流设计

### 主要数据流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Excel   │────▶│  文件    │────▶│  内容    │────▶│  任务    │
│  上传    │     │  解析    │     │  分析    │     │  生成    │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                          │
                                                          ▼
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  文件    │◀────│  Excel   │◀────│  结果    │◀────│  批次    │
│  下载    │     │  生成    │     │  聚合    │     │  分配    │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                         ▲               │
                                         │               ▼
                                   ┌──────────┐     ┌──────────┐
                                   │   LLM    │◀────│   LLM    │
                                   │  结果    │     │  翻译    │
                                   └──────────┘     └────┬─────┘
                                                          │
                 ┌──────────┐     ┌──────────┐           │
                 │WebSocket │◀────│  进度    │◀──────────┤
                 │  推送    │     │  监控    │           │
                 └──────────┘     └──────────┘           │
                                                          │
                 ┌──────────┐     ┌──────────┐           │
                 │  重试    │────▶│  错误    │◀──────────┘
                 │  机制    │     │  处理    │
                 └──────────┘     └──────────┘
```

### DataFrame数据结构

#### TaskDataFrame核心字段
```python
{
    # 标识字段
    'task_id': str,          # UUID任务标识
    'batch_id': str,         # 批次标识
    'group_id': str,         # 业务分组

    # 文本字段
    'source_text': str,      # 源文本
    'source_context': str,   # 上下文
    'game_context': str,     # 游戏背景
    'result': str,           # 翻译结果

    # 语言字段
    'source_lang': category, # 源语言(CH/EN)
    'target_lang': category, # 目标语言(PT/TH/VN)

    # 位置字段
    'excel_id': str,         # Excel标识
    'sheet_name': str,       # Sheet名称
    'row_idx': int32,        # 行索引
    'col_idx': int32,        # 列索引
    'cell_ref': str,         # 单元格引用

    # 状态字段
    'status': category,      # 任务状态
    'priority': int8,        # 优先级(1-10)
    'retry_count': int8,     # 重试次数
    'is_final': bool,        # 最终版本

    # 性能字段
    'char_count': int32,     # 字符数
    'token_count': int32,    # Token数
    'duration_ms': int32,    # 处理时长
    'cost': float32,         # 成本
    'confidence': float32,   # 置信度

    # 时间字段
    'created_at': datetime,  # 创建时间
    'updated_at': datetime,  # 更新时间
    'start_time': datetime,  # 开始时间
    'end_time': datetime,    # 结束时间

    # 元数据
    'llm_model': str,        # 使用模型
    'error_message': str,    # 错误信息
    'reviewer_notes': str    # 审核备注
}
```

### 状态机设计

```
pending → processing → completed
   ↓         ↓           ↓
   └──→ cancelled ←── failed
           ↑             ↓
           └─────────────┘
              (retry)
```

## 技术栈

### 核心框架
- **Web框架**: FastAPI 0.104.1
- **异步支持**: asyncio + uvicorn
- **数据处理**: pandas 2.1.3
- **Excel处理**: openpyxl 3.1.2

### 数据存储
- **主数据库**: MySQL 8.0
- **缓存层**: Redis 5.0
- **文件存储**: 本地文件系统

### AI集成
- **OpenAI**: GPT-4/GPT-3.5
- **阿里云**: 通义千问
- **HTTP客户端**: httpx

### 监控日志
- **日志框架**: loguru
- **性能监控**: 自定义metrics
- **错误追踪**: 结构化日志

## 设计模式

### 1. DataFrame-Centric Pattern
```python
# 所有数据操作围绕DataFrame
class TaskDataFrameManager:
    def __init__(self):
        self.df = pd.DataFrame()

    def batch_update(self, updates: List[Dict]):
        # 向量化批量更新
        self.df.loc[mask, columns] = values
```

### 2. Factory Pattern
```python
# LLM提供者工厂
class LLMFactory:
    @staticmethod
    def create_provider(config: LLMConfig) -> BaseLLMProvider:
        if config.provider == "openai":
            return OpenAIProvider(config)
        elif config.provider == "qwen":
            return QwenProvider(config)
```

### 3. Strategy Pattern
```python
# 批处理策略
class BatchStrategy(ABC):
    @abstractmethod
    def allocate(self, tasks: List) -> List[Batch]:
        pass

class CharCountStrategy(BatchStrategy):
    def allocate(self, tasks: List) -> List[Batch]:
        # 基于字符数的分配策略
```

### 4. Singleton Pattern
```python
# 配置管理单例
class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### 5. Observer Pattern
```python
# 进度监听器
class ProgressObserver:
    def update(self, progress: float):
        # WebSocket推送进度
        await websocket.send_json({"progress": progress})
```

## 性能优化

### 1. DataFrame优化
- **类型优化**: 使用category减少内存50%
- **批量操作**: 向量化操作提升100倍性能
- **分块处理**: 10000行分块避免内存溢出

### 2. LLM调用优化
- **批量合并**: 5个请求合并减少80%调用
- **并发控制**: 最多10个并发避免限流
- **缓存策略**: 相同文本缓存避免重复

### 3. 异步处理
- **异步IO**: FastAPI全异步提升吞吐
- **协程池**: 控制并发数量
- **非阻塞**: WebSocket异步推送

### 4. 资源管理
- **连接池**: 数据库连接池复用
- **内存管理**: 及时释放大对象
- **文件清理**: 定时清理临时文件

## 部署架构

### 单机部署
```yaml
services:
  backend:
    image: translation-backend:v2
    ports:
      - "8013:8013"
    environment:
      - DB_URL=mysql://localhost/translation
      - REDIS_URL=redis://localhost:6379
    volumes:
      - ./data:/app/data
```

### 集群部署
```yaml
# 负载均衡器
nginx:
  upstream backend {
    server backend1:8013;
    server backend2:8013;
    server backend3:8013;
  }

# 应用节点
backend-nodes:
  scale: 3
  resources:
    cpu: 2
    memory: 4G
```

### 监控部署
- **Prometheus**: 指标收集
- **Grafana**: 可视化面板
- **ELK Stack**: 日志分析

## 安全设计

### 1. 认证授权
- Session Token验证
- API Key管理
- 角色权限控制

### 2. 数据安全
- 敏感信息加密
- SQL注入防护
- XSS攻击防护

### 3. 限流控制
- API调用频率限制
- 文件大小限制
- 并发数量控制

## 扩展性设计

### 1. 插件化LLM
- 统一Provider接口
- 动态加载机制
- 配置化切换

### 2. 模块化服务
- 服务注册发现
- 消息队列解耦
- 微服务化准备

### 3. 水平扩展
- 无状态设计
- 分布式任务
- 负载均衡

## 总结

Backend V2架构采用了成熟的分层设计，以DataFrame为核心构建了高效的批量翻译系统。通过服务化拆分、异步处理、智能批处理等技术手段，实现了高性能、高可用、易扩展的企业级翻译平台。

### 架构亮点
1. **DataFrame中心化**: 统一数据模型，高效处理
2. **服务解耦**: 清晰的模块边界，易于维护
3. **LLM抽象**: 多模型支持，灵活切换
4. **批处理优化**: 智能合并，成本优化
5. **实时监控**: WebSocket推送，体验优秀

### 后续演进方向
1. 分布式任务调度
2. 多租户隔离
3. 自动化测试完善
4. 容器化部署
5. AI模型微调

---

文档版本: 1.0.0
更新日期: 2025-01-29
维护团队: Translation System Team