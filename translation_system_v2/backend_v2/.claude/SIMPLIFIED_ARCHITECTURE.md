# 简化架构：数据状态流转 + 任务驱动

## 核心理念

**原始数据 = 结果数据 = 数据状态**

只有一种中间数据：**任务拆分表**（描述状态变化）

## 概念模型

```
┌─────────────┐
│ 数据状态 N   │  ← 可读可写的数据（Excel/JSON/DB）
└─────────────┘
       ↓
┌─────────────┐
│  拆分器      │  ← 分析状态，生成任务表
└─────────────┘
       ↓
┌─────────────┐
│ 任务拆分表   │  ← 唯一的中间数据（指令集）
└─────────────┘
       ↓
┌─────────────┐
│  转换器      │  ← 执行任务，修改数据状态
└─────────────┘
       ↓
┌─────────────┐
│数据状态 N+1  │  ← 新的数据状态（可继续流转）
└─────────────┘
```

## 数据定义

### 数据状态（Data State）
```python
# 数据状态可以是任何格式
DataState = ExcelDataFrame | JSONData | DatabaseRows | ...

# 示例
state_0 = ExcelDataFrame.load("input.xlsx")
state_1 = ExcelDataFrame.load("translated.xlsx")
state_2 = ExcelDataFrame.load("uppercased.xlsx")

# 状态之间没有本质区别，都是数据的某个快照
```

### 任务拆分表（Task DataFrame）
```python
# 任务表是唯一的中间数据结构
# 描述：从当前状态 → 目标状态 需要做的操作

TaskDataFrame:
    task_id: str          # 任务ID

    # 位置信息
    sheet_name: str       # 哪个sheet
    row_idx: int          # 哪一行
    col_idx: int          # 哪一列

    # 操作信息
    operation: str        # 做什么操作（translate/uppercase/trim...）
    source_text: str      # 当前状态的值
    target_lang: str      # 目标语言/格式

    # 执行状态
    status: str           # pending/completed/failed
    result: str           # 执行后的值

    # 元数据
    priority: int         # 优先级
    depends_on: List[str] # 依赖哪些任务
```

## 核心组件

### 1. 拆分器（Splitter）

**职责**：分析数据状态，生成任务列表

```python
class TaskSplitter:
    def split(self, data_state: DataState, rules: List[Rule]) -> TaskDataFrame:
        """
        分析数据状态，生成任务表

        Args:
            data_state: 当前数据状态
            rules: 拆分规则（如：空单元格要翻译，黄色单元格要重译等）

        Returns:
            任务拆分表
        """
        tasks = []

        for rule in rules:
            # 扫描数据状态，找到符合规则的位置
            matches = rule.match(data_state)

            for match in matches:
                task = {
                    'task_id': generate_id(),
                    'sheet_name': match.sheet,
                    'row_idx': match.row,
                    'col_idx': match.col,
                    'operation': rule.operation,  # 'translate', 'uppercase', etc.
                    'source_text': match.value,
                    'status': 'pending'
                }
                tasks.append(task)

        return TaskDataFrame(tasks)
```

**示例规则**：
```python
# 规则1: 空单元格需要翻译
EmptyNeedsTranslation = Rule(
    condition=lambda cell: cell.is_empty(),
    operation='translate',
    target_lang='from_column_name'
)

# 规则2: 黄色单元格需要重译
YellowNeedsRetranslation = Rule(
    condition=lambda cell: cell.color == 'yellow',
    operation='translate',
    priority=9
)

# 规则3: CAPS sheet需要大写转换
CapsNeedsUppercase = Rule(
    condition=lambda cell: 'CAPS' in cell.sheet_name,
    operation='uppercase',
    depends_on_operation='translate'  # 依赖翻译结果
)
```

### 2. 转换器（Transformer）

**职责**：执行任务表中的操作，修改数据状态

