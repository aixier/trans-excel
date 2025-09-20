# Translation System Backend Architecture

## 目录结构

```
backend/
├── api_gateway/          # API网关层
│   ├── main.py          # FastAPI主应用
│   ├── models/           # API数据模型
│   └── routers/          # 路由处理
│       ├── health.py     # 健康检查
│       ├── project.py    # 项目管理API
│       └── translation.py # 翻译API
├── config/               # 配置管理
│   └── settings.py       # 系统配置
├── database/             # 数据库层
│   ├── connection.py     # 数据库连接管理
│   └── models.py         # 数据库模型
├── excel_analysis/       # Excel分析模块
│   ├── header_analyzer.py    # 表头分析器
│   └── translation_detector.py # 翻译任务检测器
├── file_service/         # 文件服务
│   └── storage/          # 存储接口
│       ├── base.py       # 存储基类
│       └── oss_storage.py # OSS存储实现
├── project_manager/      # 项目管理
│   └── manager.py        # 项目管理器
├── translation_core/     # 翻译核心
│   ├── translation_engine.py  # 翻译引擎（主逻辑）
│   ├── localization_engine.py # 本地化引擎
│   ├── terminology_manager.py # 术语管理
│   └── placeholder_protector.py # 占位符保护
└── scripts/              # 脚本工具

## 核心组件功能

### 1. Excel分析模块 (excel_analysis/)

#### HeaderAnalyzer (header_analyzer.py)
- **功能**: 分析Excel表头，识别语言列和其他列类型
- **语言支持**: CH, TW, EN, PT, TH, IND, TR, ES, AR, RU, JA, KO, VN, DE, FR, IT
- **列类型**: KEY, SOURCE, TARGET, CONTEXT, STATUS, METADATA
- **核心方法**:
  - `analyze_sheet()`: 分析单个Sheet结构
  - `_analyze_column()`: 识别列类型和语言

#### TranslationDetector (translation_detector.py)
- **功能**: 检测需要翻译的任务
- **检测策略**:
  - 按行动态检测源语言（优先EN > CH > 其他）
  - 检查每个目标语言列是否需要翻译
  - 支持颜色标记（黄色=修改，蓝色=缩短，绿色=完成）
- **核心方法**:
  - `detect_translation_tasks()`: 检测所有翻译任务
  - `group_tasks_by_batch()`: 将任务分组为批次

### 2. 翻译核心 (translation_core/)

#### TranslationEngine (translation_engine.py)
- **功能**: 主翻译引擎，协调整个翻译流程
- **流程**:
  1. 分析Excel文件结构
  2. 自动检测需要翻译的sheets（使用HeaderAnalyzer + TranslationDetector）
  3. 迭代翻译（支持多轮迭代）
  4. 批量并发处理
  5. 保存结果
- **关键特性**:
  - 支持多Sheet处理
  - 真正的增量翻译（每轮检测剩余任务）
  - 自动创建缺失的语言列
  - 动态批次大小和超时控制

#### LocalizationEngine (localization_engine.py)
- **功能**: 处理本地化相关逻辑
- **特性**: 区域特定的翻译规则

#### TerminologyManager (terminology_manager.py)
- **功能**: 管理术语表
- **特性**: 确保术语翻译一致性

### 3. API层 (api_gateway/)

#### 翻译API (routers/translation.py)
- **端点**:
  - `POST /upload`: 上传文件并启动翻译
  - `GET /tasks/{task_id}/status`: 查询任务状态
  - `GET /tasks/{task_id}/progress`: 查询详细进度
  - `GET /tasks/{task_id}/download`: 下载翻译结果
  - `POST /analyze`: 分析Excel结构

- **参数**:
  - `target_languages`: 可选，不传时自动检测所有需要的语言
  - `sheet_names`: 可选，指定要处理的sheets
  - `auto_detect`: 自动检测需要翻译的sheets
  - `batch_size`: 批次大小
  - `max_concurrent`: 最大并发数

### 4. 数据流

```
用户上传Excel
    ↓
API Gateway 接收文件
    ↓
TranslationEngine.process_translation_task()
    ↓
HeaderAnalyzer 分析表头结构
    ↓
TranslationDetector 检测翻译任务
    ↓
迭代翻译流程:
    1. 检测剩余任务
    2. 分批处理
    3. 并发翻译
    4. 应用结果
    5. 重复直到完成
    ↓
保存结果文件
    ↓
用户下载结果
```

## 关键设计决策

### 1. 自动语言检测
- **不依赖用户指定**: 系统自动检测所有需要翻译的语言
- **智能源语言选择**: 按行动态选择源语言（EN > CH > 其他）
- **自动创建列**: 如果目标语言列不存在，自动创建

### 2. 增量翻译
- **真正的迭代**: 每轮重新检测剩余任务
- **避免重复翻译**: 已完成的内容不会重复处理
- **支持多轮迭代**: 处理复杂的翻译场景

### 3. 并发处理
- **批量处理**: 将任务分组为批次
- **并发控制**: 使用信号量控制并发数
- **动态超时**: 根据迭代轮次调整超时时间

## 问题和改进点

### 当前问题
1. ~~`_detect_translatable_sheets` 依赖 `target_languages`，限制了自动检测~~ (已修复)
2. ~~重复的语言检测逻辑~~ (已修复)
3. 下载API未完全实现文件服务

### 改进建议
1. 统一使用 HeaderAnalyzer + TranslationDetector 进行检测
2. 让 target_languages 成为可选的过滤器，而非必需参数
3. 完善文件下载服务