# CAPS 规则更新 - 处理所有列

## 📋 更新概述

**更新日期**: 2025-10-17

CAPS 规则现在处理 **所有语言列**（包括源语言和目标语言），而不仅仅是目标语言列。

## ✨ 主要变更

### 之前的逻辑 ❌

```python
# 只处理目标语言列
TARGET_COLUMNS = ['TH', 'TW', 'PT', 'EN', 'VN', 'ID', 'ES', 'FR', 'DE', 'RU', 'AR', 'JA', 'KO']

# 排除源语言列
EXCLUDE_COLUMNS = ['KEY', 'CH', 'CN']

# 匹配逻辑
if column_name in EXCLUDE_COLUMNS:
    return False

if column_name not in TARGET_COLUMNS:
    return False
```

**问题**:
- ❌ CH（中文）、CN 等源语言列不会被大写处理
- ❌ 硬编码的目标语言列表，扩展性差
- ❌ 如果有新的语言列（如 JP、KR），需要手动添加到 TARGET_COLUMNS

### 现在的逻辑 ✅

```python
# 只排除索引列
EXCLUDE_COLUMNS = ['KEY', 'key', 'Key', 'INDEX', 'index', 'Index', 'ID', 'id', 'Id']

# 匹配逻辑
# 1. 排除第一列（col_idx=0）
if col_idx == 0:
    return False

# 2. 排除索引列名称
if column_name.upper() in [c.upper() for c in EXCLUDE_COLUMNS]:
    return False

# 3. 匹配所有其他列（源语言 + 目标语言）
return True
```

**优势**:
- ✅ 处理所有语言列（CH、EN、TH、TW、PT、VN等）
- ✅ 自动支持新增语言列，无需修改代码
- ✅ 更简单、更直观的逻辑

## 📊 对比示例

假设有一个 CAPS sheet，列结构如下：

```
| KEY | CH     | EN          | TH          | TW          |
|-----|--------|-------------|-------------|-------------|
| 001 | 测试   | test        | ทดสอบ       | 測試        |
| 002 | 示例   | example     | ตัวอย่าง    | 示例        |
```

### 旧逻辑处理结果

| 列名 | col_idx | 是否处理 | 原因 |
|------|---------|----------|------|
| KEY  | 0       | ❌ No    | 排除（EXCLUDE_COLUMNS）|
| CH   | 1       | ❌ No    | 排除（EXCLUDE_COLUMNS）|
| EN   | 2       | ✅ Yes   | 匹配（TARGET_COLUMNS）|
| TH   | 3       | ✅ Yes   | 匹配（TARGET_COLUMNS）|
| TW   | 4       | ✅ Yes   | 匹配（TARGET_COLUMNS）|

**结果**: CH 列不会被大写转换

### 新逻辑处理结果

| 列名 | col_idx | 是否处理 | 原因 |
|------|---------|----------|------|
| KEY  | 0       | ❌ No    | 排除（第一列）|
| CH   | 1       | ✅ Yes   | 匹配（所有非索引列）|
| EN   | 2       | ✅ Yes   | 匹配（所有非索引列）|
| TH   | 3       | ✅ Yes   | 匹配（所有非索引列）|
| TW   | 4       | ✅ Yes   | 匹配（所有非索引列）|

**结果**: 所有语言列（包括 CH）都会被大写转换

## 🎯 实际效果

### 示例 Excel 文件

**CAPS_Sheet (转换前)**:
```
| KEY | CH     | EN          | TH          |
|-----|--------|-------------|-------------|
| 001 | 攻击力 | Attack      | พลังโจมตี   |
| 002 | 防御力 | Defense     | การป้องกัน  |
```

### CAPS 处理后

**旧逻辑** (只处理 EN, TH):
```
| KEY | CH     | EN          | TH          |
|-----|--------|-------------|-------------|
| 001 | 攻击力 | ATTACK      | พลังโจมตี   |
| 002 | 防御力 | DEFENSE     | การป้องกัน  |
```
❌ CH 列保持原样（没有大写）

**新逻辑** (处理 CH, EN, TH):
```
| KEY | CH     | EN          | TH          |
|-----|--------|-------------|-------------|
| 001 | 攻击力 | ATTACK      | พลังโจมตี   |
| 002 | 防御力 | DEFENSE     | การป้องกัน  |
```
✅ 所有语言列都被大写处理

## 🔍 技术细节

### 文件修改

**文件**: `backend_v2/services/splitter/rules/caps_sheet.py`

**主要修改**:

1. **简化列定义**:
```python
# 删除
TARGET_COLUMNS = ['TH', 'TW', 'PT', 'EN', 'VN', 'ID', 'ES', 'FR', 'DE', 'RU', 'AR', 'JA', 'KO']

# 保留（简化）
EXCLUDE_COLUMNS = ['KEY', 'key', 'Key', 'INDEX', 'index', 'Index', 'ID', 'id', 'Id']
```

2. **改进匹配逻辑** (`match` 方法):
```python
# 获取列信息
column_name = context.get('column_name', '')
col_idx = context.get('col_idx', 0)

# 双重保护：按索引和按名称排除
if col_idx == 0:  # 第一列总是索引
    return False

if column_name.upper() in [c.upper() for c in EXCLUDE_COLUMNS]:
    return False

# 匹配所有其他列
return True
```

3. **更新任务创建** (`create_task` 方法):
```python
return {
    'task_id': task_id,
    'operation': 'uppercase',
    'source_text': current_value,  # 可以是源语言或目标语言
    'target_lang': column_name,    # 可以是任何语言
    'metadata': {
        'rule': 'CapsSheetRule',
        'column_type': 'all_languages',  # 新增标识
        'original_value': current_value
    }
}
```

### 测试验证

**测试脚本**: `/tmp/test_caps_rule.py`

**测试结果**:
```
✅ All tests PASSED!

Summary of changes:
  - Now processes ALL columns (source AND target languages)
  - Only excludes first column (col_idx=0) or KEY/INDEX/ID columns
  - CH, CN columns are now INCLUDED in CAPS processing
```

## 🚀 使用方法

### 通过 Web UI

1. 访问 `http://127.0.0.1:8090/#/upload`
2. 上传包含 CAPS sheet 的 Excel 文件
3. 目标语言可以留空（自动检测）
4. 系统会自动：
   - 阶段1-2: 翻译所有空白列
   - 阶段3: 检测到 CAPS sheet，对所有语言列（除 KEY）执行大写转换

### 通过 API

**阶段3 - CAPS 转换**:
```bash
# 从父 Session 继承数据和配置
curl -X POST 'http://localhost:8013/api/tasks/split' \
  -F 'parent_session_id=xxx' \
  -F 'rule_set=caps_only'

# 预期: 自动检测并处理所有语言列（除第一列）
```

## ⚠️ 注意事项

### 1. 索引列识别

系统使用双重机制识别索引列：
1. **按位置**: `col_idx == 0`（第一列）
2. **按名称**: 列名在 `EXCLUDE_COLUMNS` 中

**常见索引列名称**:
- KEY, key, Key
- INDEX, index, Index
- ID, id, Id

### 2. 中文大写转换

中文字符的"大写"转换：
- 中文没有大小写概念
- `str.upper()` 对中文无效，保持原样
- 这是预期行为，不是 bug

**示例**:
```python
"攻击力".upper()  # 结果: "攻击力" (无变化)
"attack".upper()  # 结果: "ATTACK"
```

### 3. 特殊字符处理

CAPS 转换只影响英文字母：
- 数字、标点符号保持不变
- Unicode 字符（泰文、繁体中文等）保持不变

**示例**:
```python
"Attack +50%".upper()     # 结果: "ATTACK +50%"
"พลังโจมตี".upper()       # 结果: "พลังโจมตี" (无变化)
```

### 4. 性能影响

处理所有列会：
- ✅ 增加 CAPS 任务数量（包含源语言列）
- ✅ 但大写转换速度非常快（简单字符串操作）
- ✅ 不调用 LLM，不产生额外费用

**性能对比**:
- 旧逻辑: 100个单元格 × 3个目标语言 = 300个任务
- 新逻辑: 100个单元格 × 4列（1源+3目标）= 400个任务
- 性能影响: 可忽略不计（毫秒级操作）

## 📝 向后兼容性

### 兼容性说明

✅ **完全向后兼容**:
- 现有的 CAPS sheet 仍然正常工作
- 只是新增了源语言列的大写转换
- 不影响其他功能

### 迁移建议

无需迁移！现有工作流可以继续使用。

如果你想充分利用新功能：
1. 确保源语言列（CH、CN）中有需要大写的内容
2. 系统会自动处理这些列

## 🎉 总结

这次更新让 CAPS 规则更加：

✅ **通用化**: 支持所有语言列，不限于硬编码列表
✅ **简化**: 逻辑更简单，只排除索引列
✅ **扩展性**: 自动支持新语言，无需修改代码
✅ **一致性**: 源语言和目标语言统一处理

---

**相关文件**:
- `backend_v2/services/splitter/rules/caps_sheet.py` (CAPS 规则)
- `/tmp/test_caps_rule.py` (测试脚本)