```python
class Transformer:
    def execute(self,
                data_state: DataState,
                tasks: TaskDataFrame,
                context: Dict = None) -> DataState:
        """
        执行任务，生成新的数据状态

        Args:
            data_state: 当前数据状态
            tasks: 任务表
            context: 上下文数据（其他状态的数据）

        Returns:
            新的数据状态
        """
        # 复制当前状态
        new_state = data_state.copy()

        # 执行每个任务
        for task in tasks:
            # 根据operation选择处理器
            processor = self.get_processor(task['operation'])

            # 执行处理
            result = processor.process(task, context)

            # 更新数据状态
            new_state.set_value(
                task['sheet_name'],
                task['row_idx'],
                task['col_idx'],
                result
            )

            # 更新任务状态
            task['result'] = result
            task['status'] = 'completed'

        return new_state
```

**处理器示例**：
```python
class LLMProcessor:
    """LLM翻译处理器"""
    def process(self, task: Dict, context: Dict) -> str:
        source = task['source_text']
        target_lang = task['target_lang']
        return self.llm.translate(source, target_lang)

class UppercaseProcessor:
    """大写转换处理器"""
    def process(self, task: Dict, context: Dict) -> str:
        # 从context中获取翻译后的值
        if context and 'translated_value' in context:
            source = context['translated_value']
        else:
            source = task['source_text']

        return source.upper()
```

## 完整流程示例

### CAPS翻译场景

```python
# ============================================
# 阶段1: 翻译普通任务
# ============================================

# 输入：原始Excel
state_0 = ExcelDataFrame.load("input.xlsx")

# 拆分：生成翻译任务
translation_rules = [
    EmptyNeedsTranslation,
    YellowNeedsRetranslation,
    BlueNeedsShortening
]
tasks_1 = splitter.split(state_0, rules=translation_rules)
# 输出任务表：
# | task_id | sheet | row | col | operation  | source   | status  |
# |---------|-------|-----|-----|------------|----------|---------|
# | T001    | Data  | 0   | 3   | translate  | 铭文印记  | pending |
# | T002    | Data  | 0   | 4   | translate  | 铭文印记  | pending |

# 转换：执行翻译
llm_transformer = Transformer(processor=LLMProcessor())
state_1 = llm_transformer.execute(state_0, tasks_1)
# 现在 tasks_1 中的 result 字段被填充：
# | task_id | result                |
# |---------|-----------------------|
# | T001    | รูนมาร์ค (泰语)        |
# | T002    | 銘文印記 (繁中)         |

# state_1 就是翻译后的Excel状态

# ============================================
# 阶段2: CAPS大写转换
# ============================================

# 输入：翻译后的Excel（state_1）
# 注意：state_1 对于这个阶段来说，就是"原始数据"

# 拆分：生成CAPS任务
caps_rules = [
    CapsNeedsUppercase  # 条件：sheet名包含'CAPS'
]
tasks_2 = splitter.split(state_1, rules=caps_rules)
# 输出任务表：
# | task_id | sheet    | row | col | operation  | source_text      | depends_on |
# |---------|----------|-----|-----|------------|------------------|------------|
# | C001    | CAPS第二 | 0   | 3   | uppercase  | รูนมาร์ค          | T001       |
# | C002    | CAPS第二 | 0   | 4   | uppercase  | 銘文印記          | T002       |

# 转换：执行大写转换
# 注意：需要传入context，因为CAPS转换依赖翻译结果
context = {
    'translated_tasks': tasks_1  # 传入翻译任务表
}

caps_transformer = Transformer(processor=UppercaseProcessor())
state_2 = caps_transformer.execute(state_1, tasks_2, context=context)

# 最终状态
state_2.save("output.xlsx")
```

## 数据流可视化

