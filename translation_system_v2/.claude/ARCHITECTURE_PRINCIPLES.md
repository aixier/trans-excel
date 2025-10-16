# 核心架构理念

**⚠️ 重要：所有开发必须遵循以下架构原则！**

## 基本理念

### 1. 数据状态的连续性

**原始数据 = 结果数据 = 数据状态**

```
❌ 错误理解：
原始数据 → 处理 → 结果数据
   ↑                    ↑
  不同的概念          不同的概念

✅ 正确理解：
数据状态0 → [转换] → 数据状态1 → [转换] → 数据状态2
    ↓                    ↓                    ↓
  都是数据            都是数据            都是数据
```

**关键点**：
- Excel原始文件是"数据状态0"
- Excel翻译后是"数据状态1"
- Excel大写转换后是"数据状态2"
- 任何状态都可以作为下一个转换的输入
- 不存在"原始"和"结果"的本质区别

### 2. 任务拆分表是唯一的中间数据

**任务表描述：如何从状态N变成状态N+1**

```python
# 任务表是状态之间的"差分"（diff）
TaskDataFrame = {
    'source': '状态N中的数据',
    'target': '状态N+1中应该是什么',
    'operation': '如何转换',
    'result': '转换后的值'
}
```

**关键点**：
- 任务表不是数据本身，而是状态转换的指令
- 任务表记录了所有需要执行的操作
- 任务表可以被保存、恢复、重放

### 3. 统一的转换流程

```
数据状态N
    ↓
[拆分器] - 根据规则分析状态，生成任务表
    ↓
任务拆分表
    ↓
[转换器] - 执行任务，修改数据状态
    ↓
数据状态N+1 ← 可继续作为下一个阶段的输入
```

**这个流程可以无限循环**：
```
状态0 → [拆分] → 任务1 → [翻译] → 状态1
                                     ↓
                          状态1 → [拆分] → 任务2 → [CAPS] → 状态2
                                                                ↓
                                                     状态2 → [拆分] → 任务3 → [去重] → 状态3
```

### 💡 核心洞察：DataFrame Pipeline

**整个系统就是一个 DataFrame 的 Pipeline！**

```python
# 所有数据状态都是相同格式的 DataFrame
DataFrame (state 0) == DataFrame (state 1) == DataFrame (state 2) == ...
    ↓                      ↓                      ↓
  相同的列结构          相同的列结构          相同的列结构
  key, CH, EN, ...      key, CH, EN, ...      key, CH, EN, ...
  color_CH, ...         color_CH, ...         color_CH, ...
  comment_CH, ...       comment_CH, ...       comment_CH, ...
```

**关键点**：
- ✅ **格式一致性**：每个处理器的输出必须与输入保持相同的 DataFrame 格式
- ✅ **可级联性**：任何状态都可以作为下一个转换的输入
- ✅ **完整性**：DataFrame 必须包含所有必要信息（数据+元数据）

**示例：翻译处理器**
```python
def translate_processor(input_df: DataFrame) -> DataFrame:
    """
    输入：DataFrame with columns [key, CH, EN, color_CH, color_EN, ...]
    输出：DataFrame with same columns (只修改了EN列和color_EN列的值)
    """
    output_df = input_df.copy()

    # 修改数据列
    output_df.loc[task_idx, 'EN'] = translated_text

    # 修改元数据列（标记为已翻译）
    output_df.loc[task_idx, 'color_EN'] = '#FFD3D3D3'  # 灰色
    output_df.loc[task_idx, 'comment_EN'] = f'原文: {original_text}'

    return output_df  # ✅ 格式与输入完全一致！
```

**示例：大写处理器**
```python
def uppercase_processor(input_df: DataFrame) -> DataFrame:
    """
    输入：DataFrame with columns [key, CH, EN, color_CH, color_EN, ...]
    输出：DataFrame with same columns (只修改了EN列的值)
    """
    output_df = input_df.copy()

    # 修改数据列
    output_df.loc[task_idx, 'EN'] = output_df.loc[task_idx, 'EN'].upper()

    # 元数据列保持不变（或者添加新的注释）
    output_df.loc[task_idx, 'comment_EN'] += ' | CAPS转换'

    return output_df  # ✅ 格式与输入完全一致！
```

