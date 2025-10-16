# 管道式转换架构设计

## 核心理念

**翻译是转换的一种**，所有操作都可以抽象为：
```
输入数据 → [转换器] → 输出数据
```

## 架构层次

```
┌─────────────────────────────────────────────────┐
│              Pipeline Orchestrator              │  编排层
│         (定义执行顺序、依赖关系、数据流)           │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│                 Stage Layer                     │  阶段层
│  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │ Splitter│  │Transform│  │ Exporter│         │
│  └─────────┘  └─────────┘  └─────────┘         │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│              Transformer Layer                  │  转换器层
│  ┌──────────────┐  ┌──────────────┐            │
│  │LLMTransformer│  │CapsTransform │            │
│  └──────────────┘  └──────────────┘            │
│  ┌──────────────┐  ┌──────────────┐            │
│  │TrimTransform │  │NormalizeXform│            │
│  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│                 Data Layer                      │  数据层
│         (TaskDataFrame, ExcelDataFrame)         │
└─────────────────────────────────────────────────┘
```

## 完整流程示例

### CAPS翻译场景

```
阶段1: 初始拆分
  输入: Excel原始数据
  拆分器: NormalTaskSplitter
  输出: Task[yellow, blue, normal]

阶段2: LLM翻译转换
  输入: Task[yellow, blue, normal]
  转换器: LLMTranslator
  输出: Task[yellow, blue, normal] with results

阶段3: CAPS任务拆分
  输入: Task[yellow, blue, normal] with results
  拆分器: CapsTaskSplitter
  条件: sheet_name contains 'CAPS'
  输出: Task[caps]

阶段4: CAPS大写转换
  输入: Task[caps]
  转换器: CapsTransformer
  依赖数据: 阶段2的翻译结果
  输出: Task[caps] with uppercased results

阶段5: 合并导出
  输入: [阶段2结果, 阶段4结果]
  导出器: ExcelExporter
  输出: 翻译后的Excel文件
```

## 核心接口定义

### 1. 基础转换器接口

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseTransformer(ABC):
    """所有转换器的基类"""

    @abstractmethod
    def transform(self, input_data: Any, context: Dict = None) -> Any:
        """
        执行转换

        Args:
            input_data: 输入数据（可以是任何类型）
            context: 上下文数据（可能需要其他阶段的结果）

        Returns:
            转换后的数据
        """
        pass

    def validate_input(self, input_data: Any) -> bool:
        """验证输入数据是否有效"""
        return True

    def get_dependencies(self) -> List[str]:
        """返回依赖的其他阶段ID"""
        return []
```

### 2. 任务拆分器接口

```python
class TaskSplitter(BaseTransformer):
    """任务拆分器"""

    def transform(self, input_data: Any, context: Dict = None) -> List[Dict]:
        """
        将输入数据拆分为任务列表

        Returns:
            List[Task] - 任务列表
        """
        pass
```

### 3. 数据转换器接口

```python
class DataTransformer(BaseTransformer):
    """数据转换器（如LLM翻译、大写转换等）"""

    def transform(self, tasks: List[Dict], context: Dict = None) -> List[Dict]:
        """
        对任务列表进行转换，填充result字段

        Returns:
            List[Task] with results
        """
        pass
```

### 4. 管道阶段定义

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class PipelineStage:
    """管道阶段配置"""

    stage_id: str                      # 阶段唯一标识
    transformer: BaseTransformer       # 使用的转换器
    input_stage: Optional[str] = None  # 输入来自哪个阶段
    depends_on: List[str] = None       # 依赖的其他阶段（用于context）
    condition: Optional[callable] = None  # 执行条件

    def should_execute(self, context: Dict) -> bool:
        """判断是否应该执行这个阶段"""
        if self.condition:
            return self.condition(context)
        return True
```

### 5. 管道编排器

```python
class PipelineOrchestrator:
    """管道编排器 - 负责协调各个阶段的执行"""

    def __init__(self):
        self.stages: List[PipelineStage] = []
        self.results: Dict[str, Any] = {}  # 存储每个阶段的结果

    def add_stage(self, stage: PipelineStage):
        """添加一个阶段"""
        self.stages.append(stage)

    def execute(self, initial_input: Any) -> Dict[str, Any]:
        """
        执行整个管道

        Returns:
            Dict[stage_id, result] - 所有阶段的结果
        """
        current_input = initial_input

        for stage in self.stages:
            # 检查是否应该执行
            if not stage.should_execute(self.results):
                continue

            # 准备输入数据
            if stage.input_stage:
                current_input = self.results[stage.input_stage]

            # 准备上下文（依赖的其他阶段结果）
            context = {}
            if stage.depends_on:
                for dep_stage_id in stage.depends_on:
                    context[dep_stage_id] = self.results[dep_stage_id]

            # 执行转换
            output = stage.transformer.transform(current_input, context)

            # 保存结果
            self.results[stage.stage_id] = output
            current_input = output

        return self.results
```

## 具体实现示例

### LLM翻译转换器

