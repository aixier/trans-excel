# 功能：自动检测目标语言

## 📋 功能概述

**更新日期**: 2025-10-17

系统现在支持 **不填写目标语言时自动检测所有空白列** 作为目标语言。

## ✨ 主要改进

### 1. 前端 UI 改进

**文件**: `frontend_v2/js/pages/unified-workflow-page.js`

**变更**:
- 目标语言输入框默认值改为 **空字符串**（之前是 `"EN"`）
- 添加提示文本：`"可选，留空自动检测"`
- Placeholder: `"留空=自动检测所有空白列，或输入：EN,TH,TW"`

**UI 显示**:
```html
<label class="label">
  <span class="label-text">Target Languages</span>
  <span class="label-text-alt text-gray-500">可选，留空自动检测</span>
</label>
<input type="text" id="targetLangs" value=""
       placeholder="留空=自动检测所有空白列，或输入：EN,TH,TW" />
```

### 2. 前端逻辑改进

**阶段1（文件上传）**:
```javascript
// 获取目标语言（可选，如果为空则自动检测所有空白列）
const targetLangsInput = document.getElementById('targetLangs').value.trim();
const formData = new FormData();
formData.append('file', this.file);

// 只有当用户填写了目标语言时才传递该参数
if (targetLangsInput) {
  const targetLangs = targetLangsInput.split(',')
    .map(s => s.trim())
    .filter(s => s.length > 0);
  if (targetLangs.length > 0) {
    formData.append('target_langs', JSON.stringify(targetLangs));
  }
}
// 如果不传 target_langs，后端会自动检测所有空白列
```

**阶段3（CAPS转换）**:
```javascript
// 拆分CAPS任务 - 目标语言可选（如果不传则自动继承父Session）
const splitFormData = new FormData();
splitFormData.append('parent_session_id', parentSessionId);

// 只有当用户填写了目标语言时才传递该参数
const targetLangsInput = document.getElementById('targetLangs').value.trim();
if (targetLangsInput) {
  const targetLangs = targetLangsInput.split(',')
    .map(s => s.trim())
    .filter(s => s.length > 0);
  if (targetLangs.length > 0) {
    splitFormData.append('target_langs', JSON.stringify(targetLangs));
  }
}
// 如果不传 target_langs，后端会自动从父Session继承
```

### 3. 后端逻辑改进

**文件**: `backend_v2/api/task_api.py`

**Mode A（文件上传）- 已有逻辑**:
```python
# Line 144-146
if not target_langs_list and analysis_result.get('language_detection'):
    lang_detection = analysis_result['language_detection']
    target_langs_list = lang_detection.get('suggested_config', {}).get('target_langs', [])
```

**Mode B（继承父Session）- 新增逻辑**:
```python
# Line 203-208
# Auto-inherit target_langs from parent if not provided
if not target_langs_list and parent.metadata.get('analysis'):
    lang_detection = parent.metadata['analysis'].get('language_detection', {})
    target_langs_list = lang_detection.get('suggested_config', {}).get('target_langs', [])
    if target_langs_list:
        logger.info(f"Auto-inherited target_langs from parent: {target_langs_list}")
```

**错误消息改进**:
```python
# Line 213-214
if not target_langs_list:
    raise HTTPException(
        status_code=400,
        detail="target_langs is required and could not be auto-detected"
    )
```

## 🎯 使用场景

### 场景1: 完全自动检测（推荐）

**操作**:
1. 上传 Excel 文件
2. **目标语言输入框留空**
3. 点击"开始工作流"

**系统行为**:
- 自动分析 Excel 文件
- 检测所有空白列（例如：EN, TH, TW）
- 生成对应的翻译任务

**优势**:
- ✅ 零配置，开箱即用
- ✅ 自动适应不同的 Excel 文件结构
- ✅ 避免遗漏翻译列

### 场景2: 手动指定目标语言

**操作**:
1. 上传 Excel 文件
2. **输入目标语言**: `EN,TH` （只翻译这两列）
3. 点击"开始工作流"

**系统行为**:
- 只处理指定的语言列
- 忽略其他空白列

**优势**:
- ✅ 精确控制翻译范围
- ✅ 节省处理时间和 LLM 调用费用
- ✅ 适合增量翻译场景

### 场景3: CAPS阶段自动继承

**操作**:
1. 阶段1-2: 留空目标语言（自动检测到 EN, TH, TW）
2. 阶段3: 同样留空

**系统行为**:
- CAPS 阶段自动继承父 Session 的目标语言配置
- 无需重复输入