**为什么这很重要？**

如果格式不一致（比如用单独的字典存储颜色），就无法级联：
```python
# ❌ 错误：格式不一致
state_1 = {
    'df': DataFrame(...),
    'colors': {...}  # ← 字典格式
}

state_2 = processor(state_1)  # 返回什么格式？如何保证一致性？
```

```python
# ✅ 正确：格式一致
state_1: DataFrame = ...  # 包含所有信息
state_2: DataFrame = processor(state_1)  # 输入输出都是 DataFrame
state_3: DataFrame = another_processor(state_2)  # 可以无限级联
```

## ExcelDataFrame 数据结构设计（重要）

### 设计原则：单一数据源

**核心理念**：Excel的所有信息（数据、颜色、注释）都应该在 DataFrame 中统一管理。

#### ❌ 旧设计（分离存储）

```python
@dataclass
class ExcelDataFrame:
    sheets: Dict[str, pd.DataFrame]  # 只有数据列（如 key, CH, EN）
    color_map: Dict[str, Dict[Tuple[int, int], str]]  # 单独的颜色字典
    comment_map: Dict[str, Dict[Tuple[int, int], str]]  # 单独的注释字典
```

**问题**：
- 数据分散在三个地方，容易失去同步
- 需要手动维护 DataFrame 和字典的一致性
- 查询时需要协调多个数据源
- 违反单一数据源原则

#### ✅ 新设计（统一存储）

```python
@dataclass
class ExcelDataFrame:
    sheets: Dict[str, pd.DataFrame]  # DataFrame 包含所有信息
    filename: str
    excel_id: str

# DataFrame 列结构：
# - 原始数据列：key, CH, EN, TH, PT, VN
# - 颜色列：color_CH, color_EN, color_TH, color_PT, color_VN
# - 注释列：comment_CH, comment_EN, comment_TH, comment_PT, comment_VN
```

**DataFrame 示例**：
```
key              CH         color_CH   comment_CH        EN           color_EN  comment_EN
PET_SKILL_1      强化宠物... #FFFFFF00  格式占位符有误    Enhance...   #FFFFFF00  原文：...
ELEMENT_BOX_2    初阶墨水... None       None             example1     #FFFFFF00  None
```

**优势**：
1. **单一数据源**：所有信息在一个地方，不会失去同步
2. **Pandas 原生操作**：可以用 `df[df['color_EN'] == '#FFFF00']` 直接过滤
3. **代码简洁**：所有操作都是 DataFrame 操作，不需要协调多个数据结构
4. **易于理解**：新手一眼就能看懂数据结构
5. **不易出错**：DataFrame 行操作会自动保持所有列的同步

**列命名约定**：
- 原始数据列：直接使用 Excel 列名（如 `'CH'`, `'EN'`）
- 颜色列：添加 `'color_'` 前缀（如 `'color_CH'`, `'color_EN'`）
- 注释列：添加 `'comment_'` 前缀（如 `'comment_CH'`, `'comment_EN'`）

### 数据访问方式对比

**旧方式（需要协调两个数据源）**：
```python
# 获取单元格值和颜色
df_value = excel_df.sheets['PET'].iloc[0, 1]
color = excel_df.color_map['PET'].get((0, 1))
```

**新方式（单一数据源）**：
```python
# 获取整行数据（包含颜色和注释）
row = excel_df.sheets['PET'].iloc[0]
value = row['CH']
color = row['color_CH']
comment = row['comment_CH']
```

### 为什么这个变化重要？

1. **避免数据不一致**：
   - ❌ 旧设计：DataFrame 更新了但 color_map 忘记更新
   - ✅ 新设计：一次操作同时更新所有相关信息

2. **简化所有下游逻辑**：
   - TaskSplitter：直接从 DataFrame 读取颜色判断任务类型
   - Exporter：直接从 DataFrame 读取颜色和注释导出
   - 不需要在多个数据结构之间查找和匹配

