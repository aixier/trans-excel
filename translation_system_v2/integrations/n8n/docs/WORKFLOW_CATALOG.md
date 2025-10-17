# n8n 工作流目录

本文档详细说明所有预设工作流的功能、配置和使用场景。

---

## 📋 工作流总览

| 工作流 | 文件 | 复杂度 | 适用场景 |
|-------|------|--------|---------|
| 基础翻译 | `01_basic_translation.json` | ⭐ | 单文件手动翻译 |
| 术语表翻译 | `02_translation_with_glossary.json` | ⭐⭐ | 需要术语一致性的翻译 |
| 批量处理 | `03_batch_translation.json` | ⭐⭐⭐ | 定时批量翻译多个文件 |
| 链式处理 | `04_chain_translation_caps.json` | ⭐⭐⭐ | 翻译+大写转换 |
| 定时任务 | `05_scheduled_translation.json` | ⭐⭐⭐⭐ | 每日自动翻译 |
| Webhook触发 | `06_webhook_triggered.json` | ⭐⭐⭐⭐ | 外部系统触发翻译 |
| 条件分支 | `07_conditional_processing.json` | ⭐⭐⭐⭐ | 根据文件特性自动选择策略 |

---

## 🔷 工作流1: 基础翻译

### 文件
`workflows/01_basic_translation.json`

### 功能描述
最简单的翻译流程，适合学习和测试。

### 流程图
```
[手动触发]
    ↓
[读取Excel文件]
    ↓
[上传并拆分任务]
    ↓
[等待拆分完成]
    ↓
[执行翻译]
    ↓
[等待翻译完成]
    ↓
[下载结果文件]
    ↓
[保存到本地]
```

### 节点列表

| 节点名称 | 节点类型 | 说明 |
|---------|---------|------|
| Manual Trigger | manualTrigger | 手动触发 |
| Read File | readBinaryFile | 读取Excel文件 |
| Upload & Split | httpRequest | 上传文件并拆分任务 |
| Poll Split Status | httpRequest | 轮询拆分状态 |
| Execute Translation | httpRequest | 开始执行翻译 |
| Poll Execution Status | httpRequest | 轮询执行状态 |
| Download Result | httpRequest | 下载翻译结果 |
| Save Result | writeBinaryFile | 保存到文件系统 |

### 配置参数

#### 1. Read File节点
```json
{
  "filePath": "/data/input/game.xlsx"
}
```
**修改**: 替换为实际文件路径

#### 2. Upload & Split节点
```json
{
  "method": "POST",
  "url": "http://localhost:8013/api/tasks/split",
  "bodyParameters": {
    "source_lang": "CH",
    "target_langs": "EN,TH",
    "rule_set": "translation"
  }
}
```
**修改**:
- `source_lang`: 源语言
- `target_langs`: 目标语言（逗号分隔）

#### 3. Poll Split Status节点
```json
{
  "options": {
    "repeat": {
      "until": "={{$json.status === 'split_complete'}}",
      "interval": 1000,
      "maxRetries": 300
    }
  }
}
```
**说明**: 每1秒检查一次，最多5分钟

#### 4. Execute Translation节点
```json
{
  "bodyParametersJson": "={\n  \"session_id\": \"{{$json.session_id}}\",\n  \"processor\": \"llm_qwen\",\n  \"max_workers\": 10\n}"
}
```
**修改**:
- `processor`: `llm_qwen` | `llm_openai` | `uppercase`
- `max_workers`: 并发数（1-20）

#### 5. Save Result节点
```json
{
  "fileName": "=result_{{$json.session_id}}.xlsx",
  "dataPropertyName": "data"
}
```
**说明**: 自动使用session_id命名文件

### 使用步骤

1. **导入工作流**
   ```bash
   # 在n8n界面
   Import from File → 选择 01_basic_translation.json
   ```

2. **修改配置**
   - 双击 "Read File" 节点
   - 修改 `filePath` 为你的文件路径
   - 点击 "Save"

3. **执行工作流**
   - 点击 "Execute Workflow"
   - 观察每个节点的执行状态
   - 查看保存的结果文件

### 预期输出

```
/data/output/result_<session_id>.xlsx
```

### 常见问题

**Q1: 文件读取失败**
- 检查文件路径是否正确
- 确认n8n有权限读取该路径

**Q2: API连接失败**
- 确认后端运行在 http://localhost:8013
- 检查Docker网络配置

---

## 🔷 工作流2: 术语表翻译

### 文件
`workflows/02_translation_with_glossary.json`

### 功能描述
在翻译时使用术语表，确保专业术语的翻译一致性。

