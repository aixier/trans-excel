# 工作流更新日志

## 2025-01-17: 修复完整版翻译工作流

### 工作流信息

- **名称**: Web Form Translation (网页表单翻译)
- **ID**: `1xQAR3UTNGrk0X6B`
- **文件**: `08_web_form_translation.json`

### 问题描述

原工作流存在以下问题：

1. ❌ **包含 2 个 Respond to Webhook 节点**
   - "Return Success" (respond-1)
   - "Return Error" (respond-2)

2. ❌ **"Return Error" 节点未连接**（孤立节点）

3. ❌ **触发错误**: `"Unused Respond to Webhook node found in the workflow"`

4. ❌ **表单无法访问**: 返回 "Problem loading form"

### 根本原因

根据 [n8n GitHub Issue #12371](https://github.com/n8n-io/n8n/issues/12371):

> **Form Trigger 不能与 Respond to Webhook 节点一起使用**

这是 n8n 在新版本中的设计变更。Form Trigger 已经内置了响应功能，不需要也不允许使用额外的 Respond to Webhook 节点。

### 解决方案

#### 1. 移除 Respond to Webhook 节点

**删除的节点**:
- ❌ "Return Success" (type: n8n-nodes-base.respondToWebhook)
- ❌ "Return Error" (type: n8n-nodes-base.respondToWebhook)

从 14 个节点减少到 13 个节点。

#### 2. 配置 Form Trigger 使用内置响应

**修改前**:
```json
{
  "responseMode": "onReceived",
  "formSubmittedText": "翻译任务已提交..."
}
```

**修改后**:
```json
{
  "path": "translation",
  "responseMode": "lastNode",
  "respondWith": "json",
  "responseBody": "={{ $json }}"
}
```

**关键变化**:
- ✅ 添加了 `path: "translation"` 参数
- ✅ `responseMode` 改为 `"lastNode"` (等待工作流完成)
- ✅ 添加了 `respondWith: "json"` (返回 JSON)
- ✅ 添加了 `responseBody: "={{ $json }}"` (使用最后节点的输出)
- ✅ `typeVersion` 从 1 升级到 2

#### 3. 添加响应格式化节点

在工作流末尾添加了新节点：

**Format Response** (code-response):
```javascript
// 格式化最终响应
const sessionId = $('Upload & Split Tasks').item.json.session_id;
const fileName = $json.fileName;

return {
  json: {
    success: true,
    message: "✅ 翻译完成！",
    session_id: sessionId,
    file_name: fileName,
    download_url: `http://localhost:8013/api/download/${sessionId}`,
    tips: "文件已保存，可以通过 download_url 下载"
  }
};
```

**作用**: 格式化最终响应数据，Form Trigger 会自动使用这个输出作为响应。

#### 4. 更新节点连接

**修改前**:
```
Save Result File → Return Success
                 → Return Error (未连接)
```

**修改后**:
```
Save Result File → Format Response
```

### 工作流结构

#### 修复后的节点列表 (13 个节点)

1. **Translation Form** - Form Trigger (入口)
2. **Process Form Data** - Code (处理表单数据)
3. **Upload & Split Tasks** - HTTP Request (上传文件并拆分)
4. **Poll Split Status** - HTTP Request (轮询拆分状态)
5. **Check Split Complete** - If (检查拆分完成)
6. **Wait 2s** - Wait (等待 2 秒)
7. **Execute Translation** - HTTP Request (执行翻译)
8. **Poll Execution Status** - HTTP Request (轮询执行状态)
9. **Check Execution Complete** - If (检查执行完成)
10. **Wait 5s** - Wait (等待 5 秒)
11. **Download Result** - HTTP Request (下载结果)
12. **Save Result File** - Write Binary File (保存文件)
13. **Format Response** - Code (格式化响应) ⭐ 新增

#### 节点连接流程

```
Translation Form
    ↓
Process Form Data
    ↓
Upload & Split Tasks
    ↓
Poll Split Status ←──┐
    ↓                │
Check Split Complete │
    ↓           ↓    │
    ✓           ✗    │
    ↓           ↓    │
Execute      Wait 2s─┘
Translation
    ↓
Poll Execution Status ←──┐
    ↓                     │