3. **符合数据状态的连续性原则**：
   - 数据状态应该是完整的、自包含的
   - 不应该依赖外部字典来解释数据的含义

## 实现原则

### ✅ 应该做的

1. **所有操作抽象为转换器**
   - LLM翻译是转换
   - CAPS大写是转换
   - 去重是转换
   - 格式化是转换

2. **转换器只关心任务表**
   - 输入：当前数据状态 + 任务表
   - 输出：新的数据状态
   - 不关心数据从哪来、是否是"原始"

3. **拆分器只关心规则**
   - 输入：数据状态 + 拆分规则
   - 输出：任务表
   - 规则可配置、可组合

4. **数据状态独立性**
   - 每个状态都可以独立保存
   - 每个状态都可以独立加载
   - 每个状态都可以作为新流程的起点

### ❌ 不应该做的

1. **不要混淆数据和任务**
   - ❌ 在数据状态中混入任务信息
   - ❌ 在任务表中存储完整数据状态

2. **不要硬编码转换逻辑**
   - ❌ 在拆分器中执行转换
   - ❌ 在转换器中做拆分

3. **不要假设数据来源**
   - ❌ 假设输入一定是"原始文件"
   - ❌ 假设某个字段一定是空的

4. **不要耦合不同阶段**
   - ❌ LLM转换器直接调用CAPS转换
   - ❌ 拆分器依赖特定的转换器

## CAPS转换案例

**正确的实现方式**：

```python
# 阶段1: 翻译
state_0 = load_excel("input.xlsx")
tasks_1 = splitter.split(state_0, rules=[EmptyCell, YellowCell])
state_1 = transformer.execute(state_0, tasks_1, processor=LLM)

# 阶段2: CAPS转换
# 注意：state_1对于这个阶段来说，就是"原始数据"
tasks_2 = splitter.split(state_1, rules=[CapsSheet])
state_2 = transformer.execute(
    state_1,
    tasks_2,
    processor=Uppercase,
    context={'previous_tasks': tasks_1}  # 传递依赖
)
```

**错误的实现方式**：

```python
# ❌ 在拆分阶段就创建CAPS任务
tasks = splitter.split(state_0, rules=[
    NormalTranslation,
    CapsUppercase  # ← 错！此时还没有翻译结果
])

# ❌ LLM翻译器处理CAPS任务
for task in tasks:
    if task['type'] == 'caps':
        # 这里CAPS任务被送到LLM翻译了！
        result = llm.translate(task['source'])
```

## 新增功能开发指南

当需要添加新的数据处理功能时：

### 1. 确定是拆分器还是转换器

**拆分器**：分析数据状态，找出需要处理的位置
- 示例：找出所有空单元格、找出黄色单元格

**转换器**：修改数据内容
- 示例：翻译文本、转大写、去空格

### 2. 定义拆分规则

```python
class MyRule:
    def match(self, data_state):
        """返回符合条件的位置列表"""
        matches = []
        # 扫描数据状态
        for cell in data_state.all_cells():
            if self.condition(cell):
                matches.append(cell.position)
        return matches
```

### 3. 实现处理器

```python
class MyProcessor:
    def process(self, task, context):
        """处理单个任务，返回结果"""
        source = task['source_text']
        result = self.do_something(source)
        return result
```

### 4. 组装到流程中

```python
# 添加新阶段
orchestrator.add_stage(
    splitter_rules=[MyRule()],
    transformer=Transformer(MyProcessor())
)
```

## 文档更新要求

当修改架构时：
1. 更新本文件（ARCHITECTURE_PRINCIPLES.md）
2. 更新CLAUDE.md
3. 更新SIMPLIFIED_ARCHITECTURE.md
4. 添加示例代码

## 违反原则的后果

❌ 不遵循这些原则会导致：
- 代码耦合，难以维护
- 功能冲突，难以扩展
- 逻辑混乱，难以理解
- Bug频发，难以调试

✅ 遵循这些原则的好处：
- 模块独立，易于维护
- 功能清晰，易于扩展
- 逻辑简单，易于理解
- 质量稳定，易于测试

---

**记住：数据状态是连续的，任务表是唯一的中间数据！**