### 流程图
```
[手动触发]
    ↓
[读取Excel文件]
    ↓
[读取术语表JSON]
    ↓
[检查术语表是否已上传]
    ↓
[IF 不存在] → [上传术语表]
    ↓
[上传并拆分任务]
    ↓
[执行翻译（启用术语表）]
    ↓
[下载结果]
```

### 关键节点

#### Check Glossary节点
```json
{
  "name": "Check Glossary",
  "type": "httpRequest",
  "parameters": {
    "method": "GET",
    "url": "http://localhost:8013/api/glossaries/list"
  }
}
```

#### Upload Glossary节点
```json
{
  "name": "Upload Glossary",
  "type": "httpRequest",
  "parameters": {
    "method": "POST",
    "url": "http://localhost:8013/api/glossaries/upload",
    "sendBinaryData": true,
    "binaryPropertyName": "glossary",
    "bodyParameters": {
      "glossary_id": "terms"
    }
  }
}
```

#### Execute with Glossary节点
```json
{
  "bodyParametersJson": "={\n  \"session_id\": \"{{$json.session_id}}\",\n  \"processor\": \"llm_qwen\",\n  \"glossary_config\": {\n    \"enabled\": true,\n    \"id\": \"terms\"\n  }\n}"
}
```

### 配置参数

**术语表文件路径**:
```json
{
  "filePath": "/data/glossaries/game_terms.json"
}
```

**术语表ID**:
```json
{
  "glossary_id": "game_terms"
}
```

### 使用步骤

1. **准备术语表**
   ```bash
   # 复制示例术语表
   cp examples/glossaries/game_terms.json /data/glossaries/
   ```

2. **导入工作流**
   ```bash
   Import from File → 选择 02_translation_with_glossary.json
   ```

3. **配置路径**
   - 修改Excel文件路径
   - 修改术语表文件路径
   - 确认术语表ID

4. **执行测试**
   - Execute Workflow
   - 检查术语是否正确应用

### 术语表格式

**简化格式**:
```json
{
  "攻击力": "ATK",
  "生命值": "HP",
  "防御力": "DEF"
}
```

**标准格式**:
```json
{
  "id": "game_terms",
  "name": "游戏术语",
  "version": "1.0",
  "terms": [
    {
      "id": "term_001",
      "source": "攻击力",
      "category": "属性",
      "priority": 10,
      "translations": {
        "EN": "ATK",
        "TH": "พลังโจมตี"
      }
    }
  ]
}
```

---

## 🔷 工作流3: 批量处理

### 文件
`workflows/03_batch_translation.json`

### 功能描述
批量处理文件夹中的多个Excel文件，适合大规模翻译任务。

### 流程图
```
[定时触发 / 手动触发]
    ↓
[扫描输入文件夹]
    ↓
[获取所有.xlsx文件列表]
    ↓
[循环: 每个文件]
    ├→ [读取文件]
    ├→ [上传并拆分]
    ├→ [执行翻译]
    ├→ [下载结果]
    └→ [保存到输出文件夹]
    ↓
[收集处理结果]
    ↓
[生成汇总报告]
    ↓
[发送通知邮件]
```

### 关键节点

#### List Files节点
```json
{
  "name": "List Files",
  "type": "executeCommand",
  "parameters": {
    "command": "find /data/input -name '*.xlsx' -type f"
  }
}
```

#### Split in Batches节点
```json
{
  "name": "Loop Files",
  "type": "splitInBatches",
  "parameters": {
    "batchSize": 1,
    "options": {
      "reset": false
    }
  }
}
```

#### Aggregate Results节点
```json
{
  "name": "Aggregate Results",
  "type": "aggregate",
  "parameters": {
    "aggregate": "aggregateAll",
    "options": {}
  }
}
```

### 配置参数

**输入文件夹**:
```json
{
  "command": "find /data/input -name '*.xlsx' -type f"
}
```

**输出文件夹**:
```json
{
  "fileName": "=/data/output/{{$json.original_filename}}_translated.xlsx"
}
```

**批次大小**:
```json
{
  "batchSize": 1  // 每次处理1个文件
}
```

### 使用步骤

1. **准备文件**
   ```bash
   # 将待翻译文件放入输入文件夹
   cp *.xlsx /data/input/
   ```

2. **导入工作流**
   ```bash
   Import from File → 选择 03_batch_translation.json
   ```

3. **配置路径**
   - 修改输入文件夹路径
   - 修改输出文件夹路径

4. **执行**
   - 手动执行: Execute Workflow
   - 定时执行: 激活工作流（Activate）

### 汇总报告格式