```
Excel原始文件 (state_0)
    │
    │ [拆分] rules: [空单元格, 黄色, 蓝色]
    ↓
任务表1 (tasks_1)
    | task_id | operation  | source   | result   |
    | T001    | translate  | 铭文印记  | (空)     |
    | T002    | translate  | 铭文印记  | (空)     |
    │
    │ [转换] LLMProcessor
    ↓
任务表1 (tasks_1) ← 填充result
    | task_id | operation  | source   | result      |
    | T001    | translate  | 铭文印记  | รูนมาร์ค    |
    | T002    | translate  | 铭文印记  | 銘文印記     |
    │
    │ [应用到数据状态]
    ↓
Excel翻译后 (state_1)
    │
    │ [拆分] rules: [CAPS sheet]
    ↓
任务表2 (tasks_2)
    | task_id | operation  | source_text | result |
    | C001    | uppercase  | รูนมาร์ค     | (空)   |
    | C002    | uppercase  | 銘文印記      | (空)   |
    │
    │ [转换] UppercaseProcessor + context(tasks_1)
    ↓
任务表2 (tasks_2) ← 填充result
    | task_id | operation  | source_text | result     |
    | C001    | uppercase  | รูนมาร์ค     | รูนมาร์ค   |
    | C002    | uppercase  | 銘文印記      | 銘文印記    |
    │
    │ [应用到数据状态]
    ↓
Excel最终版本 (state_2)
```

## 编排器（Orchestrator）

```python
class PipelineOrchestrator:
    """简化的管道编排器"""

    def __init__(self):
        self.stages = []

    def add_stage(self, splitter_rules, transformer):
        """
        添加一个阶段

        Args:
            splitter_rules: 拆分规则列表
            transformer: 转换器实例
        """
        self.stages.append({
            'splitter_rules': splitter_rules,
            'transformer': transformer
        })

    def execute(self, initial_state: DataState) -> DataState:
        """执行整个流程"""
        current_state = initial_state
        all_tasks = {}  # 保存所有阶段的任务表（用于依赖）

        for idx, stage in enumerate(self.stages):
            # 1. 拆分：生成任务表
            tasks = self.splitter.split(
                current_state,
                rules=stage['splitter_rules']
            )

            # 2. 转换：执行任务
            context = {'all_tasks': all_tasks}  # 传入之前所有的任务
            new_state = stage['transformer'].execute(
                current_state,
                tasks,
                context=context
            )

            # 3. 保存任务表和状态
            all_tasks[f'stage_{idx}'] = tasks
            current_state = new_state

        return current_state
```

## 使用示例

```python
# 创建编排器
orchestrator = PipelineOrchestrator()

# 阶段1: 翻译
orchestrator.add_stage(
    splitter_rules=[
        EmptyNeedsTranslation,
        YellowNeedsRetranslation
    ],
    transformer=Transformer(LLMProcessor())
)

# 阶段2: CAPS大写
orchestrator.add_stage(
    splitter_rules=[
        CapsNeedsUppercase
    ],
    transformer=Transformer(UppercaseProcessor())
)

# 执行
input_excel = ExcelDataFrame.load("input.xlsx")
output_excel = orchestrator.execute(input_excel)
output_excel.save("output.xlsx")
```

## 优势

1. **概念简洁** - 只有两个核心概念：数据状态、任务表
2. **状态独立** - 每个数据状态都是独立的，可以单独保存/加载
3. **任务可追踪** - 任务表记录了所有变更，便于审计
4. **易于理解** - 流程线性清晰：状态→任务→转换→新状态
5. **灵活组合** - 可以任意添加新的拆分规则和转换器

## 文件结构

```
services/
├── splitter/
│   ├── task_splitter.py      # 任务拆分器
│   └── rules/                 # 拆分规则
│       ├── empty_cell.py
│       ├── yellow_cell.py
│       └── caps_sheet.py
│
├── transformer/
│   ├── transformer.py         # 转换器框架
│   └── processors/            # 处理器
│       ├── llm_processor.py
│       ├── uppercase_processor.py
│       └── trim_processor.py
│
├── orchestrator/
│   └── pipeline.py            # 管道编排器
│
└── data_state/
    └── excel_dataframe.py     # 数据状态封装
```

## 与现有代码的关系

现有代码可以逐步迁移：

1. **保留** `ExcelDataFrame` - 作为数据状态的实现
2. **保留** `TaskDataFrameManager` - 作为任务表的实现
3. **重构** `TaskSplitter` - 使用规则驱动
4. **重构** `BatchTranslator` - 作为LLMProcessor
5. **新增** `Orchestrator` - 协调整个流程

无需大规模重写，只需调整组织方式！