Check Execution Complete  │
    ↓              ↓      │
    ✓              ✗      │
    ↓              ↓      │
Download       Wait 5s────┘
Result
    ↓
Save Result File
    ↓
Format Response (最后节点)
```

### 响应机制

#### Form Trigger 的 responseMode

**lastNode 模式**:
- 表单提交后，n8n 会等待整个工作流执行完成
- 使用最后一个节点（Format Response）的输出作为响应
- 用户会看到翻译完成的结果

**特点**:
- ✅ 用户体验好（一次性完成所有步骤）
- ✅ 无需手动轮询状态
- ⚠️ 等待时间较长（取决于翻译任务）

#### 响应格式

```json
{
  "success": true,
  "message": "✅ 翻译完成！",
  "session_id": "xxx-xxx-xxx",
  "file_name": "example_translated.xlsx",
  "download_url": "http://localhost:8013/api/download/xxx-xxx-xxx",
  "tips": "文件已保存，可以通过 download_url 下载"
}
```

### 部署步骤

#### 1. 通过 API 更新（已完成）

```bash
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/scripts
python3 << 'EOF'
import requests
import json
from config import get_api_headers

headers = get_api_headers()
workflow_id = "1xQAR3UTNGrk0X6B"

# 停用
requests.post(f'http://localhost:5678/api/v1/workflows/{workflow_id}/deactivate', headers=headers)

# 更新
with open('../workflows/08_web_form_translation.json', 'r') as f:
    workflow = json.load(f)

update_data = {
    'name': workflow['name'],
    'nodes': workflow['nodes'],
    'connections': workflow['connections'],
    'settings': workflow['settings']
}

requests.put(f'http://localhost:5678/api/v1/workflows/{workflow_id}', headers=headers, json=update_data)

# 激活
requests.post(f'http://localhost:5678/api/v1/workflows/{workflow_id}/activate', headers=headers)
EOF
```

✅ **状态**: 已通过 API 更新并激活

#### 2. 在 UI 中保存（必须）⚠️

**重要**: 虽然通过 API 已更新工作流，但 **必须在 n8n UI 中手动保存一次**才能注册 webhook 路由！

**操作步骤**:
1. 访问: `http://localhost:5678/workflow/1xQAR3UTNGrk0X6B`
2. 检查工作流结构是否正确
3. 点击右上角 **"Save"** 按钮（💾 图标）
4. 等待 "Saved" 提示
5. Webhook 会自动注册

**为什么必须手动保存？**

根据我们的经验（详见 `.claude/CLAUDE.md`）：
- n8n 的 webhook 注册是两步过程
- API 只能生成 `webhookId`（UUID）
- 注册路由到内存路由表**只能通过 UI 保存触发**
- 这是 n8n 的架构限制，无法通过纯 API 绕过

#### 3. 验证 Webhook

保存后，运行验证脚本：

```bash
cd scripts
python3 << 'EOF'
import requests
from config import get_api_headers

headers = get_api_headers()
response = requests.get('http://localhost:5678/api/v1/workflows/1xQAR3UTNGrk0X6B', headers=headers)
workflow = response.json()['data']

# 查找 Form Trigger 节点
form_nodes = [n for n in workflow['nodes'] if n['type'] == 'n8n-nodes-base.formTrigger']
if form_nodes:
    webhook_id = form_nodes[0].get('webhookId', '')
    path = form_nodes[0]['parameters'].get('path', '')

    if webhook_id:
        form_url = f"http://localhost:5678/form/{webhook_id}"
        print(f"✅ Webhook 已生成")
        print(f"📍 Form URL: {form_url}")

        # 测试访问
        test = requests.get(form_url)
        if "Problem loading form" in test.text:
            print("❌ Webhook 未注册 - 请在 UI 中保存工作流")
        else:
            print("✅ 表单可访问")
    else:
        print("❌ Webhook ID 为空 - 请在 UI 中保存工作流")
EOF
```

### 测试验证

#### 1. 表单访问测试

在 UI 中保存后，webhook URL 应该类似：
```
http://localhost:5678/form/<webhook-id>
```

访问后应该看到：
- 📄 标题：Excel 文件翻译系统
- 📤 文件上传框
- 🌍 目标语言多选框（EN/TH/PT/VN）
- 📚 术语表下拉菜单
- 🔧 翻译引擎下拉菜单