```json
{
  "summary": {
    "total_files": 10,
    "successful": 9,
    "failed": 1,
    "total_time_seconds": 3600,
    "failed_files": ["error_file.xlsx"]
  }
}
```

---

## 🔷 工作流4: 链式处理

### 文件
`workflows/04_chain_translation_caps.json`

### 功能描述
先执行翻译，然后对CAPS sheet进行大写转换，适合需要多阶段处理的场景。

### 流程图
```
[上传文件]
    ↓
[阶段1: 翻译]
    ├→ 拆分 (rule_set=translation)
    ├→ 执行 (processor=llm_qwen)
    └→ 保存 session_A
    ↓
[阶段2: 大写转换]
    ├→ 拆分 (parent_session_id=session_A, rule_set=caps_only)
    ├→ 执行 (processor=uppercase)
    └→ 保存 session_B
    ↓
[下载最终结果]
(使用 session_B)
```

### 关键配置

#### Stage 1: Translation
```json
{
  "name": "Split Translation Tasks",
  "parameters": {
    "bodyParameters": {
      "rule_set": "translation",
      "target_langs": "EN"
    }
  }
}
```

#### Stage 2: CAPS
```json
{
  "name": "Split CAPS Tasks",
  "parameters": {
    "bodyParameters": {
      "parent_session_id": "={{$json.session_id}}",  // 使用第一阶段的session_id
      "rule_set": "caps_only"
    }
  }
}
```

### Session传递

```javascript
// Stage 1输出
$json.session_id = "session_A"

// Stage 2使用
parent_session_id = $json.session_id  // "session_A"

// Stage 2输出
$json.session_id = "session_B"

// Download使用
download_session_id = $json.session_id  // "session_B"
```

### 使用场景

**场景1: 游戏本地化**
```
中文 → 英文 → CAPS sheet大写化
```

**场景2: 多语言发布**
```
中文 → [英文, 泰文, 葡萄牙文] → 各语言的CAPS处理
```

---

## 🔷 工作流5: 定时任务

### 文件
`workflows/05_scheduled_translation.json`

### 功能描述
设置定时任务，自动监控文件夹并处理新文件。

### 流程图
```
[定时触发: 每天凌晨2点]
    ↓
[扫描新增文件]
    ↓
[IF 有新文件]
    ├→ YES: [批量处理]
    └→ NO:  [跳过，等待下次]
    ↓
[生成日志]
    ↓
[发送通知]
```

### Schedule配置

#### Cron表达式

```json
{
  "name": "Schedule Trigger",
  "type": "scheduleTrigger",
  "parameters": {
    "rule": {
      "interval": [
        {
          "field": "cronExpression",
          "expression": "0 2 * * *"  // 每天凌晨2点
        }
      ]
    }
  }
}
```

**常用Cron表达式**:

| 表达式 | 说明 |
|-------|------|
| `0 2 * * *` | 每天凌晨2点 |
| `0 */6 * * *` | 每6小时 |
| `0 0 * * 1` | 每周一凌晨 |
| `0 0 1 * *` | 每月1日凌晨 |
| `*/30 * * * *` | 每30分钟 |

### 新文件检测

```bash
# 检查是否有新文件（24小时内）
find /data/input -name '*.xlsx' -type f -mtime -1
```

### 通知配置

#### Slack通知
```json
{
  "name": "Send Slack Notification",
  "type": "slack",
  "parameters": {
    "channel": "#translation-alerts",
    "text": "=Translation completed:\n- Total: {{$json.total}}\n- Success: {{$json.success}}\n- Failed: {{$json.failed}}"
  }
}
```

#### Email通知
```json
{
  "name": "Send Email",
  "type": "emailSend",
  "parameters": {
    "toEmail": "admin@example.com",
    "subject": "Daily Translation Report",
    "text": "=See attached report"
  }
}
```

---

## 🔷 工作流6: Webhook触发

### 文件
`workflows/06_webhook_triggered.json`

### 功能描述
通过Webhook接收外部系统的翻译请求，实现系统间集成。

### 流程图
```
[Webhook接收请求]
    ↓
[解析请求参数]
(file_url, target_langs, callback_url)
    ↓
[从URL下载文件]
    ↓
[上传并翻译]
    ↓
[上传结果到云存储]
    ↓
[回调通知原系统]
(POST to callback_url)
```

### Webhook配置

```json
{
  "name": "Webhook",
  "type": "webhook",
  "parameters": {
    "path": "translate",
    "responseMode": "responseNode",
    "options": {}
  }
}
```

**Webhook URL**: `https://your-n8n.com/webhook/translate`

### 请求格式

