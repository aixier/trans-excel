# Task DataFrame 设计说明文档

## 概述
Task DataFrame是翻译系统的核心数据结构，用于管理和跟踪所有翻译任务的生命周期。每一行代表一个独立的翻译任务。

## 字段说明

### 1. 任务标识字段

#### task_id
- **类型**: string
- **格式**: `TASK_XXXX` (例如: TASK_0001)
- **说明**: 任务的唯一标识符，全局唯一
- **生成时机**: 任务创建时自动生成
- **用途**: 任务追踪、日志记录、错误定位

#### batch_id
- **类型**: string
- **格式**: `BATCH_{lang}_{TYPE}_{num}` (例如: BATCH_TR_NORMAL_001)
- **说明**: 批次标识符，用于批量处理任务
- **组成规则**:
  - `{lang}`: 目标语言代码 (TR/PT/TH/VN等)
  - `{TYPE}`: 任务类型 (NORMAL/YELLOW/BLUE)
  - `{num}`: 批次序号 (001-999)
- **用途**: 批量提交API请求、并发控制、成本优化

#### group_id
- **类型**: string
- **格式**: `GROUP_{category}_{num}` (例如: GROUP_UI_001)
- **说明**: 任务分组标识，相似内容的任务共享同一group_id
- **分组策略**:
  - 按Sheet类型: UI/DIALOG/ITEM/SKILL/QUEST
  - 按文本长度: SHORT/MEDIUM/LONG
- **用途**: 上下文共享、翻译一致性保证、批量审核

### 2. 语言和内容字段

#### source_lang
- **类型**: string
- **可选值**: CH(中文) / EN(英文)
- **说明**: 源语言代码
- **用途**: 选择正确的语言模型、应用语言特定规则

#### source_text
- **类型**: string
- **说明**: 需要翻译的原始文本
- **限制**: 不能为空
- **用途**: 翻译的输入内容

#### source_context
- **类型**: string
- **说明**: 源文本的上下文信息
- **内容**: 同行/列的相关文本、前后文内容
- **格式示例**:
  ```
  上文: [前一行内容]
  下文: [后一行内容]
  同行其他列: [相关内容]
  ```
- **用途**: 提高翻译准确性、保持语境一致性

#### game_context
- **类型**: string
- **说明**: 游戏相关的背景信息
- **内容**: 游戏名称、类型、世界观、专有名词等
- **用途**: 确保游戏术语翻译的准确性

#### target_lang
- **类型**: string
- **可选值**: TR/TH/PT/VN/IND/ES
- **说明**: 目标语言代码
- **映射关系**:
  - TR: 土耳其语
  - TH: 泰语
  - PT: 葡萄牙语
  - VN: 越南语
  - IND: 印尼语
  - ES: 西班牙语

### 3. Excel位置字段

#### excel_id
- **类型**: string
- **格式**: UUID
- **说明**: Excel文件的唯一标识
- **用途**: 关联原始文件、结果回写

#### sheet_name
- **类型**: string
- **说明**: Excel工作表名称
- **用途**: 定位数据源、结果回写位置

#### row_idx
- **类型**: integer
- **说明**: 行索引（0开始）
- **用途**: 精确定位单元格位置

#### col_idx
- **类型**: integer
- **说明**: 列索引（0开始）
- **用途**: 精确定位单元格位置

#### cell_ref
- **类型**: string
- **格式**: Excel单元格引用 (例如: A1, B15)
- **说明**: 人类可读的单元格位置
- **用途**: 调试、错误报告、用户界面显示

### 4. 任务状态字段

#### status
- **类型**: string
- **可选值**:
  - `pending`: 待处理
  - `processing`: 处理中
  - `completed`: 已完成
  - `failed`: 失败
  - `cancelled`: 已取消
- **状态流转**:
  ```
  pending → processing → completed
                     ↘ → failed
         → cancelled
  ```
- **用途**: 任务队列管理、进度跟踪、重试控制

#### priority
- **类型**: integer
- **范围**: 1-10 (10为最高优先级)
- **默认值**: 5
- **优先级规则**:
  - UI文本: 8
  - 短文本(≤20字符): 7
  - 对话文本: 5
  - 其他: 5
- **用途**: 任务调度优先级控制

#### task_type
- **类型**: string
- **可选值**:
  - `normal`: 常规翻译（无颜色标记）
  - `yellow`: 黄色重翻译任务
  - `blue`: 蓝色缩短任务
- **说明**: 基于Excel单元格颜色确定的任务类型
- **用途**: 选择不同的提示词模板、应用特定处理逻辑

### 5. 结果字段

#### result
- **类型**: string
- **说明**: 翻译结果文本
- **默认值**: 空字符串
- **用途**: 存储LLM返回的翻译结果