**优势**:
- ✅ 一致性保证
- ✅ 减少用户操作
- ✅ 避免配置错误

## 🔍 自动检测逻辑

后端通过 `ExcelAnalyzer` 分析文件时：

1. **检测列名模式**:
   ```
   key | CH | EN | TH | TW | PT | VN
   ```

2. **识别空白列**:
   - 列存在但没有翻译内容
   - 或列标题存在，但数据为空

3. **生成建议配置**:
   ```python
   {
     "language_detection": {
       "suggested_config": {
         "source_lang": "CH",
         "target_langs": ["EN", "TH", "TW", "PT", "VN"]
       }
     }
   }
   ```

4. **存储到 Session metadata**:
   ```python
   session.metadata['analysis'] = analysis_result
   ```

## 📊 对比表

| 特性 | 旧版本 | 新版本 |
|------|--------|--------|
| **默认值** | `"EN"` | `""` (空字符串) |
| **必填性** | 必填 | 可选 |
| **文件上传** | 必须手动输入 | 自动检测或手动输入 |
| **CAPS继承** | 必须手动输入 | 自动继承或手动输入 |
| **错误提示** | `target_langs is required` | `target_langs is required and could not be auto-detected` |
| **用户体验** | 需要了解文件结构 | 零配置即可使用 |

## ⚠️ 注意事项

### 1. 自动检测失败的情况

如果系统无法自动检测目标语言（例如：非标准的 Excel 格式），会返回错误：

```json
{
  "detail": "target_langs is required and could not be auto-detected"
}
```

**解决方法**: 手动输入目标语言

### 2. 性能考虑

自动检测所有空白列可能会：
- 生成更多翻译任务
- 消耗更多 LLM API 调用
- 增加处理时间

**建议**:
- 对于大型文件或费用敏感场景，建议手动指定需要翻译的列
- 对于小型文件或探索性场景，使用自动检测更方便

### 3. CAPS 阶段特殊情况

如果阶段1使用了手动指定的目标语言，阶段3会自动继承这些语言。如果需要不同的目标语言，需要在阶段3重新指定。

## 🧪 测试验证

### 测试用例1: 空白自动检测

```bash
# 不传 target_langs 参数
curl -X POST 'http://localhost:8013/api/tasks/split' \
  -F 'file=@test.xlsx' \
  -F 'rule_set=translation'

# 预期: 自动检测所有空白列
# 响应: session_id 和成功消息
```

### 测试用例2: 手动指定

```bash
# 传递 target_langs 参数
curl -X POST 'http://localhost:8013/api/tasks/split' \
  -F 'file=@test.xlsx' \
  -F 'target_langs=["EN","TH"]' \
  -F 'rule_set=translation'

# 预期: 只处理 EN 和 TH 列
```

### 测试用例3: CAPS 自动继承

```bash
# 第一阶段：留空 target_langs
curl -X POST 'http://localhost:8013/api/tasks/split' \
  -F 'file=@test.xlsx' \
  -F 'rule_set=translation'

# 获取 session_id: xxx

# 第三阶段：不传 target_langs，自动继承
curl -X POST 'http://localhost:8013/api/tasks/split' \
  -F 'parent_session_id=xxx' \
  -F 'rule_set=caps_only'

# 预期: 自动继承父 Session 的 target_langs
```

## 📝 API 文档更新

### POST /api/tasks/split

**参数变更**:

| 参数 | 类型 | 旧版本 | 新版本 | 说明 |
|------|------|--------|--------|------|
| `target_langs` | JSON字符串 | 必填 | **可选** | 目标语言数组，例如 `["EN","TH"]`<br>**如果不传**: Mode A 自动检测空白列，Mode B 自动继承父 Session |

**示例**:

```javascript
// 自动检测（推荐）
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('rule_set', 'translation');
// 不传 target_langs

// 手动指定
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('target_langs', '["EN","TH","TW"]');
formData.append('rule_set', 'translation');
```

## 🎉 总结

这次改进让系统更加智能和易用：

✅ **零配置上手**: 新用户无需了解 Excel 结构，直接上传即可
✅ **灵活性**: 高级用户可以精确控制翻译范围
✅ **一致性**: CAPS 阶段自动继承配置，避免不一致
✅ **更好的错误提示**: 当自动检测失败时，给出明确的错误信息

---

**相关文件**:
- `frontend_v2/js/pages/unified-workflow-page.js` (前端)
- `backend_v2/api/task_api.py` (后端 API)
- `backend_v2/services/excel_analyzer.py` (分析器)