```bash
curl -X POST https://your-n8n.com/webhook/translate \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "https://storage.example.com/game.xlsx",
    "target_langs": ["EN", "TH"],
    "glossary_id": "game_terms",
    "callback_url": "https://api.example.com/translation/callback",
    "metadata": {
      "project_id": "proj_123",
      "user_id": "user_456"
    }
  }'
```

### 响应格式

**立即响应** (responseMode: "onReceived"):
```json
{
  "status": "accepted",
  "workflow_id": "workflow_abc",
  "message": "Translation started"
}
```

**完成后响应** (responseMode: "responseNode"):
```json
{
  "status": "completed",
  "session_id": "session_xyz",
  "result_url": "https://storage.example.com/result.xlsx",
  "statistics": {
    "total_tasks": 100,
    "completed": 100,
    "duration_seconds": 120
  }
}
```

### 回调通知

```json
{
  "name": "Callback Notification",
  "type": "httpRequest",
  "parameters": {
    "method": "POST",
    "url": "={{$json.callback_url}}",
    "jsonParameters": true,
    "bodyParametersJson": "={\n  \"status\": \"completed\",\n  \"session_id\": \"{{$json.session_id}}\",\n  \"result_url\": \"{{$json.result_url}}\",\n  \"metadata\": {{JSON.stringify($json.metadata)}}\n}"
  }
}
```

---

## 🔷 工作流7: 条件分支

### 文件
`workflows/07_conditional_processing.json`

### 功能描述
根据文件特性（大小、内容）自动选择最优处理策略。

### 流程图
```
[上传文件]
    ↓
[分析文件]
(获取任务数、Sheet列表)
    ↓
[IF 任务数 < 100]
    ├→ YES: [快速模式]
    │       (max_workers=20, 无术语表)
    └→ NO:  [精确模式]
            (max_workers=5, 启用术语表)
    ↓
[IF 包含CAPS Sheet]
    ├→ YES: [翻译 + 大写]
    └→ NO:  [仅翻译]
    ↓
[下载结果]
```

### IF节点配置

#### 判断任务数量
```json
{
  "name": "Check Task Count",
  "type": "if",
  "parameters": {
    "conditions": {
      "number": [
        {
          "value1": "={{$json.task_count}}",
          "operation": "smaller",
          "value2": 100
        }
      ]
    }
  }
}
```

#### 判断Sheet类型
```json
{
  "name": "Check CAPS Sheet",
  "type": "if",
  "parameters": {
    "conditions": {
      "string": [
        {
          "value1": "={{$json.sheets}}",
          "operation": "contains",
          "value2": "CAPS"
        }
      ]
    }
  }
}
```

### 策略配置

**快速模式**:
```json
{
  "max_workers": 20,
  "glossary_config": null,
  "extract_context": false
}
```

**精确模式**:
```json
{
  "max_workers": 5,
  "glossary_config": {
    "enabled": true,
    "id": "terms"
  },
  "extract_context": true
}
```

---

## 📊 工作流对比

| 特性 | 基础翻译 | 术语表 | 批量处理 | 链式处理 | 定时任务 | Webhook | 条件分支 |
|-----|---------|--------|---------|---------|---------|---------|---------|
| 手动触发 | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| 定时触发 | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| 外部触发 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| 术语表支持 | ❌ | ✅ | 可选 | 可选 | 可选 | ✅ | ✅ |
| 批量处理 | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| 多阶段 | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| 条件分支 | ❌ | 简单 | ❌ | ❌ | ❌ | ❌ | ✅ |
| 通知功能 | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ | 可选 |

---

## 🚀 快速选择指南

### 根据使用场景选择

**场景1: 第一次使用，想快速测试**
→ 使用 **01_basic_translation.json**

**场景2: 需要保证术语翻译一致性**
→ 使用 **02_translation_with_glossary.json**

**场景3: 每天需要处理大量文件**
→ 使用 **03_batch_translation.json** 或 **05_scheduled_translation.json**

**场景4: 需要翻译后自动大写转换**
→ 使用 **04_chain_translation_caps.json**

**场景5: 与其他系统集成**
→ 使用 **06_webhook_triggered.json**

**场景6: 不同文件需要不同策略**
→ 使用 **07_conditional_processing.json**

---

## 📚 下一步

- [实现方案](./IMPLEMENTATION_PLAN.md) - 详细实施步骤
- [Docker部署](./DOCKER_DEPLOYMENT.md) - 生产环境部署
- [故障排除](./TROUBLESHOOTING.md) - 常见问题解决
- [最佳实践](./BEST_PRACTICES.md) - 性能和安全建议

---

**选择合适的工作流，开始你的自动化翻译之旅！** 🚀