#### confidence
- **类型**: float
- **范围**: 0.0-1.0
- **说明**: 翻译结果的置信度
- **计算方法**: 基于模型返回的概率或自定义评分
- **用途**: 质量控制、人工审核筛选

#### is_final
- **类型**: boolean
- **默认值**: false
- **说明**: 是否为最终确认的翻译结果
- **用途**: 区分草稿和最终版本

#### reviewer_notes
- **类型**: string
- **说明**: 审核员的备注和修改建议
- **用途**: 质量改进、问题记录

### 6. 统计字段

#### char_count
- **类型**: integer
- **说明**: source_text + source_context的字符总数
- **用途**: 批次分配、成本计算、性能优化

#### token_count
- **类型**: integer
- **说明**: API调用消耗的token数量
- **用途**: 成本计算、配额管理

#### cost
- **类型**: float
- **单位**: 人民币(元)
- **说明**: 该任务的API调用成本
- **计算公式**: token_count * 单价
- **用途**: 成本统计、预算控制

### 7. 时间字段

#### created_at
- **类型**: datetime
- **说明**: 任务创建时间
- **格式**: ISO 8601
- **用途**: 任务追踪、统计分析

#### updated_at
- **类型**: datetime
- **说明**: 任务最后更新时间
- **自动更新**: 任何字段变更时
- **用途**: 变更追踪、缓存控制

#### start_time
- **类型**: datetime
- **说明**: 任务开始执行时间
- **触发条件**: status变为processing时
- **用途**: 性能监控、超时控制

#### end_time
- **类型**: datetime
- **说明**: 任务结束时间
- **触发条件**: status变为completed/failed时
- **用途**: 执行时长计算

#### duration_ms
- **类型**: integer
- **单位**: 毫秒
- **说明**: 任务执行耗时
- **计算**: end_time - start_time
- **用途**: 性能分析、优化决策

### 8. 错误处理字段

#### retry_count
- **类型**: integer
- **默认值**: 0
- **最大值**: 3 (可配置)
- **说明**: 任务重试次数
- **用途**: 重试控制、错误分析

#### error_message
- **类型**: string
- **说明**: 错误信息详情
- **内容示例**:
  - API超时
  - Token限制
  - 模型错误
  - 网络异常
- **用途**: 错误诊断、问题修复

#### llm_model
- **类型**: string
- **说明**: 使用的LLM模型标识
- **示例**: gpt-4, qwen-turbo, claude-3
- **用途**: 模型性能对比、成本分析

## 使用场景

### 1. 任务创建流程
```python
# 创建新任务时需要设置的字段
required_fields = [
    'task_id', 'source_text', 'source_lang',
    'target_lang', 'excel_id', 'sheet_name',
    'row_idx', 'col_idx', 'task_type'
]

# 自动生成的字段
auto_fields = [
    'created_at', 'updated_at', 'status'(默认pending)
]
```

### 2. 批量处理
```python
# 按batch_id分组处理
# 同一批次的任务会一起提交给LLM API
batch_tasks = df[df['batch_id'] == 'BATCH_TR_NORMAL_001']
```

### 3. 状态管理
```python
# 获取待处理任务
pending_tasks = df[df['status'] == 'pending']

# 按优先级排序
priority_tasks = pending_tasks.sort_values('priority', ascending=False)
```

### 4. 结果回写
```python
# 使用excel_id, sheet_name, row_idx, col_idx
# 精确定位并更新Excel单元格
for task in completed_tasks:
    excel.update_cell(
        sheet=task['sheet_name'],
        row=task['row_idx'],
        col=task['col_idx'],
        value=task['result']
    )
```

## 数据完整性约束

1. **唯一性约束**:
   - task_id必须全局唯一
   - (excel_id, sheet_name, row_idx, col_idx, target_lang)组合唯一

2. **非空约束**:
   - task_id, source_text, target_lang不能为空
   - status必须有值（默认pending）

3. **引用完整性**:
   - batch_id必须对应有效的批次
   - excel_id必须对应已上传的文件

4. **业务规则**:
   - 同一batch_id内的task_type必须相同
   - retry_count不能超过最大重试次数
   - confidence值必须在0-1范围内

## 性能优化建议

1. **索引字段**:
   - task_id (主键)
   - batch_id (批量查询)
   - status (状态筛选)
   - excel_id + sheet_name (回写定位)

2. **分区策略**:
   - 按status分区存储
   - 已完成任务可归档

3. **缓存策略**:
   - 热点数据(pending/processing)保持在内存
   - 完成的任务可持久化到磁盘

## 扩展性设计

### 预留字段用途
- 支持多轮翻译(revision_count)
- 支持翻译评分(quality_score)
- 支持用户反馈(user_feedback)
- 支持版本控制(version)

### 元数据扩展
可通过JSON字段存储额外的元数据:
```python
metadata = {
    'client_id': 'xxx',
    'project_name': 'xxx',
    'custom_rules': {},
    'tags': []
}
```