#### 2. 完整流程测试

1. 上传测试 Excel 文件
2. 选择目标语言（例如：EN）
3. 选择术语表（可选）
4. 选择翻译引擎（默认：通义千问）
5. 提交表单

**预期结果**:
- 等待几分钟（取决于文件大小）
- 返回 JSON 响应，包含：
  - `success: true`
  - `session_id`
  - `file_name`
  - `download_url`

#### 3. 下载结果

使用返回的 `download_url`:
```bash
curl "http://localhost:8013/api/download/<session_id>" -o result.xlsx
```

### 与简化版的对比

| 特性 | 简化版 (trans) | 完整版 (translation) |
|------|---------------|-------------------|
| **节点数** | 2 | 13 |
| **响应模式** | onReceived | lastNode |
| **自动轮询** | ❌ | ✅ |
| **自动下载** | ❌ | ✅ |
| **等待时间** | <1秒 | 几分钟 |
| **用户体验** | 需手动查询 | 一次性完成 |
| **适合场景** | API 集成 | 终端用户 |
| **Form URL** | `/form/trans` | `/form/<webhook-id>` |

### 注意事项

1. **⚠️ 必须在 UI 中保存**
   - 通过 API 更新后，必须在 UI 中打开并保存一次
   - 这是注册 webhook 路由的唯一方式

2. **⚠️ 工作流执行时间**
   - 完整版会等待翻译完成（几分钟）
   - 确保 n8n 的超时设置足够长
   - 建议在表单中提示用户等待时间

3. **⚠️ 错误处理**
   - 当前版本移除了 Return Error 节点
   - 如果工作流失败，用户会收到 n8n 的默认错误响应
   - 未来可以考虑添加 Error Trigger 节点处理错误

4. **⚠️ Wait 节点的 webhookId**
   - Wait 节点需要 webhookId 来恢复执行
   - 当前设置为空字符串，n8n 会自动生成
   - 在 UI 中保存时会自动填充

### 相关文档

- [Webhook 修复文档](../WEBHOOK_FIXED.md)
- [Claude 开发指南](../.claude/CLAUDE.md)
- [工作流版本对比](./README_WORKFLOWS.md)
- [n8n GitHub Issue #12371](https://github.com/n8n-io/n8n/issues/12371)

## 2025-01-17 19:30: 修复 Binary Data 处理错误

### 问题

工作流更新后，表单提交时出现错误：
```
NodeApiError: source.on is not a function
at ExecuteContext.execute (...HttpRequestV3.node.ts:847:16)
```

错误节点：Upload & Split Tasks (HTTP Request)

### 根本原因

HTTP Request 节点中 multipart/form-data 的文件参数引用不正确：
- 使用了 `Object.values($binary)[0]`，这种方式在某些情况下可能不稳定
- n8n 期望明确的字段名引用

### 解决方案

将 HTTP Request 节点的文件参数从：
```json
{
  "name": "file",
  "value": "={{ Object.values($binary)[0] }}"
}
```

改为：
```json
{
  "name": "file",
  "value": "={{ $binary['Excel 文件'] }}"
}
```

### 验证

运行验证脚本：
```bash
cd /mnt/d/work/trans_excel/translation_system_v2/integrations/n8n/scripts
python3 verify_form.py
```

输出：
- ✅ Binary pass-through: Correct
- ✅ Binary reference: Correct (specific field name)
- ⚠️ No webhook ID - workflow needs to be saved in UI

### 下一步

**必需操作**：
1. 在 n8n UI 中打开工作流：`http://localhost:5678/workflow/1xQAR3UTNGrk0X6B`
2. 点击 Save 按钮（💾）
3. 运行 `python3 verify_form.py` 确认 webhook 已注册
4. 测试表单提交流程

**测试步骤**：
1. 访问表单 URL（在保存后从 verify_form.py 输出获取）
2. 上传测试 Excel 文件
3. 选择目标语言
4. 提交并等待结果

---

**更新时间**: 2025-01-17 19:30
**更新人**: Claude Code
**状态**: ✅ 配置已修复，⚠️ 待 UI 保存和测试
