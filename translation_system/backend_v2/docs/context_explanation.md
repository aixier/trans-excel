# 上下文提取功能说明

## 什么是"上下文"？

**上下文（Context）** 是指翻译时提供给LLM的**辅助信息**，帮助模型更准确地理解文本含义和翻译风格。

---

## 提取的6类上下文

### 1. 游戏信息（Game Context）
从GameInfo中获取的全局信息：
```
[Game] Game: MyRPG | Genre: RPG | Platform: Mobile | Style: Fantasy
```

**作用**：让翻译符合游戏类型和风格

---

### 2. 单元格注释（Comment）
Excel单元格中的批注信息：
```
[Comment] 这是主菜单的标题文本，需要简短有力
```

**作用**：提供人工标注的翻译要求

---

### 3. 列标题（Column Header）
列名信息：
```
[Column] EN  或  [Column] Item_Description
```

**作用**：说明这是什么类型的列（语言、描述、名称等）

---

### 4. 相邻单元格信息（Neighbor Context）

#### 4a. 上一行分类标题
```
[Category] Weapon Skills
```
如果上一行是全大写或以冒号结尾，识别为分类标题

#### 4b. 行标签（第一列）
```
[Row Label] SWORD_001  或  [Row Label] NPC_Elder_01
```

**作用**：提供该行的ID或标识，帮助理解内容类型

---

### 5. 内容特征推断（Content Context）

#### 5a. 长度判断
- `[Type] Short text/UI element` - ≤10字符，UI按钮
- `[Type] Medium text/Menu item` - ≤30字符，菜单项
- `[Type] Description text` - ≤100字符，描述文本
- `[Type] Long text/Dialog` - >100字符，对话文本

#### 5b. 格式特征
- `[Format] Question` - 以问号结尾
- `[Format] Exclamation` - 以感叹号结尾
- `[Format] Multi-line text` - 包含换行符
- `[Format] Contains variables` - 包含 `{变量}`
- `[Format] Contains percentage` - 包含百分号
- `[Format] Contains numbers` - 包含数字

**作用**：帮助LLM保持原文格式和语气

---

### 6. 表格类型（Sheet Context）
根据Sheet名称推断类型：
- `[Sheet Type] UI/Interface text` - UI、interface
- `[Sheet Type] Dialog/Conversation` - dialog、dialogue
- `[Sheet Type] Item descriptions` - item
- `[Sheet Type] Skills/Abilities` - skill、ability
- `[Sheet Type] NPC related` - npc
- `[Sheet Type] Quest/Mission text` - quest、mission
- `[Sheet Type] Tutorial/Help text` - tutorial、help

**作用**：提供整体内容类型，指导翻译风格

---

## 实际使用示例

### 示例1：UI按钮
```
源文本: "Start Game"

提取的上下文:
[Game] Game: MyRPG | Genre: RPG | Platform: Mobile |
[Column] EN |
[Row Label] BTN_MAIN_001 |
[Type] Short text/UI element |
[Sheet Type] UI/Interface text

发送给LLM的Prompt:
请将以下英文翻译成土耳其语：
- 源文本: "Start Game"
- 上下文: [Game] Game: MyRPG | Genre: RPG | Platform: Mobile | [Column] EN | [Row Label] BTN_MAIN_001 | [Type] Short text/UI element | [Sheet Type] UI/Interface text

翻译结果: "Oyuna Başla" (符合游戏UI简短风格)
```

---

### 示例2：NPC对话
```
源文本: "Welcome to our village! Are you a traveler?"

提取的上下文:
[Game] Game: MyRPG | Genre: RPG | Platform: Mobile |
[Column] EN |
[Category] Village Elder |
[Row Label] NPC_ELDER_GREETING_01 |
[Type] Long text/Dialog |
[Format] Question |
[Sheet Type] Dialog/Conversation

发送给LLM的Prompt:
请将以下英文翻译成土耳其语：
- 源文本: "Welcome to our village! Are you a traveler?"
- 上下文: [Game] Game: MyRPG... [Category] Village Elder... [Format] Question...

翻译结果: "Köyümüze hoş geldiniz! Bir gezgin misiniz?"
(保持了友好的对话语气和疑问句格式)
```

---

### 示例3：带变量的物品描述
```
源文本: "Increases attack by {value}%"

提取的上下文:
[Game] Game: MyRPG | Genre: RPG | Platform: Mobile |
[Column] EN |
[Row Label] BUFF_ATK_001 |
[Type] Medium text/Menu item |
[Format] Contains variables |
[Format] Contains percentage |
[Sheet Type] Item descriptions

翻译结果: "Saldırıyı %{value} artırır"
(保留了变量占位符{value}，正确处理了百分号位置)
```

---

## 上下文的作用

### ✅ 开启上下文提取的好处

1. **提高翻译准确性**
   - 理解文本所属类型（UI、对话、描述等）
   - 保持游戏风格一致性

2. **保持格式正确**
   - 识别变量占位符 `{value}`，避免被翻译
   - 保持特殊符号（%、!、?）的位置

3. **理解语境**
   - 知道是哪个NPC的对话
   - 明确是按钮、标题还是描述

4. **优化翻译风格**
   - 短文本翻译简洁
   - 对话文本保持口语化
   - UI文本符合界面习惯

---

### ❌ 关闭上下文提取的影响

**速度提升**：5-10倍
**质量影响**：
- ✅ 大部分简单文本仍能正确翻译（依赖LLM自身能力）
- ⚠️ 可能丢失特定风格要求
- ⚠️ 可能不理解特殊格式要求
- ⚠️ 缺少游戏整体背景信息

**适用场景**：
- 快速预览和测试
- 简单的UI文本翻译（按钮、标签）
- 大批量初步翻译，后期人工校对
- 超大文件（10000+行）初次拆分查看统计

---

## 性能对比

| 文件大小 | 开启上下文 | 关闭上下文 | 速度提升 |
|---------|-----------|-----------|---------|
| 1000行 | 10秒 | 3秒 | 3.3倍 |
| 6000行 | 25秒 | 7秒 | 3.6倍 |
| 6000行 | 68秒（旧版）| 7秒（优化）| **9.7倍** |

---

## 使用建议

### 🟢 建议开启上下文

- ✅ 正式生产环境翻译
- ✅ 游戏对话、剧情等需要语境的内容
- ✅ 包含大量变量和特殊格式的文本
- ✅ 首次翻译新项目
- ✅ 质量要求高的内容

### 🟡 可以关闭上下文

- 📊 快速查看文件统计信息
- 🧪 测试拆分流程
- 🔄 重复拆分相同文件
- 📝 简单的UI文本（按钮、标签）
- 🚀 超大文件（10000+行）快速预处理
- 📦 批量处理大量文件

---

## 配置方法

### API请求
```json
POST /api/tasks/split
{
  "session_id": "xxx",
  "source_lang": "EN",
  "target_langs": ["TR", "TH"],
  "extract_context": false  // false=关闭，true=开启（默认）
}
```

### 前端界面
```
☑ 提取上下文信息（更准确但较慢）
💡 大文件时可关闭此选项以提升5-10倍速度
```

---

## 代码实现

上下文提取核心代码：
- `services/context_extractor.py` - 提取逻辑
- `services/task_splitter.py:398-404` - 可选调用

关闭时的行为：
```python
if self.extract_context and self.context_extractor:
    source_context = self.context_extractor.extract_context(...)
else:
    source_context = ""  # 快速模式，不提取
```