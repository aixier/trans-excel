# 术语表使用说明

## 功能概述

在 **2_execute_transformation.html** 页面中添加了术语表功能，可以在翻译时使用自定义术语表来提高翻译质量和一致性。

---

## 使用步骤

### 1. 打开执行翻译页面

```
file:///D:/work/trans_excel/translation_system_v2/frontend_v2/test_pages/2_execute_transformation.html
```

### 2. 启用术语表

1. 在页面中找到 **"📚 启用术语表（Glossary）"** 复选框
2. 勾选该复选框，展开术语表配置区域

### 3. 上传术语表

**方式1: 上传现有术语文件**

1. 点击 **"📤 上传术语表（JSON格式）"** 文件选择按钮
2. 选择术语表文件（例如：`/mnt/d/work/trans_excel/teach/terms.json`）
3. 系统会自动上传并解析术语表
4. 上传成功后会显示术语数量并自动选中该术语表

**示例术语文件**: `/mnt/d/work/trans_excel/teach/terms.json`

```json
{
    "斗王": "Brawler King",
    "天梯赛": "Ladder Tournament",
    "多重爆头": "Multi-Headshot",
    "破甲弹": "Armor-Piercing"
}
```

**方式2: 选择已有术语表**

1. 点击 **"🔄 刷新术语表列表"** 按钮
2. 从下拉菜单中选择已上传的术语表
3. 每个术语表会显示其包含的术语数量

### 4. 执行翻译

1. 输入Session ID 或 上传Excel文件
2. 选择处理器（建议使用 llm_qwen）
3. 点击 **"🚀 开始执行转换"**
4. 系统会在翻译时自动应用术语表

---

## 术语表格式

### 格式1: 简化格式（推荐用于快速导入）

```json
{
  "术语1": "Translation 1",
  "术语2": "Translation 2",
  "术语3": "Translation 3"
}
```

**特点**：
- 简单易用，适合快速创建
- 自动转换为标准格式
- 优先级默认为5
- 分类默认为"通用"

### 格式2: 标准格式（高级用户）

```json
{
  "id": "my_glossary",
  "name": "我的术语表",
  "description": "游戏术语集合",
  "version": "1.0",
  "languages": ["EN", "TH", "PT"],
  "terms": [
    {
      "id": "term_001",
      "source": "攻击力",
      "category": "属性",
      "priority": 10,
      "translations": {
        "EN": "ATK",
        "TH": "พลังโจมตี",
        "PT": "Ataque"
      }
    }
  ]
}
```

**特点**：
- 支持多语言翻译
- 可设置优先级（1-10，越高优先级越高）
- 支持分类管理
- 完整的元数据

---

## 工作原理

### 1. 术语匹配

翻译时，系统会：
1. 扫描原文，查找匹配的术语
2. 按术语长度排序（避免部分匹配）
3. 按优先级排序结果

### 2. 提示词注入

匹配到的术语会被注入到翻译提示词中：

```
相关游戏术语（请严格使用以下翻译）:
- 攻击力 → ATK
- 生命值 → HP
- 防御力 → DEF

原文：提升攻击力10%
```

### 3. LLM 翻译

LLM 根据提示词中的术语进行翻译：

```
输入: 提升攻击力10%
输出: Increase ATK by 10%  ✅
```

---

## 最佳实践

### 1. 术语优先级设置

- **10**: 核心术语（攻击力、生命值）
- **9**: 常用术语（等级、技能）
- **8**: 次要术语（背包、任务）
- **5**: 默认优先级
- **1-4**: 低优先级

### 2. 术语长度规则

优先匹配长术语：
- ✅ 先匹配 "暴击伤害"
- ❌ 再匹配 "伤害"

避免部分匹配问题。

### 3. 多语言支持

在一个术语表中支持多个目标语言：

```json
{
  "source": "攻击力",
  "translations": {
    "EN": "ATK",
    "TH": "พลังโจมตี",
    "PT": "Ataque",
    "VN": "Sức công"
  }
}
```

### 4. 分类管理

建议按功能分类：
- 属性（攻击力、防御力）
- 系统（等级、经验值）
- 战斗（技能、装备）
- 货币（金币、钻石）

---

## 测试示例

### 完整测试流程

1. **准备术语表文件** (`/mnt/d/work/trans_excel/teach/terms.json`)