```python
class LLMTranslator(DataTransformer):
    """LLM翻译转换器"""

    def __init__(self, llm_provider):
        self.llm_provider = llm_provider

    def transform(self, tasks: List[Dict], context: Dict = None) -> List[Dict]:
        """执行LLM翻译"""
        # 批量翻译
        for task in tasks:
            if task['task_type'] in ['normal', 'yellow', 'blue']:
                result = self.llm_provider.translate(task['source_text'])
                task['result'] = result

        return tasks
```

### CAPS大写转换器

```python
class CapsTransformer(DataTransformer):
    """CAPS大写转换器"""

    def get_dependencies(self) -> List[str]:
        """依赖翻译阶段的结果"""
        return ['translate_stage']

    def transform(self, tasks: List[Dict], context: Dict = None) -> List[Dict]:
        """
        执行大写转换

        Args:
            tasks: CAPS任务列表
            context: 包含'translate_stage'的翻译结果
        """
        # 从context中获取翻译结果
        translated_tasks = context.get('translate_stage', [])

        # 建立位置索引
        position_map = {}
        for task in translated_tasks:
            key = (task['sheet_name'], task['row_idx'], task['col_idx'])
            position_map[key] = task['result']

        # 转换CAPS任务
        for caps_task in tasks:
            key = (caps_task['sheet_name'], caps_task['row_idx'], caps_task['col_idx'])

            # 查找对应位置的翻译结果
            if key in position_map:
                source_text = position_map[key]
            else:
                source_text = caps_task.get('source_text', '')

            # 转大写
            caps_task['result'] = source_text.upper() if source_text else ''

        return tasks
```

### CAPS任务拆分器

```python
class CapsTaskSplitter(TaskSplitter):
    """CAPS任务拆分器"""

    def transform(self, excel_df: ExcelDataFrame, context: Dict = None) -> List[Dict]:
        """
        从Excel中拆分CAPS任务

        只处理sheet名称包含'CAPS'的sheet
        """
        tasks = []

        for sheet_name in excel_df.get_sheet_names():
            if 'caps' not in sheet_name.lower():
                continue

            df = excel_df.get_sheet(sheet_name)

            # 为每个非源列创建CAPS任务
            for row_idx in range(len(df)):
                for col_idx in range(len(df.columns)):
                    # 跳过源列（根据列名判断）
                    col_name = df.columns[col_idx]
                    if col_name.upper() in ['KEY', 'CH', 'CN']:
                        continue

                    task = {
                        'task_id': f'CAPS_{sheet_name}_{row_idx}_{col_idx}',
                        'task_type': 'caps',
                        'sheet_name': sheet_name,
                        'row_idx': row_idx,
                        'col_idx': col_idx,
                        'target_lang': col_name.upper(),
                        'status': 'pending'
                    }
                    tasks.append(task)

        return tasks
```

## 配置文件示例

```yaml
# pipeline_config.yaml

pipeline:
  name: "translation_with_caps"
  description: "标准翻译流程 + CAPS大写转换"

  stages:
    - id: "split_normal"
      type: "splitter"
      class: "NormalTaskSplitter"
      config:
        task_types: ["normal", "yellow", "blue"]

    - id: "translate"
      type: "transformer"
      class: "LLMTranslator"
      input: "split_normal"
      config:
        provider: "qwen-plus"
        batch_size: 10

    - id: "split_caps"
      type: "splitter"
      class: "CapsTaskSplitter"
      condition: "has_caps_sheets"  # 只在有CAPS sheet时执行

    - id: "uppercase"
      type: "transformer"
      class: "CapsTransformer"
      input: "split_caps"
      depends_on: ["translate"]  # 依赖翻译结果

    - id: "export"
      type: "exporter"
      class: "ExcelExporter"
      input: ["translate", "uppercase"]  # 合并多个阶段的结果
```

## 使用示例

```python
# 创建管道
orchestrator = PipelineOrchestrator()

# 加载配置
config = load_config('pipeline_config.yaml')

# 构建阶段
for stage_config in config['stages']:
    transformer = create_transformer(stage_config)
    stage = PipelineStage(
        stage_id=stage_config['id'],
        transformer=transformer,
        input_stage=stage_config.get('input'),
        depends_on=stage_config.get('depends_on', [])
    )
    orchestrator.add_stage(stage)

# 执行管道
excel_df = load_excel('input.xlsx')
results = orchestrator.execute(excel_df)

# 获取最终结果
final_output = results['export']
```

## 优势总结

1. **统一抽象** - 所有操作都是转换
2. **灵活编排** - 通过配置文件定义流程
3. **清晰依赖** - 显式声明阶段间的依赖关系
4. **易于扩展** - 添加新转换器不影响现有代码
5. **可测试性** - 每个转换器可以独立测试
6. **可维护性** - 职责清晰，模块解耦

## 未来扩展方向

1. **并行执行** - 无依赖关系的阶段可以并行执行
2. **条件分支** - 根据数据特征选择不同的转换路径
3. **错误恢复** - 某个阶段失败时的回滚机制
4. **缓存机制** - 缓存中间结果，支持断点续传
5. **可视化监控** - 实时显示管道执行进度