2. **打开页面并上传术语表**
   ```
   file:///D:/work/trans_excel/.../2_execute_transformation.html
   → 勾选"启用术语表"
   → 上传 terms.json
   → 确认显示 "28个术语"
   ```

3. **上传测试Excel**
   ```
   包含术语的文本：
   - "提升多重爆头伤害"
   - "破甲弹威力提升"
   - "斗王称号获得"
   ```

4. **执行翻译**
   ```
   Processor: llm_qwen
   启用术语表: ✅ terms
   ```

5. **验证结果**
   ```
   ✅ "多重爆头" → "Multi-Headshot"
   ✅ "破甲弹" → "Armor-Piercing"
   ✅ "斗王" → "Brawler King"
   ```

---

## API 对应关系

### 前端操作 → 后端API

| 操作 | API端点 | 请求体 |
|-----|---------|--------|
| 上传术语表 | `POST /api/glossaries/upload` | FormData(file, glossary_id) |
| 列出术语表 | `GET /api/glossaries/list` | - |
| 获取术语表详情 | `GET /api/glossaries/{id}` | - |
| 执行翻译（带术语） | `POST /api/execute/start` | `{glossary_config: {enabled: true, id: "xxx"}}` |

### 请求示例

```json
{
  "session_id": "uuid",
  "processor": "llm_qwen",
  "max_workers": 10,
  "glossary_config": {
    "enabled": true,
    "id": "terms"
  }
}
```

---

## 常见问题

### Q1: 术语表上传后在哪里？

**A**: 存储在后端 `/data/glossaries/` 目录，文件名为 `{glossary_id}.json`

### Q2: 可以上传多个术语表吗？

**A**: 可以！每次翻译只能选择一个术语表使用。

### Q3: 术语表会影响翻译质量吗？

**A**: 会提升质量！特别是专业术语和游戏特定词汇的翻译一致性。

### Q4: 不启用术语表会怎样？

**A**: 正常翻译，但LLM会根据上下文自由翻译，可能不一致。

### Q5: 术语表支持中文到中文吗？

**A**: 支持！例如简体到繁体，或者标准化某些表达。

---

## 故障排除

### 问题1: 上传术语表失败

**原因**: JSON格式错误

**解决**:
1. 使用在线JSON验证器检查格式
2. 确保使用UTF-8编码
3. 检查是否有尾随逗号

### 问题2: 术语没有生效

**原因**:
- 术语表未正确选择
- 原文中没有匹配的术语

**解决**:
1. 确认勾选了"启用术语表"
2. 确认选择了正确的术语表
3. 查看控制台日志确认术语表ID

### 问题3: 某些术语没有匹配

**原因**:
- 原文和术语表中的文本不完全一致
- 有空格或特殊字符差异

**解决**:
1. 确保术语表中的source文本与原文完全匹配
2. 检查是否有额外的空格或标点符号

---

## 技术细节

### 术语匹配算法

```python
# 后端 glossary_manager.py
def match_terms_in_text(source_text, glossary, target_lang):
    # 1. 按术语长度降序排序
    sorted_terms = sorted(terms, key=lambda t: len(t['source']), reverse=True)

    # 2. 逐个匹配，记录已匹配位置
    for term in sorted_terms:
        pos = source_text.find(term['source'])
        if pos != -1 and not overlaps:
            matched_terms.append(term)

    # 3. 按优先级排序
    return sorted(matched_terms, key=lambda x: x['priority'], reverse=True)
```

### 提示词注入位置

```
翻译请求：...

相关游戏术语（请严格使用以下翻译）:  ← 术语注入点
- 术语1 → Translation 1
- 术语2 → Translation 2

翻译要求：  ← 原有翻译要求
1. 保持游戏术语的一致性
2. ...
```

---

## 更新日志

**v1.0** (2025-10-17)
- ✅ 添加术语表上传功能
- ✅ 添加术语表列表显示
- ✅ 添加术语表启用开关
- ✅ 集成到执行翻译流程
- ✅ 支持简化格式和标准格式
- ✅ 自动刷新和自动选中
- ✅ 状态反馈和错误处理

---

## 下一步优化方向

- [ ] 术语表在线编辑器
- [ ] 术语表预览功能
- [ ] 术语匹配高亮显示
- [ ] 术语使用统计
- [ ] 术语表导入/导出Excel格式
- [ ] 术语表合并功能
